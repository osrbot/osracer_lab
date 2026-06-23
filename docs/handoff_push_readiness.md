# OSRacer Isaac / Jetson Handoff And Push Readiness

Date: 2026-06-24

This document is the operating checklist for continuing OSRacer Isaac,
Jetson Orin Nano Super 8GB runtime work, sim2sim, and sim2real preparation.
It is not push approval.

## Repository Map

| Area | Path | Branch | Role |
|---|---|---|---|
| Isaac / sim / deployment tooling | `/home/osrbot/Desktop/osracer/osracer_lab` | `main` | Primary development tree for OSRacer Isaac tooling |
| ROS upper computer | `/home/osrbot/Desktop/osracer/osracer` | `feat-demo` | Vehicle ROS bringup, Jetson tools, first-drive gates |
| Firmware source authority | `/home/osrbot/Desktop/osracer/osrcore` | source checkout | Read-only authority for firmware protocol and steering units |

`osracer` must stay on `feat-demo`. Do not use another ROS branch as the vehicle
source of truth for this work.

## Current State

- `osracer_lab` is locally ahead of origin and contains the IsaacLab, measurement,
  deployment, calibration review, MuJoCo sim2sim, and source-authority tooling.
- `osracer` `feat-demo` is locally ahead of its public baseline and contains the
  Jetson runtime, deployment verification, TensorRT, benchmark, and first-drive
  evidence tooling.
- The current readiness target is offline replay, evidence collection, and
  conservative first-drive preparation.
- Calibrated closed-loop sim2real is still blocked until real measurements,
  sensor extrinsics, and Jetson/vehicle evidence are collected.

## Recommended Execution Order

1. Confirm source authority and runtime contract in `osracer_lab`:

   ```bash
   cd /home/osrbot/Desktop/osracer/osracer_lab
   scripts/validate_osracer_lab.sh source-authority-snapshot
   scripts/validate_osracer_lab.sh runtime-contract
   scripts/validate_osracer_lab.sh measurement-consistency
   ```

2. Export or package the candidate policy from `osracer_lab`:

   ```bash
   python3 scripts/package_jetson_deployment.py \
     --policy /path/to/policy.pt \
     --measured-overlay /path/to/measured_overlay.json \
     --output-dir /tmp/osracer_jetson_deployment
   ```

3. On Jetson, run the ROS/runtime preflight from `osracer`:

   ```bash
   cd /home/osrbot/Desktop/osracer/osracer
   tools/jetson_preflight.sh \
     --policy /tmp/osracer_jetson_deployment/policy.pt \
     --offline-smoke \
     --environment-output /tmp/osracer_jetson_environment.json
   ```

4. Select the Jetson power mode from the target board, then save performance
   evidence:

   ```bash
   nvpmodel -q
   sudo tools/jetson_performance_profile.sh \
     --apply \
     --nvpmodel MODE_ID \
     --jetson-clocks \
     --set-cpu-governor \
     --json-output /tmp/osracer_performance_profile.json
   ```

5. Collect sensor, CameraInfo, IMU, lidar, odometry, serial, and environment
   evidence on the real car:

   ```bash
   tools/jetson_measurement_session.sh \
     --output-dir /tmp/osracer_measurement_session \
     --camera-topic /rgb/image_raw \
     --lidar-topic /scan \
     --imu-topic /imu_filter \
     --odom-topic /odometry/filtered
   ```

6. Import the measurement session back into `osracer_lab`:

   ```bash
   cd /home/osrbot/Desktop/osracer/osracer_lab
   MEASUREMENTS_FILE=docs/real_car_measurements.json \
   MEASUREMENT_SESSION_FILE=/tmp/osracer_measurement_session/measurement_session.json \
   scripts/validate_osracer_lab.sh import-measurement-session
   ```

7. Validate measurements and produce a calibration review pack:

   ```bash
   MEASUREMENTS_FILE=docs/real_car_measurements.json scripts/validate_osracer_lab.sh real-measurements
   MEASUREMENTS_FILE=docs/real_car_measurements.json scripts/validate_osracer_lab.sh sim2real-readiness
   MEASUREMENTS_FILE=docs/real_car_measurements.json CALIBRATION_REVIEW_PACK_OUTPUT=/tmp/osracer_calibration_review_pack scripts/validate_osracer_lab.sh calibration-review-pack
   python3 scripts/verify_calibration_review_pack.py /tmp/osracer_calibration_review_pack --require-complete
   ```

8. Before any first closed-loop motion, run the `osracer` first-drive gate and
   evidence pack workflow:

   ```bash
   cd /home/osrbot/Desktop/osracer/osracer
   tools/benchmark_policy_inference.py \
     --policy /tmp/osracer_jetson_deployment/policy.pt \
     --device cuda:0 \
     --output /tmp/osracer_policy_benchmark.json \
     --max-p95-ms 10.0

   tools/first_drive_gate.py \
     --package-dir /tmp/osracer_jetson_deployment \
     --policy-replay /tmp/osracer_policy_replay.csv \
     --sensor-summary /tmp/osracer_sensor_preflight/sensor_summary.json \
     --environment-report /tmp/osracer_jetson_environment.json \
     --serial-latency /tmp/osracer_serial_latency.json \
     --policy-benchmark /tmp/osracer_policy_benchmark.json \
     --performance-profile /tmp/osracer_performance_profile.json \
     --runtime-dir /tmp/osracer_runtime_monitor \
     --output /tmp/osracer_first_drive_gate.json

   tools/first_drive_evidence_pack.py \
     --gate-report /tmp/osracer_first_drive_gate.json \
     --output-dir /tmp/osracer_first_drive_evidence_pack \
     --overwrite

   tools/verify_first_drive_evidence_pack.py /tmp/osracer_first_drive_evidence_pack --require-pass
   ```

   For ONNX deployment packages, build TensorRT on the Jetson first and add
   `--tensorrt-build-report /tmp/osracer_tensorrt_build_report.json` to
   `tools/first_drive_gate.py`.

## Push Preparation Checklist

Run this only after the documentation and local verification state is final:

```bash
cd /home/osrbot/Desktop/osracer/osracer_lab
git status --short --branch
git diff --check
scripts/validate_osracer_lab.sh source-authority-snapshot
scripts/validate_osracer_lab.sh measurement-consistency

cd /home/osrbot/Desktop/osracer/osracer
git status --short --branch
git diff --check
tools/jetson_performance_profile.sh --json-output /tmp/osracer_perf_profile_check.json
tools/build_tensorrt_engine.sh \
  --onnx /tmp/osracer_trt_test/policy.onnx \
  --engine /tmp/osracer_trt_test/policy.engine \
  --fp16 \
  --workspace-mb 1024 \
  --log /tmp/osracer_trt_test/build.log \
  --report /tmp/osracer_trt_test/build_report.json \
  --dry-run
```

Before push, also review:

- No generated caches, temporary packs, private keys, tokens, Wi-Fi secrets, or
  real robot credentials are staged.
- `osracer` is still on `feat-demo`.
- The push target and branch are explicitly confirmed.
- The remaining unverified items are stated in the handoff message.

## Remaining Unverified Items

- Actual Orin Nano Super 8GB performance profile application.
- Actual TensorRT engine build without `--dry-run`.
- Full 21-item real-car measurement file from the physical car.
- Real CameraInfo-derived calibration from the AR0234 camera.
- Physical serial latency measurement against the current firmware.
- Passive observation recording, replay, and MuJoCo replay from the same real log.
- Low-speed closed-loop test on blocks and then on floor.
- Strict authenticated `osrcore` checkout verification if the firmware checkout is
  not present at `/home/osrbot/Desktop/osracer/osrcore`.

Do not push either repository until the push target and branch are explicitly
confirmed.
