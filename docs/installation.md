# 安装环境

本页给出推荐安装方式。路径只是示例，复制前请按自己的机器调整。

## 推荐目录

```text
~/rlgpu_ws/IsaacSim      Isaac Sim
~/rlgpu_ws/IsaacLab      Isaac Lab
~/osracer_ws/osracer_lab 本仓库
```

## 1. 安装 NVIDIA 驱动

先确认驱动可用：

```bash
nvidia-smi
```

当前开发机上，Isaac Sim 5.1 headless camera 已用 NVIDIA driver `580.159.03` 验证。若 camera task 在 `librtx.scenedb.plugin` 附近崩溃，优先检查 Vulkan/NVIDIA driver，而不是先改训练代码。

## 2. 安装 Isaac Sim 5.1

参考 NVIDIA 官方下载页安装 Isaac Sim 5.1 预编译包。

示例：

```bash
mkdir -p ~/rlgpu_ws
cd ~/rlgpu_ws
unzip ~/Downloads/isaac-sim-standalone-5.1.0-linux-x86_64.zip -d IsaacSim
```

## 3. 安装 Isaac Lab

```bash
cd ~/rlgpu_ws
git clone https://github.com/isaac-sim/IsaacLab.git
cd IsaacLab
ln -s ../IsaacSim _isaac_sim
./isaaclab.sh -i
./isaaclab.sh --install all
```

验证：

```bash
./isaaclab.sh -p scripts/environments/list_envs.py
```

## 4. 安装本仓库扩展

```bash
mkdir -p ~/osracer_ws
cd ~/osracer_ws
git clone https://github.com/osrbot/osracer_lab.git

cd ~/rlgpu_ws/IsaacLab
./isaaclab.sh -p -m pip install -e ~/osracer_ws/osracer_lab/source/osracer_lab_assets
./isaaclab.sh -p -m pip install -e ~/osracer_ws/osracer_lab/source/osracer_lab_tasks
./isaaclab.sh -p -m pip install -e ~/osracer_ws/osracer_lab/source/osracer_lab_rl
```

## 5. Headless camera 检查

视觉任务需要 camera rendering。先跑最小检查：

```bash
cd ~/rlgpu_ws/IsaacLab
./isaaclab.sh -p -c 'from isaaclab.app import AppLauncher; app=AppLauncher(headless=True, enable_cameras=True).app; print("APP_HEADLESS_CAMERA_OK"); app.close()'
```

如果失败：

```bash
nvidia-smi
find /usr/share/vulkan /etc/vulkan -name '*nvidia*icd*.json*' -o -name '*nvidia*.json*'
```

## 6. 常见安装判断

| 现象 | 优先检查 |
|---|---|
| `ModuleNotFoundError: isaaclab` | 是否通过 `./isaaclab.sh -p` 运行 |
| 找不到 OSRacer task | 三个 `source/...` 包是否 `pip install -e` |
| Drift 可以跑，Visual 崩溃 | NVIDIA driver / Vulkan / headless camera |
| 训练很慢 | `--num_envs`、CPU 同步、是否开了不必要的相机 |
