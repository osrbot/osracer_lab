# Sim2Real / Jetson

OSRacer sim2real has three stages: export the policy, validate offline, then run conservative low-speed tests on Jetson.

## Roles

| Platform | Role | Not for |
|---|---|---|
| RTX 4080 SUPER server | Isaac Lab training, export, batched simulation | Direct real-car control |
| Jetson Orin Nano Super 8G | ROS 2, sensors, inference, real-car loop | Large-scale Isaac Lab training |
| ESP32 / osrcore | Motor, steering, IMU, encoder, serial protocol | Policy inference |

## 1. Package Deployment Artifacts

```bash
python3 scripts/package_jetson_deployment.py \
  --task Isaac-OSRacerVisualRL-v0 \
  --policy logs/rsl_rl/osracer_visual/<run>/exported/policy.pt \
  --measured-overlay /tmp/osracer_measured_overlay.json \
  --output-dir /tmp/osracer_jetson_deployment
```

The package contains:

```text
policy.pt
hardware_params.json
measured_overlay.json
manifest.json
SHA256SUMS
```

## 2. Jetson Preflight

```bash
cd /path/to/osracer_jetson_deployment
sha256sum -c SHA256SUMS
/path/to/osracer/tools/verify_jetson_deployment.py .
/path/to/osracer/tools/jetson_preflight.sh --policy policy.pt --offline-smoke
```

## 3. Collect Real-Car Measurements

```bash
cd /home/osrbot/Desktop/osracer/osracer
tools/jetson_measurement_session.sh \
  --output-dir /tmp/osracer_measurement_session
```

Import the session into `docs/real_car_measurements.json` before calibrated sim2real.

## 4. Offline Replay

Replay real observations through the exported policy before closed-loop driving:

```bash
python3 scripts/run_sim2real_replay_pipeline.py \
  --policy-replay-csv /tmp/policy_replay.csv \
  --output-dir /tmp/osracer_sim2real_replay
```

## 5. Before First Closed Loop

- `runtime-contract` passes.
- Required real measurements are filled.
- Camera/lidar/IMU extrinsics are unified.
- Policy replay has no non-finite values.
- Watchdog and zero-speed fallback are verified.
- Start with `speed <= 0.3 m/s`.
- Test on blocks before floor driving.

## First Debug Targets

If something fails, check in this order:

1. Serial device and firmware stream mode.
2. ROS topic names and frame IDs.
3. Observation ordering and scaling.
4. Policy output units.
5. Watchdog and stale observation behavior.
