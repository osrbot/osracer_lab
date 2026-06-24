# 常见问题

## 看不到 OSRacer task

检查是否安装了三个扩展包：

```bash
cd ~/rlgpu_ws/IsaacLab
./isaaclab.sh -p -m pip install -e ~/osracer_ws/osracer_lab/source/osracer_lab_assets
./isaaclab.sh -p -m pip install -e ~/osracer_ws/osracer_lab/source/osracer_lab_tasks
./isaaclab.sh -p -m pip install -e ~/osracer_ws/osracer_lab/source/osracer_lab_rl
```

再查：

```bash
./isaaclab.sh -p scripts/environments/list_envs.py | grep OSRacer
```

## Visual task 启动崩溃

先跑：

```bash
nvidia-smi
find /usr/share/vulkan /etc/vulkan -name '*nvidia*icd*.json*' -o -name '*nvidia*.json*'
```

再跑 headless camera 最小检查：

```bash
cd ~/rlgpu_ws/IsaacLab
./isaaclab.sh -p -c 'from isaaclab.app import AppLauncher; app=AppLauncher(headless=True, enable_cameras=True).app; print("APP_HEADLESS_CAMERA_OK"); app.close()'
```

## ROS 没有 odom / IMU

优先检查：

- `/dev/osrbot_base` 是否存在
- 串口权限是否正确
- `osracer feat-demo` 是否最新
- 启动日志里是否有 `OSRCORE ProjectVer`
- 固件是否支持 `fw version`
- 启动后是否恢复 `stream sync`

同步帧应为：

```text
s px py pz vx vy vz yaw qx qy qz qw ax ay az gx gy gz
```

## 固件版本日志缺失

新固件支持：

```text
fw version
```

并返回包含 `ProjectVer` 的行。如果日志没有 `OSRCORE ProjectVer`，可能是：

- 固件不是最新
- 串口被其他进程占用
- `firmware_version_timeout_s` 太短

## sim2real-readiness 失败

这是预期状态，直到实车测量完成。

常见失败项：

| 失败项 | 含义 |
|---|---|
| `required_real_measurements` | 参数填写不完整 |
| `strict_extrinsics` | URDF/static TF 外参仍冲突 |
| `measured_sensor_extrinsics_applied` | 还没应用实测外参 |
| `camera calibration overlay` | 视觉部署缺少 CameraInfo 标定 |
