# OSRacer Hardware Parameters

This is the current real-vehicle parameter source for sim2sim, sim2real, and Jetson deployment work.

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

## Use In The Pipeline

- IsaacLab: keep high-throughput training on the RTX 4080 SUPER and keep these parameters as the reference for task updates.
- MuJoCo: build the second simulator against the same action contract and hardware parameter source.
- Jetson: deploy only exported TorchScript/ONNX/TensorRT policies; do not train on Jetson.
- Real car: run passive logging and offline replay before enabling closed-loop `/ackermann_cmd`.
