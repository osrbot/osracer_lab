# OSRacer Isaac / Jetson Implementation Status

Date: 2026-06-23

This document summarizes the current local implementation state across:

- `/home/osrbot/Desktop/osracer/osracer_lab`
- `/home/osrbot/Desktop/osracer/osracer`

Do not treat this as push approval. Both repositories are still local-ahead only.

## Current Git State

| Repository | Branch | State |
|---|---|---|
| `osracer_lab` | `main` | `main...origin/main [ahead 33]` |
| `osracer` | `dev` | `dev...origin/dev [ahead 17]` |

## Implemented In `osracer_lab`

- TorchScript policy export: `scripts/export_osracer_policy.py`
- Hardware parameter source: `source/osracer_lab_assets/osracer_lab_assets/hardware_params.py`
- Hardware parameter JSON export: `scripts/export_hardware_params.py`
- MuJoCo kinematic sim2sim smoke: `scripts/mujoco_sim2sim_smoke.py`
- Observation replay to MuJoCo pipeline: `scripts/run_sim2real_replay_pipeline.py`
- Runtime contract check against the upper-computer repo: `scripts/check_runtime_contract.py`
- Sim2real readiness summary: `scripts/sim2real_readiness.py`
- Real-car measurement value validator: `scripts/validate_real_measurements.py`
- Real-car measurement template: `docs/real_car_measurements.template.json`
- Sensor extrinsics measured-value checker/writer: `scripts/apply_sensor_extrinsics.py`
- Jetson deployment package creation: `scripts/package_jetson_deployment.py`
- Documentation:
  - `docs/deployment.md`
  - `docs/hardware_parameters.md`
  - `docs/mujoco_sim2sim.md`
  - `docs/real_car_measurement_checklist.md`
  - `docs/extrinsics_alignment.md`

## Implemented In `osracer`

- TorchScript inference node and launch path for `/ackermann_cmd`
- Policy observation recorder for real-car passive logs
- CSV policy replay: `tools/policy_replay_csv.py`
- Replay summary gate: `tools/policy_replay_summary.py`
- Jetson preflight: `tools/jetson_preflight.sh`
- Read-only real-car readiness check: `tools/real_car_readiness_check.sh`
- Jetson runtime monitor and summary:
  - `tools/jetson_runtime_monitor.sh`
  - `tools/jetson_runtime_summary.py`
- Jetson deployment package verifier: `tools/verify_jetson_deployment.py`
- Jetson performance profile helper: `tools/jetson_performance_profile.sh`
- TensorRT engine build helper: `tools/build_tensorrt_engine.sh`
- Policy inference benchmark and trtexec log parser: `tools/benchmark_policy_inference.py`
- First-drive runbook: `docs/first_drive_runbook.md`
- Jetson runtime plan: `docs/jetson_orin_runtime.md`

## Verified Commands

Run from `osracer_lab`:

```bash
scripts/validate_osracer_lab.sh runtime-contract
scripts/validate_osracer_lab.sh sim2real-readiness
MEASUREMENTS_FILE=/tmp/osracer_measurements_complete.json scripts/validate_osracer_lab.sh real-measurements
MEASUREMENTS_FILE=/tmp/osracer_measurements_complete.json scripts/validate_osracer_lab.sh sim2real-readiness
python3 scripts/export_hardware_params.py --output /tmp/osracer_hardware_params.json
python3 scripts/package_jetson_deployment.py \
  --policy /tmp/osracer_dummy_policy.pt \
  --output-dir /tmp/osracer_deploy_pkg_readme_clean
```

Run from `osracer`:

```bash
tools/jetson_preflight.sh
tools/jetson_runtime_monitor.sh --duration 1 --output-dir /tmp/osracer_runtime_monitor_smoke
tools/jetson_runtime_summary.py /tmp/osracer_runtime_monitor_smoke
tools/verify_jetson_deployment.py /tmp/osracer_deploy_pkg_readme_clean --skip-policy-load
```

## Current Readiness Result

`scripts/validate_osracer_lab.sh sim2real-readiness` currently returns:

```text
sim2real_readiness: fail
[PASS] runtime_contract
[FAIL] strict_extrinsics
[FAIL] required_real_measurements
```

This is expected. The current code is ready for offline replay and conservative
first-drive preparation, not calibrated closed-loop sim2real.

## Blocking Items Before Calibrated Closed Loop

1. Resolve `base_link -> camera_link`, `base_link -> laser`, and `base_link -> imu_link` source-of-truth conflict between URDF and static TF.
2. Measure and record the 20 required real-car parameters in `docs/real_car_measurements.json`, copied from `docs/real_car_measurements.template.json`, and pass `scripts/validate_osracer_lab.sh real-measurements`.
3. Install/check Jetson runtime dependencies on the actual Orin Nano Super 8GB:
   - ROS 2 Jazzy runtime packages
   - `ackermann_msgs`
   - Torch or ONNX/TensorRT runtime for the deployment format
4. Run passive real-car observation recording.
5. Replay recorded observations through the packaged policy.
6. Run MuJoCo action replay from the same observations.
7. Only then enable low-speed closed loop on blocks, then floor.

## Push-Readiness Notes

Before any push:

```bash
git diff --check
rg -n "<team-sensitive-patterns>" .
```

Do not push either repository until the push target and branch are explicitly confirmed.
