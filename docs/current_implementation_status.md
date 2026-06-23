# OSRacer Isaac / Jetson Implementation Status

Date: 2026-06-24

This document summarizes the current local implementation state across:

- `/home/osrbot/Desktop/osracer/osracer_lab`
- `/home/osrbot/Desktop/osracer/osracer`

Do not treat this as push approval. Both repositories are still local-ahead only.

## Current Git State

| Repository | Branch | State |
|---|---|---|
| `osracer_lab` | `main` | local-ahead push-prep state; run `git status --short --branch` before pushing |
| `osracer` on server | `feat-demo` | synchronized to Mac/GitHub `feat-demo` at `6d96f52`; server is not used for `feat-demo` push |
| `osracer` on Mac | `feat-demo` at `/Users/winter/.codex/worktrees/904a/osracer` | authoritative local push-prep worktree for `feat-demo`, currently `6d96f52` |

## Implemented In `osracer_lab`

- TorchScript policy export: `scripts/export_osracer_policy.py`
- Hardware parameter source: `source/osracer_lab_assets/osracer_lab_assets/hardware_params.py`
- Hardware parameter JSON export: `scripts/export_hardware_params.py`
- AR0234-derived IsaacLab pinhole camera helper: `ar0234_pinhole_camera_cfg()`
- 25m lidar planar scan helper: `lidar_25m_planar_scan_cfg()`
- Simulation sensor contract check: `scripts/check_sim_sensor_contract.py`
- MuJoCo kinematic sim2sim smoke with measured overlay support: `scripts/mujoco_sim2sim_smoke.py`
- Observation replay to MuJoCo pipeline: `scripts/run_sim2real_replay_pipeline.py`
- Source authority check for `osrcore` and `osracer feat-demo`: `scripts/check_source_authority.py`
  - Defaults to sibling `/home/osrbot/Desktop/osracer/osrcore` for direct firmware checks when present.
- Read-only local source authority snapshot: `docs/source_authority_snapshot.json`
- Source authority snapshot generator: `scripts/create_source_authority_snapshot.py`
- Source authority snapshot verifier: `scripts/verify_source_authority_snapshot.py`
- Runtime contract check against the upper-computer repo: `scripts/check_runtime_contract.py`
- Sim2real readiness summary: `scripts/sim2real_readiness.py`
  - Reports measured sensor extrinsics application as an explicit gate.
- Hardware params loader for non-Isaac CLI tools: `scripts/hardware_params_loader.py`
- Real-car measurement value validator: `scripts/validate_real_measurements.py`
  - Checks cross-field consistency for speed envelope, steering symmetry, battery voltage order, camera runtime resolution, and serial latency/baud.
- Measurement consistency self-check: `scripts/check_measurement_consistency.py`
- Grouped real-car measurement gap report: `scripts/measurement_gap_report.py`
- Real-car measurement seed generator: `scripts/collect_real_measurement_seed.py`
  - Seeds firmware-derived steering protocol units from `docs/source_authority_snapshot.json` when available.
- Field measurement pack generator: `scripts/create_measurement_pack.py`
- Jetson sensor preflight measurement importer: `scripts/import_sensor_preflight_measurements.py`
- Serial latency measurement importer: `scripts/import_serial_latency_measurement.py`
- ROS CameraInfo calibration importer: `scripts/import_camera_info_calibration.py`
- Combined measurement session importer: `scripts/import_measurement_session.py`
  - Imports CameraInfo calibration when `tools.jetson_measurement_session.sh` captured it.
  - Field measurement pack now shows explicit camera/lidar/IMU/odom topic arguments for the combined session.
- Jetson environment evidence importer: `scripts/import_measurement_session.py` records `collection.jetson_environment`
- Real-car measurement template: `docs/real_car_measurements.template.json`
  - Includes camera intrinsics/distortion as a required visual sim2real measurement.
- Sensor extrinsics measured-value checker/writer: `scripts/apply_sensor_extrinsics.py`
- Calibration update dry-run planner: `scripts/plan_calibration_updates.py`
- Measured parameter overlay export: `scripts/export_measured_overlay.py`
- Camera calibration overlay gate: `scripts/check_camera_calibration_overlay.py`
- Calibration review pack export: `scripts/create_calibration_review_pack.py`
  - Includes `sensor_extrinsics_review.json` for measured-vs-URDF/static-TF alignment.
  - Archives text evidence referenced by measurement-session collection metadata into `evidence/` plus `evidence_manifest.json`.
- Calibration review pack verifier: `scripts/verify_calibration_review_pack.py`
  - Rechecks required files, evidence hashes, summary consistency, and no-writeback flag.
- Jetson deployment package creation: `scripts/package_jetson_deployment.py`
  - Includes `source_authority_snapshot.json` when available.
- Documentation:
  - `docs/deployment.md`
  - `docs/hardware_parameters.md`
  - `docs/mujoco_sim2sim.md`
  - `docs/real_car_measurement_checklist.md`
  - `docs/extrinsics_alignment.md`
  - `docs/handoff_push_readiness.md`

## Implemented In `osracer`

- TorchScript inference node and launch path for `/ackermann_cmd`
- Policy observation recorder for real-car passive logs
- CSV policy replay: `tools/policy_replay_csv.py`
- Replay summary gate: `tools/policy_replay_summary.py`
- Jetson preflight: `tools/jetson_preflight.sh --environment-output /tmp/osracer_jetson_environment.json`
- Jetson environment report: `tools/jetson_environment_report.py`
- Jetson measurement session now includes environment and CameraInfo evidence: `tools/jetson_measurement_session.sh`
  - Accepts camera/lidar/IMU/odom topic overrides and records them in `measurement_session.json`.
- Read-only real-car readiness check: `tools/real_car_readiness_check.sh`
- Jetson runtime monitor and summary:
  - `tools/jetson_runtime_monitor.sh`
  - `tools/jetson_runtime_summary.py`
- Jetson deployment package verifier: `tools/verify_jetson_deployment.py`
  - Verifies packaged source authority snapshot when included.
  - Requires CameraInfo-derived camera calibration for visual deployment packages.
- Jetson performance profile helper: `tools/jetson_performance_profile.sh`
  - Can write machine-readable JSON evidence with `--json-output`.
- TensorRT engine build helper: `tools/build_tensorrt_engine.sh`
  - Can write machine-readable build reports with `--report`.
- Policy inference benchmark and trtexec log parser: `tools/benchmark_policy_inference.py`
- First-drive runbook: `docs/first_drive_runbook.md`
- First-drive go/no-go gate: `tools/first_drive_gate.py`
  - Reports deployment package source authority snapshot as an explicit gate check.
  - Reports visual camera calibration overlay as an explicit gate check.
  - Reports policy inference p95 latency as an explicit gate check when supplied.
  - Requires Jetson performance profile JSON evidence before first drive.
  - Requires TensorRT build report evidence for ONNX deployment packages.
- First-drive evidence pack: `tools/first_drive_evidence_pack.py`
  - Archives deployment package `source_authority_snapshot.json` when supplied.
  - Archives `policy_benchmark.json` when supplied by the first-drive gate.
  - Archives `performance_profile.json` when supplied by the first-drive gate.
  - Archives `tensorrt_build_report.json` when supplied by the first-drive gate.
- First-drive evidence pack verifier: `tools/verify_first_drive_evidence_pack.py`
  - Rechecks archived visual deployment packages for camera calibration evidence.
  - Rechecks archived Jetson performance profile and TensorRT build report semantics.
- Jetson runtime plan: `docs/jetson_orin_runtime.md`
  - Jetson documentation changes are merged into Mac `feat-demo` at `/Users/winter/.codex/worktrees/904a/osracer`; the server `feat-demo` is kept synchronized but is not used for pushing.

## Verified Commands

Run from `osracer_lab`:

```bash
scripts/validate_osracer_lab.sh source-authority
scripts/validate_osracer_lab.sh source-authority-snapshot
scripts/validate_osracer_lab.sh runtime-contract
MEASUREMENT_SEED_OUTPUT=/tmp/osracer_measurements_seed.json scripts/validate_osracer_lab.sh measurement-seed
MEASUREMENTS_FILE=/tmp/osracer_measurements_seed.json MEASUREMENT_PACK_OUTPUT=/tmp/osracer_real_measurement_pack scripts/validate_osracer_lab.sh measurement-pack
MEASUREMENTS_FILE=/tmp/osracer_measurements_seed.json SENSOR_SUMMARY_FILE=/tmp/osracer_sensor_summary_valid.json scripts/validate_osracer_lab.sh import-sensor-preflight
MEASUREMENTS_FILE=/tmp/osracer_measurements_seed.json SERIAL_LATENCY_FILE=/tmp/osracer_serial_latency_valid.json scripts/validate_osracer_lab.sh import-serial-latency
MEASUREMENTS_FILE=/tmp/osracer_measurements_seed.json CAMERA_INFO_FILE=/tmp/osracer_camera_info_valid.json scripts/validate_osracer_lab.sh import-camera-info
MEASUREMENTS_FILE=/tmp/osracer_measurements_seed.json MEASUREMENT_SESSION_FILE=/tmp/osracer_measurement_session_valid/measurement_session.json scripts/validate_osracer_lab.sh import-measurement-session
MEASUREMENTS_FILE=docs/real_car_measurements.template.json scripts/validate_osracer_lab.sh measurement-gap
scripts/validate_osracer_lab.sh measurement-consistency
MEASUREMENTS_FILE=/tmp/osracer_measurements_seed.json scripts/validate_osracer_lab.sh sim2real-readiness
MEASUREMENTS_FILE=/tmp/osracer_measurements_complete.json scripts/validate_osracer_lab.sh calibration-plan
MEASUREMENTS_FILE=/tmp/osracer_measurements_complete.json MEASURED_OVERLAY_OUTPUT=/tmp/osracer_measured_overlay.json scripts/validate_osracer_lab.sh measured-overlay
MEASUREMENTS_FILE=/tmp/osracer_measurements_complete.json CALIBRATION_REVIEW_PACK_OUTPUT=/tmp/osracer_calibration_review_pack scripts/validate_osracer_lab.sh calibration-review-pack
bash /tmp/osracer_run_review_pack_evidence_test.sh
bash /tmp/osracer_test_review_pack_verifier.sh
MEASUREMENTS_FILE=/tmp/osracer_measurements_complete.json scripts/validate_osracer_lab.sh real-measurements
MEASUREMENTS_FILE=/tmp/osracer_measurements_complete.json scripts/validate_osracer_lab.sh sim2real-readiness
MEASURED_OVERLAY_FILE=/tmp/osracer_measured_overlay.json scripts/validate_osracer_lab.sh camera-calibration-overlay
python3 scripts/export_hardware_params.py --output /tmp/osracer_hardware_params.json
python3 scripts/mujoco_sim2sim_smoke.py --xml-out /tmp/osracer_overlay_smoke.xml --measured-overlay /tmp/osracer_measured_overlay.json
python3 scripts/package_jetson_deployment.py \
  --policy /tmp/osracer_dummy_policy.pt \
  --measured-overlay /tmp/osracer_measured_overlay.json \
  --output-dir /tmp/osracer_deploy_pkg_readme_clean
```

Run from `osracer`:

```bash
tools/jetson_performance_profile.sh --json-output /tmp/osracer_perf_profile_compat.json
tools/build_tensorrt_engine.sh --onnx /tmp/osracer_trt_test/policy.onnx --engine /tmp/osracer_trt_test/policy.engine --fp16 --workspace-mb 1024 --log /tmp/osracer_trt_test/build.log --report /tmp/osracer_trt_test/build_report.json --dry-run
bash /tmp/osracer_session_topic_smoke.sh
tools/jetson_preflight.sh
tools/jetson_environment_report.py --output /tmp/osracer_jetson_environment.json
tools/jetson_runtime_monitor.sh --duration 1 --output-dir /tmp/osracer_runtime_monitor_smoke
tools/jetson_runtime_summary.py /tmp/osracer_runtime_monitor_smoke
tools/verify_jetson_deployment.py /tmp/osracer_deploy_pkg_readme_clean --skip-policy-load
python3 /tmp/osracer_test_perf.py
bash /tmp/osracer_test_evidence_perf.sh
python3 /tmp/osracer_test_trt_report.py
bash /tmp/osracer_test_trt_evidence.sh
python3 /tmp/osracer_test_first_drive_verifier_reports.py
```

## Current Readiness Result

`scripts/validate_osracer_lab.sh sim2real-readiness` currently returns:

```text
sim2real_readiness: fail
[PASS] runtime_contract
[FAIL] strict_extrinsics
[FAIL] measured_sensor_extrinsics_applied
[FAIL] required_real_measurements
```

This is expected. The current code is ready for offline replay and conservative
first-drive preparation, not calibrated closed-loop sim2real.

## Blocking Items Before Calibrated Closed Loop

1. Resolve `base_link -> camera_link`, `base_link -> laser`, and `base_link -> imu_link` source-of-truth conflict between URDF and static TF.
2. Measure and record the 21 required real-car parameters in `docs/real_car_measurements.json`, copied from `docs/real_car_measurements.template.json`, and pass `scripts/validate_osracer_lab.sh real-measurements`.
3. Put an authenticated `osrbot/osrcore` checkout at `/home/osrbot/Desktop/osracer/osrcore`, then pass `python3 scripts/check_source_authority.py --strict-osrcore`.
4. Install/check Jetson runtime dependencies on the actual Orin Nano Super 8GB:
   - ROS 2 Jazzy runtime packages
   - `ackermann_msgs`
   - Torch or ONNX/TensorRT runtime for the deployment format
5. Run passive real-car observation recording.
6. Replay recorded observations through the packaged policy.
7. Run MuJoCo action replay from the same observations.
8. Only then enable low-speed closed loop on blocks, then floor.

## Push-Readiness Notes

Before any push:

```bash
git status --short --branch
git diff --check
rg -n "<team-sensitive-patterns>" .
```

Do not push either repository until the push target and branch are explicitly confirmed.
