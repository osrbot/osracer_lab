# OSRacer feat-demo 参数核对

本文记录 `osracer_lab` 与 ROS 上位机 `osracer feat-demo`、固件 `osrcore` 之间已经核对的参数，以及仍需实测确认的差异。

## 当前来源

- `feat-demo`：`osrbot/osracer`，快照 `a901398`
- 固件：`osrbot/osrcore`，快照 `729a6c2`
- Isaac / 工具仓库：`osracer_lab`

## 已匹配的运行参数

| 参数 | `osracer_lab` | `feat-demo` / 固件 |
|---|---|---|
| 串口设备 | `/dev/osrbot_base` | `/dev/osrbot_base` |
| 波特率 | `460800` | `460800` |
| 控制命令 | `v <speed_mps> <steering_deg>` | `v <speed_mps> <steering_deg>` |
| 默认遥测 | `stream sync` | `stream sync` |
| Ackermann 输入 | 速度 + 转向角 | `/ackermann_cmd` |
| 转向单位 | 策略输出弧度，固件发送角度 | ROS bridge 内部转换 |
| 固件版本 | `fw version` / `ProjectVer` | ROS 启动时查询并打印 |

## 传感器覆盖情况

| 传感器 | 当前状态 |
|---|---|
| 相机 | 已记录 AR0234、2.7mm、USB UVC、`640 x 480 @ 120 fps` 运行配置；仍需 CameraInfo 标定 |
| 激光雷达 | 已记录 25m、270 度、TOF、UDP/USB；仍需确认真实运行频率和时间戳 |
| IMU | 固件侧记录 QMI8658、量程和频率；仍需确认 ROS frame 对齐 |
| 编码器 | 固件侧有 PPR、减速比、轮半径；仍需确认加载轮径和仿真几何含义 |

## 已知不一致

| 项 | 当前差异 | 处理方式 |
|---|---|---|
| 轮半径 | 固件 / `osracer_sim` 使用 `0.0425 m`，Isaac Lab 当前使用 `0.050 m` | 实测带负载轮半径后决定编码器和碰撞几何是否分开 |
| 传感器外参 | URDF 与 static TF 不一致 | 按 [外参对齐](extrinsics_alignment.md) 统一 |
| 相机视场角 | 标称 `130 deg` 与 `2.7 mm` 针孔估算不直接一致 | 使用 CameraInfo 标定结果作为视觉 sim2real 依据 |

## 仍需补充

进入标定闭环 sim2real 前，还需要：

1. 整车质量和重量分布。
2. 前轮距、轮胎宽度、加载轮径。
3. 左右最大转向角、舵机零点、响应时间和死区。
4. 电机/ESC 参数、最大速度、最小稳定速度、加减速延迟。
5. 相机内参和畸变。
6. 相机、雷达、IMU 相对 `base_link` 的外参。
7. 串口延迟、传感器时间戳来源和同步方式。

## 验证命令

```bash
scripts/validate_osracer_lab.sh runtime-contract
python3 scripts/verify_source_authority_snapshot.py \
  docs/source_authority_snapshot.json \
  --osracer-root /home/osrbot/Desktop/osracer/osracer
```
