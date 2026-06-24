# OSRacer Isaac / Jetson 移交与推送准备

本文用于继续推进 OSRacer Isaac、Jetson Orin Nano Super 8G 运行时、sim2sim 和 sim2real 准备工作。

## 仓库映射

| 模块 | 仓库 | 分支 | 说明 |
|---|---|---|---|
| Isaac / 仿真 / 部署工具 | `https://github.com/osrbot/osracer_lab` | `main` | 当前公开仓库 |
| ROS 上位机 | `https://github.com/osrbot/osracer/tree/feat-demo` | `feat-demo` | Jetson、传感器、推理和首车工具 |
| 固件 | `https://github.com/osrbot/osrcore` | `main` | 固件协议和底层控制参数权威来源 |

## 当前状态

- `osracer_lab` 已公开。
- 文档站已迁移到 VitePress，并支持中英文切换。
- `osracer_lab` 包含 Isaac Lab、测量、部署、MuJoCo sim2sim 和来源校验工具。
- `osracer feat-demo` 包含 Jetson 推理、measurement session、首车 gate 和 evidence pack。
- 标定闭环 sim2real 仍被实车测量值和外参统一阻塞。

## 推荐执行顺序

1. 在 `osracer_lab` 中确认来源和运行接口：

   ```bash
   cd /home/osrbot/Desktop/osracer/osracer_lab
   scripts/validate_osracer_lab.sh source-authority-snapshot
   scripts/validate_osracer_lab.sh runtime-contract
   ```

2. 在实车 Jetson 上采集 measurement session。

3. 把测量结果导入 `docs/real_car_measurements.json`。

4. 生成 measured overlay 和 calibration review pack。

5. replay 真实 observation，通过后再准备低速闭环。

6. 首车前运行 `osracer feat-demo` 的 first-drive gate。

## 推送准备检查

每次推送前至少检查：

```bash
git status --short --branch
git diff --check
npm run docs:build
rg -n "password|token|secret|BEGIN .*PRIVATE|ghp_|github_pat_" .
```

只允许按明确目标推送：

- `osracer_lab` 从当前仓库推 `main`。
- `osracer feat-demo` 只能从 Mac 本机对应工作树推送，不从服务器 mirror 推送。
- `osrcore` 作为固件权威来源读取，不在本流程中改动。

## 仍未验证

- 实车质量、轮径、转向范围、舵机响应、电机/ESC 参数。
- 相机 CameraInfo 内参和畸变。
- 相机、雷达、IMU 外参统一。
- 串口延迟和传感器时间戳同步。
- Jetson 上 Torch / ONNX / TensorRT 的真实性能。
- 架空闭环和落地低速首车测试。
