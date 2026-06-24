# OSRacer 实车参数填写表

这份表把当前已经填入的参数和仍需你补充的参数放在一起。后续 calibrated sim2sim / sim2real 以这里和 `docs/real_car_measurements.json` 为依据。

## 来源

| 项 | 来源 |
|---|---|
| 固件 | `osrbot/osrcore` `main` |
| ROS 上位机 | `osrbot/osracer` `feat-demo` |
| Isaac Lab | `https://github.com/osrbot/osracer_lab` |
| 参数模板 | `docs/real_car_measurements.template.json` |

## 已填参数

### 底盘与仿真

| 参数 | 当前值 | 备注 |
|---|---:|---|
| 轴距 | `0.285 m` | 与 ROS bridge 对齐 |
| 后轮距 | `0.235 m` | 当前 Isaac / URDF 模型 |
| Isaac Lab 轮半径 | `0.050 m` | 当前仿真值 |
| 固件编码器轮半径 | `0.0425 m` | 来自 `osrcore` |
| 仿真最大速度 | `3.0 m/s` | 训练动作范围 |
| 仿真最大转向 | `0.488 rad` | 约 `27.96 deg` |
| ROS 转向限幅 | `30 deg` | bridge 限幅 |
| 初始实车限速 | `0.3 m/s` | 首车保守值 |

### 运行接口

| 参数 | 当前值 |
|---|---|
| ROS | `ROS 2 Humble` |
| Jetson 系统 | `JetPack 6.x / Ubuntu 22.04` |
| 串口设备 | `/dev/osrbot_base` |
| 串口波特率 | `460800` |
| 控制命令 | `v <speed_mps> <steering_deg>` |
| 默认遥测 | `stream sync` |
| Ackermann topic | `/ackermann_cmd` |
| Twist topic | `/cmd_vel` |
| Odom topic | `/odometry/filtered` |
| IMU topic | `/imu_filter` |
| 指令看门狗 | `0.5 s` |

### 固件控制

| 参数 | 当前值 |
|---|---:|
| 编码器 PPR | `1024` |
| 编码器减速比 | `10.55` |
| 速度计算周期 | `20 ms` |
| 速度 PID | `425.0 / 8.4 / 20.6` |
| 油门 PWM | `1000 / 1500 / 2000 us` |
| 转向 PWM | `1000 / 1500 / 2000 us` |
| 固件最大转向 | `30 deg` |
| 串口指令超时 | `500 ms` |

### 相机

| 参数 | 当前值 |
|---|---|
| 型号 | `DCXG200` |
| 传感器 | `AR0234` |
| 快门 | Global shutter |
| 镜头 | `2.7 mm` |
| 标称视场角 | `130 deg` |
| 最高分辨率 | `1920 x 1200` |
| 当前 ROS 配置 | `640 x 480 @ 120 fps` |
| 接口 | USB2.0 UVC |
| 输出格式 | MJPG / YUY2 |

### 激光雷达

| 参数 | 当前值 |
|---|---|
| 水平视场角 | `270 deg` |
| 距离 | `25 m` 级别 |
| 测量精度 | `+/-2 cm` |
| 角分辨率 | `0.1 / 0.25 deg` 可选 |
| 频率 | `10 / 20 / 25 / 30 Hz` 可选 |
| 输出 | 距离、角度、强度、时间戳 |
| 传输 | UDP/IP 和 USB |

### 需要解决的外参

| 变换 | 当前问题 |
|---|---|
| `base_link -> camera_link` | URDF 和 static TF 不一致 |
| `base_link -> laser` | URDF 和 static TF 不一致 |
| `base_link -> imu_link` | URDF 和 static TF 不一致 |

## 需要你补充的参数

### 整车质量 / 几何

| 参数 | 需要填写 |
|---|---|
| 整车质量 | 带电池、Jetson、相机、雷达、线束 |
| 前轮距 | 实测值 |
| 带负载轮半径 | 用于解决 `0.050 m` 与 `0.0425 m` 冲突 |
| 轮胎宽度 | 实测值 |
| 重心或前后重量分布 | 粗略值也可，但要标注方法 |

### 转向

| 参数 | 需要填写 |
|---|---|
| 左最大转向角 | 度或弧度 |
| 右最大转向角 | 度或弧度 |
| 舵机零点 | PWM 或角度 |
| 转向死区 | 度或 PWM |
| 转向响应时间 | 阶跃输入到稳定时间 |

### 电机 / ESC / 电池

| 参数 | 需要填写 |
|---|---|
| 电机 KV 或额定转速 | 型号或实测 |
| 电池电压范围 | 满电、标称、低压 |
| 最大速度 | 地面实测 |
| 最小稳定速度 | 地面实测 |
| 加速延迟 | 命令到速度变化 |
| 刹车延迟 | 命令到停止趋势 |

### IMU / 编码器 / 时序

| 参数 | 需要填写 |
|---|---|
| IMU 实际发布频率 | ROS topic 实测 |
| IMU 坐标系方向 | 相对 `base_link` |
| 编码器速度误差 | 与外部测量对比 |
| 串口往返延迟 | 多次采样均值和 p95 |
| 传感器时间戳来源 | 硬件时间 / ROS 接收时间 |

### 相机标定

| 参数 | 需要填写 |
|---|---|
| `fx fy cx cy` | CameraInfo |
| 畸变模型 | CameraInfo |
| 畸变系数 | CameraInfo |
| 标定分辨率 | 必须和部署分辨率对应 |
| 标定误差 | RMS / reprojection error |

### 传感器外参

| 参数 | 需要填写 |
|---|---|
| 相机 `xyz + rpy` | 相对 `base_link` |
| 雷达 `xyz + rpy` | 相对 `base_link` |
| IMU `xyz + rpy` | 相对 `base_link` |
| 测量证据 | 照片、记录、测量方法 |

## 最小优先级

如果只能先补一批，优先补：

1. 带负载轮半径。
2. 左右最大转向角和舵机零点。
3. CameraInfo 内参和畸变。
4. 相机、雷达、IMU 外参。
5. 串口延迟和传感器时间戳来源。
6. 整车质量和前后重量分布。
