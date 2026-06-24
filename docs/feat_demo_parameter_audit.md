# OSRacer feat-demo Parameter Audit

Date: 2026-06-24

Authority checked:

- Mac `feat-demo`: `/Users/winter/.codex/worktrees/904a/osracer` at `7b92682`
- Server `feat-demo` mirror: `/home/osrbot/Desktop/osracer/osracer` at `7b92682`
- Firmware authority snapshot source: local read-only `osrcore` at `9742339`
- Isaac/tooling repo: `/home/osrbot/Desktop/osracer/osracer_lab`

## Matched Runtime Parameters

| Item | `osracer feat-demo` | `osracer_lab` |
|---|---|---|
| ROS runtime | Humble | `real_runtime.ros_distro=humble` |
| Jetson OS target | JetPack 6.x / Ubuntu 22.04 | `real_runtime.jetson_os=JetPack 6.x / Ubuntu 22.04` |
| Serial device | `/dev/osrbot_base` | `/dev/osrbot_base` |
| Serial baud | `460800` | `460800` |
| Command protocol | `v <speed_mps> <steering_deg>` | same |
| Command watchdog | `0.5 s` | `0.5 s` |
| Wheelbase | `0.285 m` | `0.285 m` |
| Bridge steering clamp | `30 deg` | `30 deg` |
| Policy steering envelope | `0.488 rad` | `0.488 rad` |
| Initial real speed cap | `0.3 m/s` | `0.3 m/s` |
| Ackermann topic | `/ackermann_cmd` | `/ackermann_cmd` |
| CmdVel topic | `/cmd_vel` | `/cmd_vel` |
| Odom topic | `/odometry/filtered` | `/odometry/filtered` |
| IMU topic | `/imu_filter` | `/imu_filter` |
| Camera runtime | `/dev/video0`, `640x480`, `120 fps`, `mjpeg2rgb`, `camera_link` | same |
| Lidar runtime frame/topic | `laser`, `/scan` | same |

## Sensor Spec Coverage

| Sensor | Covered in lab | Notes |
|---|---|---|
| AR0234 camera | model `DCXG200`, global shutter, `1920x1200`, `2.7 mm`, advertised `130 deg`, UVC, MJPG/YUY2, runtime `640x480@120` | Calibration still required at deployed resolution. |
| 25m lidar | `270 deg`, `0.1/0.25 deg`, `10/20/25/30 Hz`, `25 m @ 70%`, `15 m @ 10%`, Class 1, IP65 | Lab conservative scan model uses `0.25 deg`, `10 Hz`, `25 m`, `1081` rays. |
| Chassis/firmware | `SERIAL_TIMEOUT=500 ms`, steering PWM `1000/1500/2000`, trim `0 deg`, encoder `1024 PPR`, gear ratio `10.55`, firmware wheel radius `0.0425 m`, PID `425.0/8.4/20.6`, QMI8658 IMU | Snapshot derived from `osrcore`. |

## Known Mismatches

- `osracer_sim` kinematic simulator and `osrcore` encoder odometry use `wheel_radius=0.0425 m`; `osracer_sim` also uses `track_width=0.215 m`.
- `osracer_lab` chassis parameters use `rear_track_m=0.235 m` and `wheel_radius_m=0.050 m` for the current Isaac/URDF model.
- This is not a source-code conflict yet because the kinematic simulator is a lightweight ROS sim, but it should not be treated as calibrated sim2real until real measurements choose the authoritative values.
- Sensor extrinsics still conflict between URDF and static TF:
  - `base_link -> camera_link`
  - `base_link -> laser`
  - `base_link -> imu_link`

## Information Still Needed

These items are still required before calibrated closed-loop sim2real:

1. Full vehicle mass with battery, Jetson, camera, lidar, and wiring.
2. Front/rear weight distribution.
3. Front track and tire width.
4. Confirmed loaded wheel radius or tire diameter.
5. True left/right max steering angles.
6. Steering zero point, command units, deadband, and response time.
7. Motor KV or rated RPM.
8. Battery S count, charged/nominal/cutoff voltage.
9. True max speed and minimum stable speed on ground.
10. Throttle deadband and response delay.
11. Encoder ticks per revolution and mount location.
12. IMU physical frame alignment and measured timing. Firmware reports QMI8658, 1000 Hz ODR, +-4 g accel, +-1024 dps gyro.
13. Camera calibration at runtime resolution: `fx`, `fy`, `cx`, `cy`, distortion model, coefficients.
14. Measured camera/lidar/IMU extrinsics in `base_link`.
15. Serial command latency report from the actual firmware.
16. Sensor timestamp source and clock sync method.

## Verification Commands

```bash
scripts/validate_osracer_lab.sh source-authority-snapshot
scripts/validate_osracer_lab.sh runtime-contract
scripts/validate_osracer_lab.sh measurement-consistency
MEASUREMENTS_FILE=docs/real_car_measurements.template.json scripts/validate_osracer_lab.sh measurement-gap
```
