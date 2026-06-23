# OSRacer Policy Deployment Notes

This repository currently verifies training and simulation and ships a checkpoint export script.
The sibling ROS 2 workspace `/home/osrbot/Desktop/osracer/osracer` ships the runtime inference node and CSV replay tool.
Use this document as the deployment contract between training, export, replay, and real-car bringup.

## Current Verified Artifacts

- Drift baseline: `logs/rsl_rl/osracer_drift/2026-06-23_17-05-26/model_1999.pt`
  - Command: `scripts/train_osracer_drift.py --headless --num_envs 2048 --max_iterations 2000`
  - Result: completed successfully on the RTX 4080 SUPER host.
- Visual stability check: `logs/rsl_rl/osracer_visual/2026-06-23_17-54-56/model_49.pt`
  - Command: `scripts/train_osracer_drift.py --task Isaac-OSRacerVisualRL-v0 --headless --num_envs 256 --max_iterations 50`
  - Result: completed successfully after finite-observation and non-finite-state guards.
- Visual throughput probe: `logs/rsl_rl/osracer_visual/2026-06-23_18-08-58/model_9.pt`
  - Command: `scripts/train_osracer_drift.py --task Isaac-OSRacerVisualRL-v0 --headless --num_envs 512 --max_iterations 10`
  - Result: completed successfully; this is a throughput probe, not a trained policy.

## Action Contract

The IsaacLab action is two-dimensional:

```text
[target_speed_mps, target_steering_rad]
```

Current simulation limits are defined in `source/osracer_lab_tasks/osracer_lab_tasks/common/actions.py`:

```text
max speed:    3.0 m/s
max steering: 0.488 rad
wheelbase:    0.285 m
rear track:   0.235 m
wheel radius: 0.050 m
```

The real OSRacer ROS 2 bridge in `/home/osrbot/Desktop/osracer/osracer` accepts both:

- `ackermann_msgs/msg/AckermannDrive` on `ackermann_cmd`
- `geometry_msgs/msg/Twist` on `cmd_vel`

Preferred deployment path for a learned policy is direct `AckermannDrive`:

```text
policy action[0] -> AckermannDrive.speed
policy action[1] -> AckermannDrive.steering_angle
```

The chassis bridge converts `AckermannDrive` to the firmware serial command:

```text
v <speed_mps> <steering_deg>
```

The launch defaults in `osracer_bringup/launch/chassis_ackermann.launch.py` are:

```text
port_name: /dev/osrbot_base
baud_rate: 460800
wheelbase: 0.285
max_steering_angle_deg: 30.0
cmd_watchdog_timeout_s: 0.5
```

Note: the simulation steering limit `0.488 rad` is about 27.96 deg, slightly below the bridge clamp of 30 deg.

## Recommended ROS 2 Integration Shape

Export a checkpoint before integrating with ROS 2:

```bash
~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/export_osracer_policy.py \
  --headless \
  --checkpoint logs/rsl_rl/osracer_drift/2026-06-23_17-05-26/model_1999.pt
```

The default output directory is `<checkpoint_dir>/exported/` and contains:

```text
policy.pt
```

ONNX export is available when explicitly requested:

```bash
~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/export_osracer_policy.py \
  --headless --format onnx \
  --checkpoint logs/rsl_rl/osracer_drift/2026-06-23_17-05-26/model_1999.pt
```

Add a separate inference node in the OSRacer ROS 2 workspace rather than coupling deployment code into the IsaacLab training package.

Recommended node responsibilities:

1. Load a trained RSL-RL checkpoint or an exported TorchScript/ONNX policy.
2. Subscribe to the observation sources required by the trained task.
3. Recreate the same observation ordering, scaling, clipping, and finite-value handling used in simulation.
4. Run inference at a bounded rate.
5. Publish `AckermannDrive` to `ackermann_cmd`.
6. Clamp speed and steering before publish.
7. Stop publishing or publish zero speed if observations are stale.

Drift policy deployment is the first practical target because it uses proprioceptive state rather than camera tensors.
Visual policy deployment needs an additional camera preprocessing node that matches `visual/mdp_sensors/observations.py`.
Real hardware parameters are tracked in `docs/hardware_parameters.md` and `osracer_lab_assets.hardware_params`.

## Bringup Sequence

On the car workspace:

```bash
ros2 launch osracer_bringup chassis_ackermann.launch.py
```

Check bridge inputs:

```bash
ros2 topic info /ackermann_cmd
ros2 topic info /cmd_vel
ros2 topic echo /odom
ros2 topic echo /imu/data
```

Manual low-speed command check:

```bash
ros2 topic pub --once /ackermann_cmd ackermann_msgs/msg/AckermannDrive \
  "{speed: 0.2, steering_angle: 0.0}"
```

Stop command:

```bash
ros2 topic pub --once /ackermann_cmd ackermann_msgs/msg/AckermannDrive \
  "{speed: 0.0, steering_angle: 0.0}"
```

## Safety Gates Before Real Driving

- Check the current sim2real gate summary before enabling closed loop:

```bash
scripts/validate_osracer_lab.sh sim2real-readiness
```

- Treat `scripts/validate_osracer_lab.sh sim2real-ready-strict` as the gate for calibrated closed-loop sim2real. It should fail until measured real-car parameters and unified sensor extrinsics are in place.
- Start with `speed <= 0.3 m/s` until the inference node and watchdog behavior are verified.
- Keep `steering_angle` inside `[-0.488, 0.488]` rad to match the simulation action envelope.
- Verify `cmd_watchdog_timeout_s=0.5` stops stale commands.
- Verify the policy node publishes zero speed when input observations are stale or non-finite.
- Run the car on blocks before floor testing.
- Keep RC/manual override available during all first-drive tests.

## Next Missing Work

The ROS 2 runtime path now exists in the sibling OSRacer workspace. Remaining work is validation and model fidelity:

1. Fill the missing real-car mass, steering, motor, encoder, IMU, extrinsic, and timing parameters.
2. Extend the MuJoCo sim2sim smoke model in `docs/mujoco_sim2sim.md` into calibrated rollouts with the same action and observation contract.
3. Replay recorded real-car observations through exported `policy.pt` before closed-loop driving.
4. Add a low-speed real-car checklist tied to `/ackermann_cmd`.
