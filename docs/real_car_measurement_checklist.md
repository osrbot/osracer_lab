# OSRacer 实车测量清单

本清单用于把真实硬件参数转成可用于 sim2sim、sim2real 和 Jetson 部署的测量数据。每项测量都应保留原始记录、照片、日志和测量日期。

## 当前仓库已确认

| 项 | 当前值 | 来源 |
|---|---|---|
| 轴距 | `0.285 m` | Isaac Lab action config / `chassis_ackermann.launch.py` |
| 后轮距 | `0.235 m` | Isaac Lab 硬件参数源 |
| 仿真轮半径 | `0.050 m` | Isaac Lab action config |
| 固件编码器轮半径 | `0.0425 m` | `osrcore` |
| 仿真最大转向 | `0.488 rad` | Isaac Lab action envelope |
| ROS 转向限幅 | `30 deg` | `chassis_ackermann.launch.py` |
| 串口 | `/dev/osrbot_base @ 460800` | `chassis_ackermann.launch.py` |
| 初始实车限速 | `0.3 m/s` | sim2real 安全策略 |

## 推荐采集流程

1. 在 Jetson 上停止占用底盘串口的节点。
2. 采集 Jetson 环境、串口延迟、CameraInfo 和传感器 topic。
3. 用 `scripts/create_measurement_pack.py` 生成字段包。
4. 把实测值写入 `docs/real_car_measurements.json`。
5. 运行校验和 gap report。

示例：

```bash
cd /home/osrbot/Desktop/osracer/osracer_lab
python3 scripts/create_measurement_pack.py \
  --template docs/real_car_measurements.template.json \
  --output-dir /tmp/osracer_real_measurement_pack
```

校验：

```bash
MEASUREMENTS_FILE=docs/real_car_measurements.json \
  scripts/validate_osracer_lab.sh real-measurements

MEASUREMENTS_FILE=docs/real_car_measurements.json \
  scripts/validate_osracer_lab.sh sim2real-readiness
```

## 标定 sim2real 前必须测量

| 类别 | 必填内容 |
|---|---|
| 整车质量 | 带电池、Jetson、相机、雷达、线束的总质量 |
| 轮胎 | 带负载轮半径、轮胎宽度、是否打滑 |
| 几何 | 前轮距、后轮距确认、轴距复测 |
| 转向 | 左右最大转向角、零点、死区、响应时间 |
| 电机 / ESC | 最大速度、最小稳定速度、加减速延迟、刹车延迟 |
| 编码器 | 每圈 tick、安装位置、实际速度换算误差 |
| IMU | 型号、频率、量程、坐标系、磁力计可用性 |
| 相机 | CameraInfo 内参、畸变、真实运行分辨率和帧率 |
| 雷达 | 真实扫描频率、角分辨率、时间戳来源 |
| 外参 | camera / lidar / IMU 相对 `base_link` 的 `xyz + rpy` |
| 时序 | 串口往返延迟、命令到执行延迟、传感器时间同步 |

## 最小首轮命令

Jetson 环境：

```bash
cd /home/osrbot/Desktop/osracer/osracer
tools/jetson_environment_report.py --output /tmp/osracer_jetson_environment.json
```

串口延迟：

```bash
cd /home/osrbot/Desktop/osracer/osracer_lab
python3 scripts/import_serial_latency_measurement.py \
  --measurements docs/real_car_measurements.json \
  --serial-latency /tmp/osracer_serial_latency.json
```

相机标定：

```bash
python3 scripts/import_camera_info_calibration.py \
  --measurements docs/real_car_measurements.json \
  --camera-info /tmp/osracer_camera_info.json
```

传感器预检查：

```bash
python3 scripts/import_sensor_preflight_measurements.py \
  --measurements docs/real_car_measurements.json \
  --sensor-summary /tmp/osracer_sensor_summary.json
```

## 更新规则

- 不要把未测量的猜测值写成已确认参数。
- 每个实测值都要记录单位、来源、时间和采集方式。
- 对视觉策略，必须先有 CameraInfo 标定再谈 sim2real。
- 对闭环实车，必须先通过 measurement、overlay、replay 和首车 gate。
