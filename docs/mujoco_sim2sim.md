# MuJoCo Sim2Sim Plan

This repository keeps IsaacLab as the high-throughput training simulator. MuJoCo is used as a second simulator to catch action-contract, geometry, and dynamics mistakes before real-car tests.

## Current Scope

The current MuJoCo support is a kinematic contract smoke test:

- It reuses `osracer_lab_assets.hardware_params`.
- It generates a minimal MJCF model with the same wheelbase, rear track, wheel radius, steering clamp, and speed envelope.
- It keeps the action contract as `[target_speed_mps, target_steering_rad]`.
- It compiles the MJCF and can run a short planar Ackermann rollout when the `mujoco` Python package is installed.

It is not yet a calibrated contact dynamics model. Mass, steering response, motor/ESC response, tire friction, and sensor extrinsics still need real measurements before wheel-ground contact dynamics should be enabled.

## Commands

Export the shared hardware parameter source:

```bash
python3 scripts/export_hardware_params.py --output /tmp/osracer_hardware_params.json
```

Generate the MuJoCo smoke-test model:

```bash
python3 scripts/mujoco_sim2sim_smoke.py --xml-out /tmp/osracer_minimal.xml
```

If MuJoCo is installed in the active Python environment:

```bash
python3 scripts/mujoco_sim2sim_smoke.py --xml-out /tmp/osracer_minimal.xml --compile
```

Run a one-second kinematic smoke rollout:

```bash
python3 scripts/mujoco_sim2sim_smoke.py \
  --xml-out /tmp/osracer_rollout.xml \
  --rollout-steps 100 \
  --speed-mps 0.3 \
  --steering-rad 0.1
```

Expected output includes compile dimensions and rollout metrics:

```text
compiled nq=3 nv=3 nu=3
rollout steps=100 time_s=1 speed_mps=0.3 steering_rad=0.1 distance_m=...
```

Replay actions produced by the sibling ROS workspace tool `tools/policy_replay_csv.py`:

```bash
python3 scripts/mujoco_sim2sim_smoke.py \
  --xml-out /tmp/osracer_action_replay.xml \
  --actions-csv /tmp/osracer_policy_replay.csv \
  --steps-per-action 1
```

The action CSV must contain `speed_cmd` and `steering_cmd`. These are exactly the command columns appended by `tools/policy_replay_csv.py` in `/home/osrbot/Desktop/osracer/osracer`.

Expected output:

```text
compiled nq=3 nv=3 nu=3
actions_csv_rollout rows=... steps=... time_s=... distance_m=...
```

Run the full offline pipeline from recorded observations:

```bash
OSRACER_MUJOCO_PYTHON=/tmp/osracer_mujoco_venv/bin/python \
python3 scripts/run_sim2real_replay_pipeline.py \
  --observations /tmp/osracer_policy_observations.csv \
  --policy /path/to/policy.pt \
  --output-dir /tmp/osracer_sim2real_replay
```

The pipeline writes:

```text
/tmp/osracer_sim2real_replay/policy_replay.csv
/tmp/osracer_sim2real_replay/mujoco_replay.xml
```

## Next Work

1. Replace placeholder mass with measured full-vehicle mass.
2. Add measured steering servo latency and motor/ESC speed response.
3. Add camera, lidar, and IMU extrinsics from the real car.
4. Replay exported `policy.pt` through `tools/policy_replay_csv.py`, then feed its `speed_cmd` / `steering_cmd` output into the MuJoCo kinematic model.
5. Add calibrated wheel-ground contact dynamics after tire and mass data are measured.
6. Compare speed, yaw rate, turn radius, steering saturation, and termination behavior before real-car replay.
