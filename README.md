# OSRacer Isaac Lab

`osracer_lab` 是 OSRacer 阿克曼车的 Isaac Lab 训练、sim2sim、sim2real 和 Jetson 部署准备仓库。

它不替代底层固件和 ROS 上位机，而是负责训练、导出、离线验证、实车参数整理和部署包准备。

| 层 | 仓库 | 用途 |
|---|---|---|
| 固件 | [`osrbot/osrcore`](https://github.com/osrbot/osrcore) | ESP32 底盘控制、IMU、编码器、串口协议 |
| ROS 上位机 | [`osrbot/osracer`](https://github.com/osrbot/osracer/tree/feat-demo) `feat-demo` | Jetson 运行时、传感器、策略推理、实车工具 |
| Isaac Lab | [`osrbot/osracer_lab`](https://github.com/osrbot/osracer_lab) | 训练、导出、sim2sim、sim2real 检查 |

## 文档

文档站使用 VitePress：

- 在线地址：`https://osrbot.github.io/osracer_lab/`
- 中文入口：[`docs/index.md`](docs/index.md)
- 英文入口：[`docs/en/index.md`](docs/en/index.md)
- 新手入口：[`docs/getting-started.md`](docs/getting-started.md)

本地预览：

```bash
npm install
npm run docs:dev
```

## 快速开始

```bash
mkdir -p ~/osracer_ws
cd ~/osracer_ws
git clone https://github.com/osrbot/osracer_lab.git

cd ~/rlgpu_ws/IsaacLab
./isaaclab.sh -p -m pip install -e ~/osracer_ws/osracer_lab/source/osracer_lab_assets
./isaaclab.sh -p -m pip install -e ~/osracer_ws/osracer_lab/source/osracer_lab_tasks
./isaaclab.sh -p -m pip install -e ~/osracer_ws/osracer_lab/source/osracer_lab_rl

cd ~/osracer_ws/osracer_lab
scripts/validate_osracer_lab.sh static
scripts/validate_osracer_lab.sh source-authority-snapshot
scripts/validate_osracer_lab.sh runtime-contract
```

最小 smoke test：

```bash
~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/train_osracer_drift.py \
  --headless --num_envs 64 --max_iterations 2
```

## 任务

| Gym ID | 说明 |
|---|---|
| `Isaac-OSRacerDriftRL-v0` | 无视觉漂移 / 控制训练 |
| `Isaac-OSRacerVisualRL-v0` | 带相机输入的视觉策略训练 |

## 推荐训练基线

```bash
# RTX 4080 SUPER 上的 drift baseline
~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/train_osracer_drift.py \
  --headless --num_envs 2048 --max_iterations 2000

# visual baseline
~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/train_osracer_drift.py \
  --task Isaac-OSRacerVisualRL-v0 --headless --num_envs 256
```

导出部署候选 checkpoint：

```bash
~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/export_osracer_policy.py \
  --headless \
  --task Isaac-OSRacerVisualRL-v0 \
  --checkpoint logs/rsl_rl/osracer_visual/<run>/model_1999.pt
```

`Isaac-OSRacerDriftRL-v0` 仍是 sim-only 基线；如需导出仿真研究 artifact，必须额外加 `--allow-sim-only-observations`。

## 实车运行接口

| 项 | 当前值 |
|---|---|
| Jetson 运行环境 | JetPack 6.x / Ubuntu 22.04 / ROS 2 Humble |
| 串口设备 | `/dev/osrbot_base` |
| 串口波特率 | `460800` |
| 控制命令 | `v <speed_mps> <steering_deg>` |
| 默认遥测 | `stream sync`, `s/m/r/b` |
| 同步帧 | `s px py pz vx vy vz yaw qx qy qz qw ax ay az gx gy gz` |
| 固件版本 | ROS 启动时查询 `fw version` 并打印 `OSRCORE ProjectVer` |

在 [实车参数填写表](docs/real_car_parameter_fill_sheet.md) 的缺失项补齐、sim2real readiness 检查通过之前，不要把训练好的策略视为可直接上车。

## 目录

```text
source/osracer_lab_assets/      机器人 URDF、mesh、USD、ArticulationCfg
source/osracer_lab_tasks/       任务环境和 MDP 模块
source/osracer_lab_rl/          RSL-RL 启动辅助
scripts/                        训练、导出、验证、sim2real 工具
docs/                           VitePress 文档站和参考文档
```

## 验证

```bash
scripts/validate_osracer_lab.sh static
scripts/validate_osracer_lab.sh source-authority-snapshot
scripts/validate_osracer_lab.sh runtime-contract
scripts/validate_osracer_lab.sh measurement-gap
scripts/validate_osracer_lab.sh sim2real-readiness
npm run docs:build
```
