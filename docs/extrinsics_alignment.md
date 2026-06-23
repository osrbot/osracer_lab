# OSRacer Sensor Extrinsics Alignment

This runbook resolves the current `base_link -> camera/lidar/imu` source-of-truth
conflict before calibrated sim2real.

## Current Conflict

The upper-computer repo currently exposes two different transform sets:

| Frame | URDF `xyz rpy` | Static TF launch `xyz rpy` |
|---|---|---|
| `camera_link` | `0.12323 -0.017229 -0.053395 -1.5708 0 -1.5708` | `0.30 0 0.075 0 0 0` |
| `laser` | `-0.082558 -0.017229 0.034095 0 0 0` | `0.10 0 0.13 0 0 0` |
| `imu_link` | `0.0417958953212156 -0.0177578126845364 -0.063598843109235 0 0 0` | `0.22 0 0.03 0 0 0` |

Do not tune visual, lidar, or IMU sim2real against both sets. Pick one measured
source and propagate it everywhere.

## Recommended Source Of Truth

Use measured physical mounting as the source of truth, then update generated or
handwritten robot description files from that measurement.

Recommended order:

1. Measure sensor positions on the assembled car relative to `base_link`.
2. Decide the sign convention and axes using ROS REP-103 frames.
3. Update the OSRacer ROS description and static TF path so they agree.
4. Update `osracer_lab_assets.hardware_params.OSRACER_SENSOR_EXTRINSICS`.
5. Run the strict runtime contract check.

## Measurement Notes

Use meters and radians in repo parameters.

For each sensor, record:

| Field | Meaning |
|---|---|
| `x` | forward from `base_link` |
| `y` | left from `base_link` |
| `z` | up from `base_link` |
| `roll` | rotation around x |
| `pitch` | rotation around y |
| `yaw` | rotation around z |

For the camera, also record whether `camera_link` follows optical frame
convention directly or whether a separate optical frame transform is required.
The AR0234 image pipeline should not be tuned until this is settled.

For the lidar, confirm whether the first scan angle and increasing angle
direction match the ROS driver output.

For the IMU, confirm that the frame used by firmware quaternion output matches
the ROS `imu_link` frame. A visually plausible pose can still have inverted yaw
or swapped axes.

## Live ROS Checks

On the Jetson or dev machine with the ROS workspace sourced:

```bash
ros2 launch osracer_description robot_description_tf.launch.py
ros2 run tf2_ros tf2_echo base_link camera_link
ros2 run tf2_ros tf2_echo base_link laser
ros2 run tf2_ros tf2_echo base_link imu_link
```

If the robot state publisher is active from URDF at the same time, check for
duplicate publishers:

```bash
ros2 topic echo /tf_static --once
```

There should be one intended static transform for each sensor frame.

## Repo Update Gate

After recording measured `camera_extrinsic_xyz_rpy_in_base_link`,
`lidar_extrinsic_xyz_rpy_in_base_link`, and
`imu_extrinsic_xyz_rpy_in_base_link` in the measurement JSON, use this value
format for each item:

```json
{"value": [x, y, z, roll, pitch, yaw], "source": "measurement note or log"}
```

Review the planned alignment first:

```bash
cd /home/osrbot/Desktop/osracer/osracer_lab
MEASUREMENTS_FILE=docs/real_car_measurements.json \
  scripts/validate_osracer_lab.sh calibration-plan
MEASUREMENTS_FILE=docs/real_car_measurements.json \
  scripts/validate_osracer_lab.sh sensor-extrinsics-check
```

The calibration review pack also writes `sensor_extrinsics_review.json`, which
records measured, URDF, and static TF values for each sensor frame.

If the measured values are correct, apply them to the URDF, static TF launch,
and IsaacLab hardware parameter source:

```bash
MEASUREMENTS_FILE=docs/real_car_measurements.json \
  scripts/validate_osracer_lab.sh sensor-extrinsics-write
```

After updating transforms, run:

```bash
scripts/validate_osracer_lab.sh runtime-contract
python3 scripts/check_runtime_contract.py \
  --osracer-root /home/osrbot/Desktop/osracer/osracer \
  --strict-extrinsics
```

Pass condition:

- Normal runtime contract check passes.
- Strict extrinsics check passes.
- `docs/hardware_parameters.md` no longer lists conflicting values for the
  active source of truth.
- The first passive real-car log uses the same frame names as simulation.

Stop if:

- URDF and static TF still disagree.
- `camera_link`, `laser`, or `imu_link` has more than one static publisher.
- IMU yaw sign or lidar angle direction disagrees with manual motion.
