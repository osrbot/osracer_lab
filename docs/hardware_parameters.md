# OSRacer Hardware Parameters

This is the current real-vehicle parameter source for sim2sim, sim2real, and Jetson deployment work.
Use `docs/real_car_measurement_checklist.md` to collect the missing measured values.
Use `docs/extrinsics_alignment.md` to resolve the current camera, lidar, and IMU frame conflict.

## Chassis Parameters

Known simulation and bridge-aligned values:

| Parameter | Value |
|---|---:|
| Wheelbase | `0.285 m` |
| Rear track | `0.235 m` |
| Wheel radius | `0.050 m` |
| Simulation max speed | `3.0 m/s` |
| Simulation max steering | `0.488 rad` |
| Initial real-car speed clamp | `0.3 m/s` |

The steering limit `0.488 rad` is the current simulation action envelope. The ROS bridge clamps at `30 deg`, so keep the learned-policy deployment clamp at or below `0.488 rad` until the real servo range is measured.

## Camera

User-supplied AR0234 camera parameters:

| Parameter | Value |
|---|---|
| Model | `DCXG200` |
| Sensor | `AR0234` |
| Shutter | Global shutter |
| Lens | `2.7 mm`, advertised low-distortion / no-distortion |
| Advertised FOV | `130 deg` |
| Resolution | `1920 x 1200` |
| Pixel size | `3 um x 3 um` |
| Frame rate | `90 / 120 fps` |
| Interface | USB2.0 UVC |
| Format | MJPG / YUY2 |
| Power | about `2 W` |
| Supply | `5 V` |
| Module size | `36 mm x 36 mm` |
| Net weight | `59.9-67.5 g` |

Current ROS camera launch uses `usb_cam` on `/dev/video0`, publishes `/rgb/image_raw`
with `frame_id=camera_link`, and configures `640 x 480 @ 120 fps` using
`mjpeg2rgb`.

Important calibration note: AR0234 sensor size from the pixel pitch is about `5.76 mm x 3.6 mm`. A `2.7 mm` pinhole model from that sensor size does not directly produce a `130 deg` horizontal FOV, so the advertised FOV should be treated as a lens-level or diagonal claim until camera calibration confirms the real intrinsics.

Current IsaacLab visual RL still uses a downsampled pinhole camera approximation. Do not change the trained visual task to `130 deg` until a checkerboard calibration provides `fx`, `fy`, `cx`, `cy`, and distortion coefficients.

## Lidar

User-supplied 25m lidar parameters:

| Parameter | Value |
|---|---|
| Scan principle | Mechanical rotation |
| Ranging principle | Pulse TOF |
| Horizontal FOV | `270 deg` |
| Range | `>=25 m @ 70% reflectivity`, `>=15 m @ 10% reflectivity` |
| Accuracy | `+/-2 cm` |
| Angular resolution | `0.1 deg / 0.25 deg` options |
| Scan rate | `10 / 20 / 25 / 30 Hz` |
| Sample rate | `28.8 / 36 / 43.2 kHz` options |
| Output | Range, angle, intensity, timestamp |
| Transport | UDP/IP and USB |
| Wavelength | `940 nm` |
| Safety | Class 1 |
| Size | `60 mm x 60 mm x 80 mm` |
| Weight | `160 g` |
| Power | `<=2 W` |
| Supply | `9-36 V` |
| Protection | IP65 |

For sim2sim, lidar should be modeled first as a 270-degree planar scan with measured scan rate and angular resolution. Use the real driver timestamps during sim2real replay to catch time alignment issues before closed-loop tests.

## Real Runtime Contract

Values confirmed from the current `osracer` upper-computer code:

| Parameter | Value |
|---|---|
| Chassis launch | `osracer_bringup chassis_ackermann.launch.py` |
| Serial device | `/dev/osrbot_base` |
| Serial baud | `460800` |
| Command protocol | `v <speed_mps> <steering_deg>` |
| Command watchdog | `0.5 s` |
| Ackermann command topic | `/ackermann_cmd` |
| Twist command topic | `/cmd_vel` |
| Runtime odom topic | `/odometry/filtered` |
| Runtime IMU topic | `/imu_filter` |
| Raw magnetometer topic | `/magnetometer_data` |
| RC topic | `/rc_data` |
| IMU serial frame | `i qx qy qz qw ax ay az gx gy gz` |
| Odom serial frame | `o px py pz vx vy vz yaw` |

The bridge accepts `AckermannDrive.steering_angle` in radians, clamps it by
`max_steering_angle_deg=30.0`, then sends steering to firmware in degrees.

## Sensor Extrinsics

There is a current source-of-truth conflict that must be resolved before
calibrated sim2real:

| Transform | URDF value `xyz rpy` | Static TF launch value `xyz rpy` |
|---|---|---|
| `base_link -> camera_link` | `0.12323 -0.017229 -0.053395 -1.5708 0 -1.5708` | `0.30 0 0.075 0 0 0` |
| `base_link -> laser` | `-0.082558 -0.017229 0.034095 -0.00028339 -0.031729 0.0057633` | `0.10 0 0.13 0 0 0` |
| `base_link -> imu_link` | `0.0417958953212156 -0.0177578126845364 -0.063598843109235 0 0 0` | `0.22 0 0.03 0 0 0` |

Use measured physical mounting or a single generated robot description as the
source of truth. Do not calibrate a camera/lidar/IMU sim2real pipeline against
both sets.
Follow `docs/extrinsics_alignment.md` before enabling strict extrinsic checks.

## Still Required

These values are still required before the sim2real model should be considered close to the real car:

| Area | Required values |
|---|---|
| Vehicle mass | Full vehicle mass with battery, Jetson, camera, lidar, and wiring |
| Geometry | Front track, tire width, confirmed wheel radius, sensor mounting positions |
| Weight distribution | Front/rear distribution or approximate component locations |
| Steering | True left/right max steering angle, servo command units, zero point, response time, deadband |
| Motor / ESC | Motor KV or rated rpm, battery voltage, max speed, minimum stable speed, throttle deadband, acceleration/brake delay |
| Encoder / odom | Encoder ticks per revolution, mount location, whether odom is firmware-only or fused upstairs |
| IMU | Model, rate, accel/gyro ranges, magnetometer availability, frame alignment |
| Extrinsics | Camera, lidar, and IMU `xyz + rpy` relative to `base_link` |
| Timing | Serial baud rate, command latency, sensor timestamp source, clock sync method |
| Frame tree | Resolve the URDF vs static TF disagreement for camera, lidar, and IMU |

## Use In The Pipeline

- IsaacLab: keep high-throughput training on the RTX 4080 SUPER and keep these parameters as the reference for task updates.
- MuJoCo: build the second simulator against the same action contract and hardware parameter source.
- Jetson: deploy only exported TorchScript/ONNX/TensorRT policies; do not train on Jetson.
- Real car: run passive logging and offline replay before enabling closed-loop `/ackermann_cmd`.

Check that this parameter source still matches the upper-computer repo:

```bash
python3 scripts/check_runtime_contract.py --osracer-root /home/osrbot/Desktop/osracer/osracer
```

After the camera, lidar, and IMU extrinsics are measured and unified, make the
extrinsic check strict:

```bash
python3 scripts/check_runtime_contract.py \
  --osracer-root /home/osrbot/Desktop/osracer/osracer \
  --strict-extrinsics
```
