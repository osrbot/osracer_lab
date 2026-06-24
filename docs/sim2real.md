# Sim2Real / Jetson

OSRacer 的 sim2real 分成三步：导出策略、离线验证、Jetson 低速实车测试。

## 角色分工

| 机器 | 做什么 | 不做什么 |
|---|---|---|
| RTX 4080 SUPER 服务器 | Isaac Lab 训练、策略导出、批量仿真 | 不直接控制实车 |
| Jetson Orin Nano Super 8G | ROS、传感器、推理、实车闭环 | 不跑大规模训练 |
| ESP32 / osrcore | 电机、转向、IMU、编码器、串口协议 | 不跑策略 |

## 1. 打包部署产物

```bash
cd ~/osracer_ws/osracer_lab
python3 scripts/package_jetson_deployment.py \
  --policy /tmp/policy.pt \
  --output-dir /tmp/osracer_deploy_pkg
```

有实测 overlay 时：

```bash
python3 scripts/package_jetson_deployment.py \
  --policy /tmp/policy.pt \
  --measured-overlay /tmp/osracer_measured_overlay.json \
  --output-dir /tmp/osracer_deploy_pkg
```

## 2. Jetson 预检查

在 Jetson 上运行 `osracer feat-demo` 的工具：

```bash
tools/jetson_preflight.sh
tools/jetson_environment_report.py --output /tmp/osracer_jetson_environment.json
tools/real_car_readiness_check.sh
```

## 3. 采集实车测量包

```bash
tools/jetson_measurement_session.sh \
  --camera-topic /rgb/image_raw \
  --lidar-topic /scan \
  --imu-topic /imu_filter \
  --odom-topic /odometry/filtered \
  --output-dir /tmp/osracer_measurement_session
```

回到训练机后导入：

```bash
cd ~/osracer_ws/osracer_lab
MEASUREMENTS_FILE=/tmp/osracer_measurements_seed.json \
MEASUREMENT_SESSION_FILE=/tmp/osracer_measurement_session/measurement_session.json \
scripts/validate_osracer_lab.sh import-measurement-session
```

## 4. 离线 replay

```bash
python3 scripts/run_sim2real_replay_pipeline.py \
  --policy /tmp/policy.pt \
  --observations-csv /tmp/policy_replay.csv \
  --output-dir /tmp/osracer_replay_report
```

## 5. 首次实车闭环前检查

必须确认：

- `runtime-contract` 通过
- 相机内参已导入，视觉任务不能用广告 FOV 代替标定
- 外参冲突已解决
- 串口延迟已测量
- Jetson performance profile 已记录
- TensorRT / TorchScript 推理延迟满足要求
- 首次限速仍保持 `0.3 m/s` 或更低

## 失败时优先排查

| 现象 | 优先检查 |
|---|---|
| 没有 `/odometry/filtered` | `stream sync`、`s` 帧、串口设备 |
| 启动日志无 ProjectVer | 固件是否支持 `fw version` |
| 视觉策略效果差 | 相机标定、外参、运行分辨率 |
| Jetson 卡顿 | 推理延迟、CPU governor、TensorRT engine |
