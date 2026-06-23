# OSRacer Real-Car Measurement Checklist

Use this checklist to turn real hardware facts into calibrated sim2sim and
sim2real parameters. Keep raw notes, photos, and logs with each measurement.
Use `docs/extrinsics_alignment.md` for the camera, lidar, and IMU frame
alignment procedure.

## Confirmed From Current Repos

| Item | Value | Source |
|---|---|---|
| Wheelbase | `0.285 m` | IsaacLab action config and `chassis_ackermann.launch.py` |
| Rear track | `0.235 m` | IsaacLab hardware parameter source |
| Wheel radius | `0.050 m` | IsaacLab action config |
| Simulation max steering | `0.488 rad` | IsaacLab action envelope |
| ROS bridge max steering | `30 deg` | `chassis_ackermann.launch.py` |
| First real-car speed clamp | `0.3 m/s` | deployment/runbook convention |
| Chassis serial | `/dev/osrbot_base @ 460800` | `chassis_ackermann.launch.py` |
| Command protocol | `v <speed_mps> <steering_deg>` | `chassis_ackermann.py` |
| Camera | AR0234, global shutter, `2.7 mm`, advertised `130 deg` | user-supplied camera spec |
| Lidar | 270 deg mechanical pulse-TOF, `>=25 m`, Class 1 | user-supplied lidar spec |


Create the machine-readable measurement file before updating calibrated sim parameters:

Generate a field pack for manual measurements and evidence files:

```bash
MEASUREMENT_PACK_OUTPUT=/tmp/osracer_real_measurement_pack \
  scripts/validate_osracer_lab.sh measurement-pack
```

A combined Jetson evidence session can collect sensor topic rates and serial query latency in one directory:

```bash
cd /home/osrbot/Desktop/osracer/osracer
tools/jetson_measurement_session.sh --output-dir /tmp/osracer_measurement_session
# The session includes sensor preflight, Jetson environment, and serial latency evidence.
cd /home/osrbot/Desktop/osracer/osracer_lab
scripts/validate_osracer_lab.sh measurement-seed
MEASUREMENTS_FILE=docs/real_car_measurements.json \
MEASUREMENT_SESSION_FILE=/tmp/osracer_measurement_session/measurement_session.json \
  scripts/validate_osracer_lab.sh import-measurement-session
```

Or run the individual import steps:

```bash
scripts/validate_osracer_lab.sh measurement-seed
# Fill every required value and source field with real measurements.
MEASUREMENTS_FILE=docs/real_car_measurements.json \
  scripts/validate_osracer_lab.sh real-measurements
MEASUREMENTS_FILE=docs/real_car_measurements.json \
  scripts/validate_osracer_lab.sh sim2real-readiness
```

After running `tools/jetson_sensor_preflight.sh` in the `osracer` repo on the
Jetson, attach its topic-rate evidence to the measurement file:

```bash
MEASUREMENTS_FILE=docs/real_car_measurements.json \
SENSOR_SUMMARY_FILE=/tmp/osracer_sensor_preflight/sensor_summary.json \
  scripts/validate_osracer_lab.sh import-sensor-preflight
```

`import-sensor-preflight` only completes `sensor_timestamp_sync_method` when the
required camera, lidar, IMU, and odom topics are present and have parsed rates.
It does not fill IMU ranges, extrinsics, serial latency, or physical dynamics.

After stopping any node that owns `/dev/osrbot_base`, measure serial query
latency from the `osracer` repo and import it:

```bash
cd /home/osrbot/Desktop/osracer/osracer
tools/serial_latency_probe.py --output /tmp/osracer_serial_latency.json
cd /home/osrbot/Desktop/osracer/osracer_lab
MEASUREMENTS_FILE=docs/real_car_measurements.json \
SERIAL_LATENCY_FILE=/tmp/osracer_serial_latency.json \
  scripts/validate_osracer_lab.sh import-serial-latency
```

`measurement-seed` writes only repo-confirmed facts and collection metadata. It
does not invent mass, steering, speed, IMU range, latency, or extrinsic values.
The seeded baud rate is intentionally not enough to pass the serial latency
measurement gate.

The readiness gate only counts an item as complete when `value` and `source` are
non-empty and `value` matches the template `expected_format`. Keep
`docs/real_car_measurements.json` local if it contains lab notes, serials, or
other non-public details.

Generate a review pack before writing measured values back into source files:

```bash
MEASUREMENTS_FILE=docs/real_car_measurements.json \
  scripts/validate_osracer_lab.sh calibration-review-pack
```

The review pack contains validation results, the calibration plan, a measured
overlay for offline sim/replay, and sim2real readiness gates. Treat it as the
handoff artifact for deciding whether any source write-back is approved.

## Must Measure Before Calibrated Sim2Real

| Area | Parameter | Unit / Format | Suggested method | Current status |
|---|---|---|---|---|
| Mass | Full vehicle mass with battery, Jetson, camera, lidar, wiring | kg | Scale, ready-to-run state | missing |
| Mass | Front/rear weight distribution | kg or percent | Two-scale axle measurement | missing |
| Geometry | Front track | m | Measure tire center to tire center | missing |
| Geometry | Tire width and loaded radius | m | Caliper/tape, car on ground | missing |
| Steering | Servo command min / center / max | firmware units or PWM us | Query firmware or sweep with wheels lifted | missing |
| Steering | True left/right wheel angle at limits | deg or rad | Angle gauge on wheel, compare left/right | missing |
| Steering | Steering zero offset and deadband | deg or rad | Sweep small commands around zero | missing |
| Steering | Step response delay and settling time | s | Record command timestamp plus video/encoder/IMU response | missing |
| Motor / ESC | Motor KV or rated rpm | KV or rpm | Motor datasheet or tachometer | missing |
| Motor / ESC | Battery voltage range and S count | V | Battery label and measured charged/nominal/cutoff voltage | missing |
| Motor / ESC | True max speed | m/s | Straight low-risk run, logged odom/video | missing |
| Motor / ESC | Minimum stable speed | m/s | Increment speed commands on lifted and ground tests | missing |
| Motor / ESC | Throttle deadband and acceleration/brake delay | command units, s | Step command logs with wheel tachometer/odom | missing |
| Encoder / odom | Encoder ticks per revolution and mount location | ticks/rev, frame | Firmware/config/datasheet check | missing |
| IMU | Model | part number | Board BOM or firmware driver source | missing |
| IMU | Sample rate | Hz | Firmware config or measured ROS topic rate | missing |
| IMU | Accel/gyro ranges | g, deg/s or rad/s | Firmware config or datasheet | missing |
| IMU | Magnetometer availability and calibration state | yes/no, notes | ROS topic and firmware command check | missing |
| Timing | Serial command latency | s | Timestamp ROS publish to firmware echo/effect | missing |
| Timing | Sensor timestamp source and clock sync | description | Driver/firmware inspection | missing |
| Extrinsics | `base_link -> camera_link` | xyz rpy, meters/radians | Measure mount or calibrate; resolve URDF vs static TF | conflicting |
| Extrinsics | `base_link -> laser` | xyz rpy, meters/radians | Measure mount or calibrate; resolve URDF vs static TF | conflicting |
| Extrinsics | `base_link -> imu_link` | xyz rpy, meters/radians | Measure mount or calibrate; resolve URDF vs static TF | conflicting |

## Minimum First-Pass Commands

Record real topic rates:

```bash
ros2 topic hz /odometry/filtered
ros2 topic hz /imu_filter
ros2 topic hz /rgb/image_raw
```

Record passive policy observations:

```bash
ros2 launch osracer_bringup policy_observation_recorder.launch.py \
  output_path:=/tmp/osracer_policy_observations.csv \
  rate_hz:=10.0
```

Export the shared hardware parameter JSON after each update:

```bash
python3 scripts/export_hardware_params.py --output /tmp/osracer_hardware_params.json
```

## Update Rule

Only move a value from `missing` or `conflicting` into the simulation control
path after it has a measurement note and a matching repo parameter update.
