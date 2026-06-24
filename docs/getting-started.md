# 快速开始

这一页的目标是让新手确认仓库能跑，而不是马上训练一个可上车的策略。

## 你需要准备什么

| 项 | 建议 |
|---|---|
| 训练机器 | Ubuntu + NVIDIA GPU，当前开发机为 RTX 4080 SUPER |
| 推理机器 | Jetson Orin Nano Super 8G，JetPack 6.x / Ubuntu 22.04 |
| Isaac Sim | 建议 Isaac Sim 5.1 |
| Isaac Lab | 与 Isaac Sim 5.1 匹配的 Latest / main 安装 |
| ROS 实车仓库 | `osrbot/osracer` 的 `feat-demo` 分支 |
| 固件仓库 | `osrbot/osrcore` 的 `main` 分支 |

!!! note
    训练在服务器上做，Jetson 负责部署推理和实车传感器。不要在 Jetson Orin Nano Super 8G 上跑大规模 Isaac Lab 训练。

## 1. 克隆仓库

```bash
mkdir -p ~/osracer_ws
cd ~/osracer_ws
git clone https://github.com/osrbot/osracer_lab.git
cd osracer_lab
```

## 2. 进入 Isaac Lab 环境

下面假设你的 Isaac Lab 在 `~/rlgpu_ws/IsaacLab`：

```bash
cd ~/rlgpu_ws/IsaacLab
./isaaclab.sh -p scripts/environments/list_envs.py
```

如果这一步不能列出 Isaac Lab 环境，请先看 [安装环境](installation.md)。

## 3. 安装 OSRacer 扩展

```bash
cd ~/rlgpu_ws/IsaacLab
./isaaclab.sh -p -m pip install -e ~/osracer_ws/osracer_lab/source/osracer_lab_assets
./isaaclab.sh -p -m pip install -e ~/osracer_ws/osracer_lab/source/osracer_lab_tasks
./isaaclab.sh -p -m pip install -e ~/osracer_ws/osracer_lab/source/osracer_lab_rl
```

## 4. 确认任务注册

```bash
cd ~/rlgpu_ws/IsaacLab
./isaaclab.sh -p scripts/environments/list_envs.py | grep OSRacer
```

应该能看到：

```text
Isaac-OSRacerDriftRL-v0
Isaac-OSRacerVisualRL-v0
```

## 5. 跑最小静态检查

```bash
cd ~/osracer_ws/osracer_lab
scripts/validate_osracer_lab.sh static
scripts/validate_osracer_lab.sh source-authority-snapshot
scripts/validate_osracer_lab.sh runtime-contract
```

这三步用于确认：

- Python 文件和包结构基本正确
- `osrcore` / `osracer feat-demo` 的协议合同还一致
- ROS 实车合同与 lab 参数还一致

## 6. 跑 drift smoke

```bash
cd ~/osracer_ws/osracer_lab
~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/train_osracer_drift.py \
  --headless --num_envs 64 --max_iterations 2
```

这不是正式训练，只是确认 Isaac Lab 能创建 OSRacer 环境。

## 7. 下一步

| 你想做什么 | 下一页 |
|---|---|
| 安装 Isaac Sim / Isaac Lab | [安装环境](installation.md) |
| 正式训练和导出策略 | [训练与导出](training.md) |
| 准备实车参数 | [实车参数](real-car.md) |
| Jetson 部署 | [Sim2Real / Jetson](sim2real.md) |
