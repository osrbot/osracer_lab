# OSRacer Policy Deployment Interface

This page defines the interface between training, export, offline replay, and real-car bringup.

`osracer_lab` verifies training and simulation and exports checkpoints. The sibling ROS 2 workspace `/home/osrbot/Desktop/osracer/osracer` provides runtime inference and CSV replay tools.

## Verified Artifacts

- Drift baseline: `logs/rsl_rl/osracer_drift/2026-06-23_17-05-26/model_1999.pt`
  - Command: `scripts/train_osracer_drift.py --headless --num_envs 2048 --max_iterations 2000`
  - Result: completed successfully on the RTX 4080 SUPER host.
  - Scope: sim-only research baseline; not a default real-car deployment policy.
- Visual stability check: `logs/rsl_rl/osracer_visual/2026-06-23_17-54-56/model_49.pt`
  - Command: `scripts/train_osracer_drift.py --task Isaac-OSRacerVisualRL-v0 --headless --num_envs 256 --max_iterations 50`
- Visual throughput probe: `logs/rsl_rl/osracer_visual/2026-06-23_18-08-58/model_9.pt`
  - Command: `scripts/train_osracer_drift.py --task Isaac-OSRacerVisualRL-v0 --headless --num_envs 512 --max_iterations 10`

## Action Interface

Isaac Lab actions are two-dimensional:

```text
[target_speed_mps, target_steering_rad]
```

Current simulation limits:

```text
max speed:    3.0 m/s
max steering: 0.488 rad
wheelbase:    0.285 m
rear track:   0.235 m
wheel radius: 0.050 m
```

The real ROS 2 bridge accepts:

- `ackermann_msgs/msg/AckermannDrive` on `ackermann_cmd`
- `geometry_msgs/msg/Twist` on `cmd_vel`

Preferred learned-policy path:

```text
policy action[0] -> AckermannDrive.speed
policy action[1] -> AckermannDrive.steering_angle
```

The chassis bridge converts `AckermannDrive` into firmware serial commands:

```text
v <speed_mps> <steering_deg>
```

## Export And Package

Export a deployment-candidate TorchScript policy:

```bash
~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/export_osracer_policy.py \
  --headless \
  --task Isaac-OSRacerVisualRL-v0 \
  --checkpoint logs/rsl_rl/osracer_visual/<run>/model_1999.pt
```

Package for Jetson:

```bash
python3 scripts/package_jetson_deployment.py \
  --task Isaac-OSRacerVisualRL-v0 \
  --policy logs/rsl_rl/osracer_visual/<run>/exported/policy.pt \
  --measured-overlay /tmp/osracer_measured_overlay.json \
  --output-dir /tmp/osracer_jetson_deployment
```

For visual policies, `measured_overlay.json` must include CameraInfo-derived `camera_calibration` at the deployed resolution.

## Recommended ROS 2 Node

The inference node should live in the OSRacer ROS 2 workspace, not inside the Isaac Lab training package.

Responsibilities:

1. Load TorchScript or ONNX policy.
2. Subscribe to the trained task's observation sources.
3. Recreate observation ordering, scaling, clipping, and finite-value handling.
4. Run inference at a bounded rate.
5. Publish `AckermannDrive` to `ackermann_cmd`.
6. Clamp speed and steering before publish.
7. Publish zero speed or stop publishing on stale observations.

## Bringup Sequence

```bash
ros2 launch osracer_bringup chassis_ackermann.launch.py
```

Check inputs:

```bash
ros2 topic info /ackermann_cmd
ros2 topic info /cmd_vel
ros2 topic echo /odom
ros2 topic echo /imu/data
```

Low-speed command:

```bash
ros2 topic pub --once /ackermann_cmd ackermann_msgs/msg/AckermannDrive \
  "{speed: 0.2, steering_angle: 0.0}"
```

Stop:

```bash
ros2 topic pub --once /ackermann_cmd ackermann_msgs/msg/AckermannDrive \
  "{speed: 0.0, steering_angle: 0.0}"
```

## Safety Gates

- Check `scripts/validate_osracer_lab.sh sim2real-readiness`.
- Keep first tests at `speed <= 0.3 m/s`.
- Keep `steering_angle` within `[-0.488, 0.488]` rad.
- Verify `cmd_watchdog_timeout_s=0.5`.
- Verify stale observations lead to zero speed or no command.
- Test on blocks before floor driving.
- Keep RC/manual override available.

## Remaining Work

1. Fill missing mass, steering, motor, encoder, IMU, extrinsics, and timing parameters.
2. Extend MuJoCo smoke tests into calibrated rollouts.
3. Replay real-car observations through exported `policy.pt`.
4. Add a low-speed real-car checklist tied to `/ackermann_cmd`.
