# 传感器与 Observation 合同

这一页定义 `osracer_lab` 里仿真 observation、真实 ROS topic 和部署策略之间的最低一致性要求。它的目标是防止把只在 Isaac Sim 中存在的真值误导出为实车策略。

## 分层原则

| 层 | 允许使用 | 禁止用于实车部署策略 |
|---|---|---|
| 仿真 teacher / 奖励 | 世界坐标、赛道真值、完整状态、接触状态 | 不限制，但必须标记为 sim-only |
| 部署 student policy | 相机、LiDAR、IMU、底盘速度、舵角/电机状态、历史 action | `root_pos_w`、仿真欧拉角真值、理想轮胎侧偏、接触真值 |
| safety supervisor | LiDAR 最近距离、局部 free-space、速度和舵角限幅 | 不能依赖 policy 正确输出 |

## 当前任务合同

| Task | 当前用途 | 部署状态 |
|---|---|---|
| `Isaac-OSRacerDriftRL-v0` | drift / 控制研究基线 | sim-only，不允许默认作为实车部署导出 |
| `Isaac-OSRacerVisualRL-v0` | 相机 + IMU/底盘历史的部署候选基线 | 可以作为部署候选，但仍需真实 replay 和 safety gate |

检查命令：

```bash
scripts/validate_osracer_lab.sh policy-observation-contract
scripts/validate_osracer_lab.sh policy-observation-contract --task Isaac-OSRacerVisualRL-v0
```

第一条会故意把 drift baseline 报为 blocked，因为它仍包含仿真真值。第二条用于检查当前部署候选 observation。

## 必须对齐的真实 ROS 数据

| 数据 | 最低要求 | 当前用途 |
|---|---|---|
| Camera | topic、`frame_id`、分辨率、fps、`CameraInfo`、曝光模式、时间戳来源 | 视觉特征 / student 输入 |
| LiDAR | topic、`frame_id`、角分辨率、频率、scan direction、时间戳来源 | free-space、occupancy、safety supervisor |
| IMU | topic、频率、量程、坐标系、是否包含滤波姿态 | 角速度、加速度、稳定性判断 |
| Chassis | 速度、舵角目标/反馈、电机目标/反馈、编码器状态 | policy 低维输入和 replay |
| Command | `/ackermann_cmd` 单位、限幅、watchdog、串口延迟 | policy 输出合同 |

## 导出规则

默认导出脚本会阻止 sim-only drift task：

```bash
~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/export_osracer_policy.py \
  --headless \
  --task Isaac-OSRacerVisualRL-v0 \
  --checkpoint logs/rsl_rl/osracer_visual/<run>/model_1999.pt
```

如果只是导出仿真研究 artifact，必须显式声明：

```bash
~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/export_osracer_policy.py \
  --headless \
  --checkpoint logs/rsl_rl/osracer_drift/<run>/model_1999.pt \
  --allow-sim-only-observations
```

这个导出不能直接用于实车闭环。

## 进入实车前的硬门槛

- `policy-observation-contract --task Isaac-OSRacerVisualRL-v0` 通过。
- `runtime-contract` 能在本地 `osracer feat-demo` 路径上运行。
- `CameraInfo`、LiDAR/Camera/IMU 外参、串口延迟、底盘响应延迟已记录。
- 真实 rosbag replay 能生成同 shape、同单位、同顺序的 policy 输入。
- LiDAR safety supervisor 已开启。
