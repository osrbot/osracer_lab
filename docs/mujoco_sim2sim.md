# MuJoCo Sim2Sim Plan

This repository keeps IsaacLab as the high-throughput training simulator. MuJoCo is used as a second simulator to catch action-contract, geometry, and dynamics mistakes before real-car tests.

## Current Scope

The current MuJoCo support is a contract smoke test:

- It reuses `osracer_lab_assets.hardware_params`.
- It generates a minimal MJCF model with the same wheelbase, rear track, wheel radius, steering clamp, and speed envelope.
- It keeps the action contract as `[target_speed_mps, target_steering_rad]`.
- It can compile the MJCF when the `mujoco` Python package is installed.

It is not yet a calibrated dynamics model. Mass, steering response, motor/ESC response, tire friction, and sensor extrinsics still need real measurements.

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

## Next Work

1. Install MuJoCo in the sim2sim Python environment.
2. Replace placeholder mass with measured full-vehicle mass.
3. Add measured steering servo latency and motor/ESC speed response.
4. Add camera, lidar, and IMU extrinsics from the real car.
5. Run exported `policy.pt` in IsaacLab and MuJoCo with the same initial states.
6. Compare speed, yaw rate, turn radius, steering saturation, and termination behavior before real-car replay.
