# Sim2Sim

Sim2Sim does not replace Isaac Lab training. It uses a second simulator to check action formatting and parameter consistency before real-car tests.

## Current Path

| Step | Tool |
|---|---|
| Isaac Lab training | `scripts/train_osracer_drift.py` |
| Policy export | `scripts/export_osracer_policy.py` |
| CSV replay | `scripts/run_sim2real_replay_pipeline.py` |
| MuJoCo smoke | `scripts/mujoco_sim2sim_smoke.py` |

## MuJoCo Smoke

```bash
python3 scripts/mujoco_sim2sim_smoke.py \
  --xml-out /tmp/osracer_minimal.xml
```

With measured values:

```bash
python3 scripts/mujoco_sim2sim_smoke.py \
  --xml-out /tmp/osracer_overlay.xml \
  --measured-overlay /tmp/osracer_measured_overlay.json
```

## What To Check

- Speed unit is `m/s`.
- Steering unit is radians in policy output and degrees in firmware serial command.
- Steering sign matches ROS bridge and firmware.
- Wheelbase, track, and wheel radius use the intended parameter source.

## Do Not Overinterpret It

The current MuJoCo smoke is not a high-fidelity real-car simulator. It is an interface consistency checker for catching policy/bridge mismatches early.
