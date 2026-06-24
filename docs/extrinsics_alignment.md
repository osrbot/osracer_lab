# OSRacer 传感器外参对齐

当前 `osracer feat-demo` 中，URDF 和 static TF 对相机、雷达、IMU 的安装位置描述不一致。这个问题必须先解决，否则视觉、雷达、IMU 的 sim2real 标定没有统一坐标基准。

## 当前冲突

| 变换 | URDF `xyz rpy` | Static TF `xyz rpy` |
|---|---|---|
| `base_link -> camera_link` | `0.12323 -0.017229 -0.053395 -1.5708 0 -1.5708` | `0.30 0 0.075 0 0 0` |
| `base_link -> laser` | `-0.082558 -0.017229 0.034095 0 0 0` | `0.10 0 0.13 0 0 0` |
| `base_link -> imu_link` | `0.0417958953212156 -0.0177578126845364 -0.063598843109235 0 0 0` | `0.22 0 0.03 0 0 0` |

不要同时按两套外参做训练、replay 或实车标定。否则离线验证和实车 TF 会互相矛盾。

## 推荐唯一来源

推荐顺序：

1. 以实车物理测量值为准，记录每个传感器相对 `base_link` 的 `x y z roll pitch yaw`。
2. 把实测值写入 `docs/real_car_measurements.json`。
3. 用 `scripts/apply_sensor_extrinsics.py` 生成 measured overlay 或 review pack。
4. 评审通过后，再决定是更新 URDF、static TF，还是统一由一个 robot description 生成两者。

## 测量记录

每个传感器至少记录：

| 项 | 要求 |
|---|---|
| 坐标系 | 明确 `base_link` 原点和朝向 |
| 平移 | `x y z`，单位米 |
| 姿态 | `roll pitch yaw`，单位弧度或角度，但文档中要写清 |
| 证据 | 照片、测量工具、原始记录、测量人和日期 |
| 误差 | 说明估计误差，尤其是相机和雷达安装角 |

## ROS 在线检查

在实车或 Jetson 上检查当前 TF：

```bash
ros2 run tf2_ros tf2_echo base_link camera_link
ros2 run tf2_ros tf2_echo base_link laser
ros2 run tf2_ros tf2_echo base_link imu_link
```

同时确认传感器 topic 的 `frame_id`：

```bash
ros2 topic echo --once /rgb/image_raw/header
ros2 topic echo --once /scan/header
ros2 topic echo --once /imu/data/header
```

## 仓库更新闸门

在没有完成实测和评审前，`strict_extrinsics` 失败是预期结果。只有满足这些条件后才允许开启严格检查：

1. `docs/real_car_measurements.json` 中有相机、雷达、IMU 外参。
2. review pack 里包含照片或文本证据。
3. URDF 和 static TF 的来源已经统一。
4. `scripts/check_runtime_contract.py --strict-extrinsics` 通过。

检查命令：

```bash
scripts/validate_osracer_lab.sh runtime-contract
python3 scripts/check_runtime_contract.py \
  --osracer-root /home/osrbot/Desktop/osracer/osracer \
  --strict-extrinsics
```
