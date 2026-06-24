# Calibration

Calibration is the core of sim2real. Without calibration, a policy should only be used for offline validation or conservative low-speed tests.

## Recommended Order

1. Fill `docs/real_car_measurements.json` from the template.
2. Import CameraInfo calibration.
3. Import serial latency and sensor preflight measurements.
4. Resolve camera/lidar/IMU extrinsics.
5. Generate a measured overlay.
6. Generate a calibration review pack.
7. Run offline replay.
8. Only then prepare low-speed real-car tests.

## Camera Intrinsics

Visual sim2real requires deployed-resolution CameraInfo:

```bash
python3 scripts/import_camera_info_calibration.py \
  --measurements docs/real_car_measurements.json \
  --camera-info /tmp/osracer_camera_info.json
```

Do not treat the advertised `130 deg` FOV as calibrated intrinsics.

## Sensor Extrinsics

Resolve `base_link -> camera_link`, `base_link -> laser`, and `base_link -> imu_link` before strict sim2real:

```bash
python3 scripts/apply_sensor_extrinsics.py \
  --measurements docs/real_car_measurements.json \
  --output /tmp/osracer_measured_overlay.json
```

## Review Pack

```bash
python3 scripts/create_calibration_review_pack.py \
  --measurements docs/real_car_measurements.json \
  --output-dir /tmp/osracer_calibration_review_pack
```

Verify it:

```bash
python3 scripts/verify_calibration_review_pack.py /tmp/osracer_calibration_review_pack
```

## Pass Criteria

`sim2real-readiness` must pass at least these gates:

- runtime interface
- required real measurements
- camera calibration overlay for visual policies
- measured sensor extrinsics
- review evidence
