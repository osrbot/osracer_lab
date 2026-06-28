# OSRacer 策略部署接口约定

本文档说明训练、导出、离线 replay 和实车 bringup 之间的接口约定。
当前仓库负责训练与仿真验证，并提供 checkpoint 导出脚本。
ROS 2 上位机工作区 `/home/osrbot/Desktop/osracer/osracer` 负责运行时推理节点和 CSV replay 工具。

## 当前已验证产物

- Drift baseline: `logs/rsl_rl/osracer_drift/2026-06-23_17-05-26/model_1999.pt`
  - Command: `scripts/train_osracer_drift.py --headless --num_envs 2048 --max_iterations 2000`
  - Result: completed successfully on the RTX 4080 SUPER host.
  - Scope: sim-only research baseline; not a default real-car deployment policy.
- Visual stability check: `logs/rsl_rl/osracer_visual/2026-06-23_17-54-56/model_49.pt`
  - Command: `scripts/train_osracer_drift.py --task Isaac-OSRacerVisualRL-v0 --headless --num_envs 256 --max_iterations 50`
  - Result: completed successfully after finite-observation and non-finite-state guards.
- Visual throughput probe: `logs/rsl_rl/osracer_visual/2026-06-23_18-08-58/model_9.pt`
  - Command: `scripts/train_osracer_drift.py --task Isaac-OSRacerVisualRL-v0 --headless --num_envs 512 --max_iterations 10`
  - Result: completed successfully; this is a throughput probe, not a trained policy.

## 动作接口

Isaac Lab 策略输出是二维动作：

```text
[target_speed_mps, target_steering_rad]
```

当前仿真限制定义在 `source/osracer_lab_tasks/osracer_lab_tasks/common/actions.py`：

```text
max speed:    3.0 m/s
max steering: 0.488 rad
wheelbase:    0.285 m
rear track:   0.235 m
wheel radius: 0.050 m
```

实车 ROS 2 bridge 在 `/home/osrbot/Desktop/osracer/osracer` 中，当前接受两种输入：

- `ackermann_msgs/msg/AckermannDrive` on `ackermann_cmd`
- `geometry_msgs/msg/Twist` on `cmd_vel`

学习策略的推荐部署路径是直接发布 `AckermannDrive`：

```text
policy action[0] -> AckermannDrive.speed
policy action[1] -> AckermannDrive.steering_angle
```

底盘 bridge 会把 `AckermannDrive` 转成固件串口命令：

```text
v <speed_mps> <steering_deg>
```

`osracer_bringup/launch/chassis_ackermann.launch.py` 的默认参数是：

```text
port_name: /dev/osrbot_base
baud_rate: 460800
wheelbase: 0.285
max_steering_angle_deg: 30.0
cmd_watchdog_timeout_s: 0.5
```

注意：仿真转向限制 `0.488 rad` 约等于 `27.96 deg`，略低于 bridge 中 `30 deg` 的限幅。

## 推荐 ROS 2 接入方式

Export a deployment-candidate checkpoint before integrating with ROS 2:

```bash
~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/export_osracer_policy.py \
  --headless \
  --task Isaac-OSRacerVisualRL-v0 \
  --checkpoint logs/rsl_rl/osracer_visual/<run>/model_1999.pt
```

The default output directory is `<checkpoint_dir>/exported/` and contains:

```text
policy.pt
```

ONNX export is available when explicitly requested:

```bash
~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/export_osracer_policy.py \
  --headless --format onnx \
  --task Isaac-OSRacerVisualRL-v0 \
  --checkpoint logs/rsl_rl/osracer_visual/<run>/model_1999.pt
```

拷贝到 Jetson 前，先把导出的策略和硬件参数、manifest、checksum 打包：

```bash
python3 scripts/package_jetson_deployment.py \
  --task Isaac-OSRacerVisualRL-v0 \
  --policy logs/rsl_rl/osracer_visual/<run>/exported/policy.pt \
  --measured-overlay /tmp/osracer_measured_overlay.json \
  --output-dir /tmp/osracer_jetson_deployment
```

部署包包含：

```text
policy.pt
hardware_params.json
measured_overlay.json  # 传入 --measured-overlay 时生成
README.md
manifest.json
SHA256SUMS
```

如果部署 `Isaac-OSRacerVisualRL-v0`，`measured_overlay.json` 必须包含部署分辨率下由 CameraInfo 得到的 `camera_calibration`。

在 Jetson 上启动前先校验部署包：

```bash
cd /path/to/osracer_jetson_deployment
sha256sum -c SHA256SUMS
/path/to/osracer/tools/verify_jetson_deployment.py .
/path/to/osracer/tools/jetson_preflight.sh --policy policy.pt --offline-smoke
```

推理节点应该放在 OSRacer ROS 2 工作区中，不要把实车部署代码耦合进 Isaac Lab 训练包。

推荐推理节点职责：

1. 加载训练好的 RSL-RL checkpoint 或导出的 TorchScript / ONNX 策略。
2. 订阅训练任务需要的 observation 来源。
3. 复现仿真里的 observation 顺序、缩放、裁剪和有限值处理。
4. 用有上限的频率运行推理。
5. 发布 `AckermannDrive` 到 `ackermann_cmd`。
6. 发布前限幅速度和转向。
7. observation 过期时停止发布，或发布零速度。

Drift 策略是第一阶段实车部署目标，因为它依赖本体状态，不依赖相机 tensor。
Visual 策略还需要额外的相机预处理节点，并且要匹配 `visual/mdp_sensors/observations.py`。
实车硬件参数记录在 `docs/hardware_parameters.md` 和 `osracer_lab_assets.hardware_params` 中。

## Bringup 顺序

在实车工作区启动底盘：

```bash
ros2 launch osracer_bringup chassis_ackermann.launch.py
```

检查 bridge 输入：

```bash
ros2 topic info /ackermann_cmd
ros2 topic info /cmd_vel
ros2 topic echo /odom
ros2 topic echo /imu/data
```

手动低速指令检查：

```bash
ros2 topic pub --once /ackermann_cmd ackermann_msgs/msg/AckermannDrive \
  "{speed: 0.2, steering_angle: 0.0}"
```

停止指令：

```bash
ros2 topic pub --once /ackermann_cmd ackermann_msgs/msg/AckermannDrive \
  "{speed: 0.0, steering_angle: 0.0}"
```

## 实车运行前安全闸门

- 打开闭环前先检查当前 sim2real gate：

```bash
scripts/validate_osracer_lab.sh sim2real-readiness
```

- `scripts/validate_osracer_lab.sh sim2real-ready-strict` 是标定闭环 sim2real 的 gate。在实车参数和统一外参完成前，它应该失败。
- 用 `scripts/validate_osracer_lab.sh measured-overlay` 做离线 replay / sim 实验，确认后再把标定变更写回源码。
- 推理节点和 watchdog 行为验证前，保持 `speed <= 0.3 m/s`。
- `steering_angle` 保持在 `[-0.488, 0.488]` rad 内，和仿真动作范围一致。
- 确认 `cmd_watchdog_timeout_s=0.5` 能停止过期指令。
- observation 过期或非有限值时，策略节点必须发布零速度或停止发布。
- 落地测试前先架空车轮测试。
- 首车测试全程保留 RC / 手动接管。

## 后续缺口

ROS 2 运行路径已经在 OSRacer 上位机工作区中存在。剩余工作主要是验证和模型保真度：

1. 补齐整车质量、转向、电机、编码器、IMU、外参和时序参数。
2. 把 `docs/mujoco_sim2sim.md` 中的 MuJoCo smoke 扩展成使用同一动作和 observation 接口的标定 rollout。
3. 闭环前，用导出的 `policy.pt` replay 已记录的实车 observation。
4. 增加绑定 `/ackermann_cmd` 的低速实车 checklist。
