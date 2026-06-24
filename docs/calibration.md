# 标定流程

标定是 sim2real 的核心。没有标定，策略只能做离线验证或低速保守测试。

## 推荐顺序

1. 车辆质量和轮径
2. 转向角和响应
3. 串口延迟
4. 相机内参
5. 相机/雷达/IMU 外参
6. Jetson 时间戳和性能
7. 离线 replay
8. 低速实车闭环

## 相机内参

相机硬件是 AR0234，全局快门，2.7 mm 镜头，广告 FOV 为 130 度。但训练/部署需要运行分辨率下的真实内参。

必须记录：

- width / height
- `fx`, `fy`, `cx`, `cy`
- distortion model
- distortion coefficients
- reprojection error
- 标定文件路径

## 传感器外参

用 `base_link` 作为父坐标系：

| Transform | 需要记录 |
|---|---|
| `base_link -> camera_link` | `x y z roll pitch yaw` |
| `base_link -> laser` | `x y z roll pitch yaw` |
| `base_link -> imu_link` | `x y z roll pitch yaw` |

测完后用：

```bash
python3 scripts/apply_sensor_extrinsics.py --help
python3 scripts/plan_calibration_updates.py --help
```

## 生成 review pack

```bash
MEASUREMENTS_FILE=/tmp/osracer_measurements_complete.json \
CALIBRATION_REVIEW_PACK_OUTPUT=/tmp/osracer_calibration_review_pack \
scripts/validate_osracer_lab.sh calibration-review-pack
```

review pack 用来在真正写回 URDF/static TF 前检查：

- 测量字段是否完整
- 外参是否和当前 URDF/static TF 冲突
- 证据文件 hash 是否一致
- 是否仍处于 no-writeback 状态

## 通过标准

`sim2real-readiness` 里至少这些项必须通过：

- runtime contract
- required real measurements
- measured sensor extrinsics applied
- strict extrinsics
- camera calibration overlay
