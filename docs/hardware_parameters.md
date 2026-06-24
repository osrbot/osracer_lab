# OSRacer 硬件参数

本文是 `osracer_lab` 当前用于 sim2sim、sim2real 和 Jetson 部署的实车参数入口。
缺失的实测值请按 [实车测量清单](real_car_measurement_checklist.md) 采集；相机、雷达、IMU 外参冲突请按 [外参对齐](extrinsics_alignment.md) 处理。

## 参数来源

- 固件权威来源：`https://github.com/osrbot/osrcore`，分支 `main`。
- ROS 上位机权威来源：`https://github.com/osrbot/osracer/tree/feat-demo`。
- 不要从 `osracer dev` 或其他分支推导车辆协议和运行参数。
- 当前固件串口接口：`v <vx_m/s> <steer_deg>`、`stream sync|legacy|off`、`s/m/r/b` 遥测。
- ROS 侧串口设备和波特率：`/dev/osrbot_base`，`460800`。

## 底盘参数

| 参数 | 当前值 |
|---|---:|
| 轴距 | `0.285 m` |
| 后轮距 | `0.235 m` |
| 仿真轮半径 | `0.050 m` |
| 仿真最大速度 | `3.0 m/s` |
| 仿真最大转向 | `0.488 rad` |
| 初始实车限速 | `0.3 m/s` |

`0.488 rad` 是当前仿真动作范围。ROS bridge 的转向限幅是 `30 deg`，实车部署策略时应保持在 `0.488 rad` 或更低，直到真实舵机范围完成测量。

## 相机

用户提供的 AR0234 相机参数：

| 参数 | 当前值 |
|---|---|
| 型号 | `DCXG200` |
| 传感器 | `AR0234` |
| 快门 | Global shutter |
| 镜头 | `2.7 mm`，标称低畸变 / 无畸变 |
| 标称视场角 | `130 deg` |
| 分辨率 | `1920 x 1200` |
| 像元尺寸 | `3 um x 3 um` |
| 帧率 | `90 / 120 fps` |
| 接口 | USB2.0 UVC |
| 输出格式 | MJPG / YUY2 |
| 功耗 | 约 `2 W` |
| 供电 | `5 V` |
| 模组尺寸 | `36 mm x 36 mm` |
| 净重 | `59.9-67.5 g` |

当前 ROS 相机启动使用 `usb_cam`，设备为 `/dev/video0`，发布 `/rgb/image_raw`，`frame_id=camera_link`，运行配置为 `640 x 480 @ 120 fps`，格式转换为 `mjpeg2rgb`。

::: warning 相机视场角需要实测
根据像元尺寸估算，AR0234 传感器尺寸约为 `5.76 mm x 3.6 mm`。`2.7 mm` 针孔模型不能直接推出 `130 deg` 水平视场角，因此 `130 deg` 只能先视为镜头标称值。视觉 sim2real 必须用棋盘格或 AprilTag 标定得到 `fx`、`fy`、`cx`、`cy` 和畸变系数。
:::

## 激光雷达

用户提供的 25m 雷达参数：

| 参数 | 当前值 |
|---|---|
| 扫描方式 | 机械旋转 |
| 测距方式 | 脉冲 TOF |
| 水平视场角 | `270 deg` |
| 探测距离 | `>=25 m @ 70%` 反射率，`>=15 m @ 10%` 反射率 |
| 测量精度 | `+/-2 cm` |
| 角分辨率 | `0.1 deg / 0.25 deg` 可选 |
| 旋转频率 | `10 / 20 / 25 / 30 Hz` |
| 采样率 | `28.8 / 36 / 43.2 kHz` 可选 |
| 输出 | 距离、角度、强度、时间戳 |
| 传输 | UDP/IP 和 USB |
| 波长 | `940 nm` |
| 安全等级 | Class 1 |
| 尺寸 | `60 mm x 60 mm x 80 mm` |
| 重量 | `160 g` |
| 功耗 | `<=2 W` |
| 供电 | `9-36 V` |
| 防护等级 | IP65 |

当前 sim2sim 先用 `lidar_25m_planar_scan_cfg()` 建模为保守的 270 度平面扫描：`0.25 deg`、`10 Hz`、`25 m`、`1081` 条射线。真实雷达配置完成并记录时间戳后，再决定是否切到 `0.1 deg` 或更高转速。

## 实车运行接口

这些值来自 `osracer feat-demo` 上位机代码和 `osrcore` 固件协议：

| 参数 | 当前值 |
|---|---|
| ROS 运行环境 | `ROS 2 Humble` on `JetPack 6.x / Ubuntu 22.04` |
| 底盘启动文件 | `osracer_bringup chassis_ackermann.launch.py` |
| 串口设备 | `/dev/osrbot_base` |
| 串口波特率 | `460800` |
| 控制协议 | `v <speed_mps> <steering_deg>` |
| 指令看门狗 | `0.5 s` |
| 固件版本查询超时 | `0.8 s` |
| 固件版本查询 | `fw version`，ROS 启动时打印 `OSRCORE ProjectVer` |
| Ackermann topic | `/ackermann_cmd` |
| Twist topic | `/cmd_vel` |
| 里程计 topic | `/odometry/filtered` |
| IMU topic | `/imu_filter` |
| 磁力计 topic | `/magnetometer_data` |
| 遥控 topic | `/rc_data` |
| IMU 串口帧 | `i qx qy qz qw ax ay az gx gy gz` |
| Odom 串口帧 | `o px py pz vx vy vz yaw` |

bridge 接收 `AckermannDrive.steering_angle`，单位为弧度；内部按 `max_steering_angle_deg=30.0` 限幅后，发送给固件时转换为角度。

## 固件控制参数

从本地只读 `osrcore` `729a6c2` 读取到的补充值：

| 模块 | 参数 | 当前值 |
|---|---|---:|
| 编码器 | A/B GPIO | `3 / 9` |
| 编码器 | PPR | `1024` |
| 编码器 | 减速比 | `10.55` |
| 编码器 | 固件轮半径 | `0.0425 m` |
| 编码器 | 速度计算周期 | `20 ms` |
| 速度 PID | `kp / ki / kd` | `425.0 / 8.4 / 20.6` |
| 速度 PID | 控制周期 | `20 ms` |
| 速度 PID | 死区 | `0.05 m/s` |
| 速度限制 | 前进 / 后退 | `+6.0 / -6.0 m/s` |
| 油门 PWM | `min / neutral / max` | `1000 / 1500 / 2000 us` |
| 转向 PWM | `min / center / max` | `1000 / 1500 / 2000 us` |
| 转向 | 固件最大转向 | `30 deg` |
| 转向 | 默认 trim / 范围 | `0 deg`, `-5..5 deg` |
| SBUS | 波特率 / 格式 | `100000`, `8E2 inverted Futaba SBUS` |
| SBUS | 通道范围 | `240..1810` |
| SBUS | CH0 / CH2 / CH6 / CH7 | 转向 / 油门 / 控制模式 / 速度模式 |
| SBUS | 低速模式 | `15%` 比例 |
| IMU | 型号 / 地址 | `QMI8658`, `0x6B` |
| IMU | 加速度 / 陀螺仪量程 | `+-4 g`, `+-1024 dps` |
| IMU | ODR / 平均采样 | `1000 Hz`, `5 samples` |
| IMU 加热 | 目标 / 预热 / 稳定 | `56 C / 38 C / 54 C` |
| 电池 | 低压 / 恢复 | `10.8 V / 11.1 V` |
| 遥测 | sync / IMU / odom / mag / RC / battery | `5 / 5 / 20 / 50 / 100 / 2000 ms` |
| 安全 | 串口指令超时 | `500 ms` |

不要直接把 Isaac Lab 的 `wheel_radius_m=0.050` 改成固件编码器半径 `0.0425 m`。这两个值当前代表的含义还没统一，必须先测量带负载轮胎半径，并决定它用于编码器里程计、碰撞几何，还是两者都用。

## 传感器外参

当前存在 URDF 和 static TF 不一致，必须在标定 sim2real 前解决：

| 变换 | URDF `xyz rpy` | Static TF `xyz rpy` |
|---|---|---|
| `base_link -> camera_link` | `0.12323 -0.017229 -0.053395 -1.5708 0 -1.5708` | `0.30 0 0.075 0 0 0` |
| `base_link -> laser` | `-0.082558 -0.017229 0.034095 0 0 0` | `0.10 0 0.13 0 0 0` |
| `base_link -> imu_link` | `0.0417958953212156 -0.0177578126845364 -0.063598843109235 0 0 0` | `0.22 0 0.03 0 0 0` |

实测安装位置或统一生成的 robot description 必须成为唯一来源，不能同时按 URDF 和 static TF 做相机、雷达、IMU 的 sim2real 标定。

## 仍需补充

| 类别 | 需要补充的实测值 |
|---|---|
| 整车质量 | 带电池、Jetson、相机、雷达和线束的总质量 |
| 几何 | 前轮距、轮胎宽度、确认后的轮半径、传感器安装位置 |
| 重量分布 | 前后轴重量分布或主要部件位置 |
| 转向 | 左右最大转角、舵机单位、零点、响应时间、死区 |
| 电机 / ESC | 电机 KV 或额定转速、电池电压、最大速度、最小稳定速度、油门死区、加减速延迟 |
| 编码器 / 里程计 | 编码器每圈 tick、安装位置、odom 是否纯固件或上位机融合 |
| IMU | 型号、频率、量程、磁力计、坐标系对齐 |
| 外参 | 相机、雷达、IMU 相对 `base_link` 的 `xyz + rpy` |
| 时序 | 串口延迟、传感器时间戳来源、时钟同步方式 |
| TF | 统一 camera、lidar、IMU 的 URDF 与 static TF |

## 在流程中的使用

- Isaac Lab：训练仍在 RTX 4080 SUPER 上高并发运行，参数文件作为任务更新参考。
- MuJoCo：第二仿真器必须使用同一套动作接口和硬件参数。
- Jetson：只部署 TorchScript / ONNX / TensorRT 策略，不在 Jetson 上训练。
- 实车：先做被动日志和离线 replay，再打开 `/ackermann_cmd` 闭环。

参数一致性检查：

```bash
python3 scripts/check_runtime_contract.py --osracer-root /home/osrbot/Desktop/osracer/osracer
scripts/validate_osracer_lab.sh sim-sensor-contract
```

完成传感器外参统一后，再开启 strict 检查：

```bash
python3 scripts/check_runtime_contract.py \
  --osracer-root /home/osrbot/Desktop/osracer/osracer \
  --strict-extrinsics
```
