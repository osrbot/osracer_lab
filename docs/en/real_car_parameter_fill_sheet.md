# OSRacer Real-Car Parameter Fill Sheet

Date: 2026-06-24

This document is the single fill-in sheet for aligning `osracer_lab`, `osracer`
`feat-demo`, and `osrcore` before calibrated sim2sim and sim2real work.

## Source Authority

| Area | Current value |
|---|---|
| Firmware | `osrbot/osrcore` `main` |
| Firmware local source read | `/Users/winter/Documents/osracer/osrcore` |
| Firmware HEAD read | `729a6c2` |
| ROS upper computer | `osrbot/osracer` `feat-demo` |
| `feat-demo` HEAD checked | `a901398` |
| IsaacLab repo | `https://github.com/osrbot/osracer_lab` |

## Already Filled Parameters

### Chassis And Simulation

| Parameter | Value | Source / note |
|---|---:|---|
| Wheelbase | `0.285 m` | `feat-demo` chassis launch / lab |
| Rear track | `0.235 m` | current lab parameter |
| IsaacLab wheel radius | `0.050 m` | current lab/URDF model |
| Firmware encoder wheel radius | `0.0425 m` | `osrcore` config |
| Simulation max speed | `3.0 m/s` | current lab training envelope |
| Simulation max steering | `0.488 rad` | current lab training envelope |
| Initial real-car speed clamp | `0.3 m/s` | conservative deployment limit |

Wheel radius is not resolved yet. `osrcore` encoder odometry and `osracer_sim`
use `0.0425 m`; IsaacLab currently uses `0.050 m`. Measure the loaded tire
radius before changing either value.

### Runtime Interface

| Parameter | Value |
|---|---|
| Jetson target OS | `JetPack 6.x / Ubuntu 22.04` |
| ROS runtime | `ROS 2 Humble` |
| Chassis launch | `osracer_bringup chassis_ackermann.launch.py` |
| Serial device | `/dev/osrbot_base` |
| Serial baud | `460800` |
| Command protocol | `v <speed_mps> <steering_deg>` |
| Command watchdog | `0.5 s` |
| Firmware version query timeout | `0.8 s` |
| Firmware version query | `fw version`, logs `OSRCORE ProjectVer` on ROS startup |
| Ackermann command topic | `/ackermann_cmd` |
| Twist command topic | `/cmd_vel` |
| Runtime odom topic | `/odometry/filtered` |
| Runtime IMU topic | `/imu_filter` |
| Raw magnetometer topic | `/magnetometer_data` |
| RC topic | `/rc_data` |
| IMU serial frame | `i qx qy qz qw ax ay az gx gy gz` |
| Odom serial frame | `o px py pz vx vy vz yaw` |

### Firmware Control

| Area | Parameter | Value |
|---|---|---:|
| Encoder | A/B GPIO | `3 / 9` |
| Encoder | PPR | `1024` |
| Encoder | Gear ratio | `10.55` |
| Encoder | Firmware wheel radius | `0.0425 m` |
| Encoder | Speed calculation interval | `20 ms` |
| Encoder | Odom scale default / range | `1.0`, `0.5..1.5` |
| Speed PID | Control interval | `20 ms` |
| Speed PID | `kp / ki / kd` | `425.0 / 8.4 / 20.6` |
| Speed PID | Max integral | `1000.0` |
| Speed PID | Deadband | `0.05 m/s` |
| Speed filter | Speed LPF / odom speed LPF | `0.15 / 0.95` |
| Speed limit | Forward / reverse firmware clamp | `+6.0 / -6.0 m/s` |
| Throttle | Feed-forward deadband default | `90 us` |
| Throttle | Feed-forward deadband range | `0..300 us` |
| Throttle | Feed-forward max | `500 us` |
| PWM | Frequency / resolution | `50 Hz / 14 bit` |
| Throttle PWM | `min / neutral / max` | `1000 / 1500 / 2000 us` |
| Steering PWM | `min / center / max` | `1000 / 1500 / 2000 us` |
| Steering | Max steering | `30 deg` |
| Steering | Trim default / range | `0 deg`, `-5..5 deg` |
| Steering | Reverse | `true` |
| Throttle | Reverse | `false` |
| Safety | Serial timeout | `500 ms` |

### SBUS / RC

| Parameter | Value |
|---|---|
| Protocol | Futaba SBUS |
| Baud / format | `100000`, `8E2 inverted` |
| Frame length | `25` |
| Channel range | `240..1810` |
| CH0 | Steering |
| CH2 | Throttle |
| CH6 | Control mode, `<1500` remote priority, `>=1500` serial control |
| CH7 | Speed mode, `<1500` reduced speed, `>=1500` full speed |
| Reduced speed scale | `15%` |

### IMU / Battery / Telemetry

| Area | Parameter | Value |
|---|---|---|
| IMU | Model / address | `QMI8658`, `0x6B` |
| IMU | Accel range | `+-4 g` |
| IMU | Gyro range | `+-1024 dps` |
| IMU | ODR | `1000 Hz` |
| IMU | Average samples | `5` |
| IMU | Gyro bias samples | `100` |
| IMU heater | Target / warm / stable | `56 C / 38 C / 54 C` |
| IMU heater | Ready timeout | `300000 ms` |
| Battery | Low voltage / recover | `10.8 V / 11.1 V` |
| Battery | Confirm / recover time | `3000 ms / 3000 ms` |
| Telemetry | Sync | `5 ms` |
| Telemetry | Legacy IMU | `5 ms` |
| Telemetry | Legacy odom | `20 ms` |
| Telemetry | Magnetometer | `50 ms` |
| Telemetry | RC | `100 ms` |
| Telemetry | Battery | `2000 ms` |

### Camera

| Parameter | Value |
|---|---|
| Model | `DCXG200` |
| Sensor | `AR0234` |
| Shutter | Global shutter |
| Lens | `2.7 mm`, advertised low/no distortion |
| Advertised FOV | `130 deg` |
| Native resolution | `1920 x 1200` |
| Pixel size | `3 um x 3 um` |
| Frame rate | `90 / 120 fps` |
| Interface | USB2.0 UVC |
| Format | MJPG / YUY2 |
| Power / supply | about `2 W`, `5 V` |
| Module size | `36 mm x 36 mm` |
| Net weight | `59.9-67.5 g` |
| ROS driver | `usb_cam` |
| ROS device | `/dev/video0` |
| ROS frame | `camera_link` |
| ROS topic | `/rgb/image_raw` |
| Runtime resolution | `640 x 480` |
| Runtime fps | `120` |
| Runtime pixel format | `mjpeg2rgb` |

Camera calibration still needs to be measured at the deployed runtime
resolution. Do not use the advertised `130 deg` as calibrated intrinsics.

### Lidar

| Parameter | Value |
|---|---|
| Scan principle | Mechanical rotation |
| Ranging principle | Pulse TOF |
| Horizontal FOV | `270 deg` |
| Range | `>=25 m @ 70% reflectivity`, `>=15 m @ 10% reflectivity` |
| Accuracy | `+-2 cm` |
| Angular resolution | `0.1 deg / 0.25 deg` |
| Scan rate | `10 / 20 / 25 / 30 Hz` |
| Sample rate | `28.8 / 36 / 43.2 kHz` |
| Output | Range, angle, intensity, timestamp |
| Transport | UDP/IP and USB |
| Wavelength | `940 nm` |
| Safety | Class 1 |
| Size | `60 mm x 60 mm x 80 mm` |
| Weight | `160 g` |
| Power | `<=2 W` |
| Supply | `9-36 V` |
| Protection | IP65 |
| ROS frame | `laser` |
| Conservative lab scan model | `270 deg`, `0.25 deg`, `10 Hz`, `25 m`, `1081` rays |

### Current Sensor Extrinsics To Resolve

These values currently disagree between URDF and static TF. Fill the measured
values below and then choose one source of truth.

| Transform | URDF value `xyz rpy` | Static TF value `xyz rpy` |
|---|---|---|
| `base_link -> camera_link` | `0.12323 -0.017229 -0.053395 -1.5708 0 -1.5708` | `0.30 0 0.075 0 0 0` |
| `base_link -> laser` | `-0.082558 -0.017229 0.034095 0 0 0` | `0.10 0 0.13 0 0 0` |
| `base_link -> imu_link` | `0.0417958953212156 -0.0177578126845364 -0.063598843109235 0 0 0` | `0.22 0 0.03 0 0 0` |

## Parameters To Fill

Fill values in SI units where possible. Add evidence paths or notes whenever a
value comes from a measurement session, datasheet, photo, video, or ROS bag.

### Vehicle Mass / Geometry

| Parameter | Fill value | Method / evidence |
|---|---|---|
| Full vehicle mass with battery, Jetson, sensors, wiring |  |  |
| Front axle weight |  |  |
| Rear axle weight |  |  |
| Front/rear weight distribution |  |  |
| Front track, tire center to tire center |  |  |
| Rear track, tire center to tire center |  |  |
| Tire width |  |  |
| Loaded tire radius |  |  |
| Loaded tire diameter |  |  |
| Tire material / compound |  |  |
| Typical test ground surface |  |  |

### Steering

| Parameter | Fill value | Method / evidence |
|---|---|---|
| True max steering left |  |  |
| True max steering right |  |  |
| Steering zero point offset |  |  |
| Servo command units confirmed |  |  |
| Steering deadband |  |  |
| Steering response time |  |  |
| Steering settle time |  |  |
| Steering asymmetry or mechanical limit note |  |  |

### Motor / ESC / Battery

| Parameter | Fill value | Method / evidence |
|---|---|---|
| Motor KV or rated RPM |  |  |
| Motor model |  |  |
| ESC model |  |  |
| ESC mode, brake, reverse behavior |  |  |
| Battery S count |  |  |
| Battery full voltage |  |  |
| Battery nominal voltage |  |  |
| Battery cutoff / safe minimum voltage |  |  |
| True max speed on ground |  |  |
| Minimum stable speed on ground |  |  |
| Throttle deadband |  |  |
| Throttle response delay |  |  |
| Brake / deceleration response delay |  |  |

### Encoder / Odometry

| Parameter | Fill value | Method / evidence |
|---|---|---|
| Encoder ticks per revolution confirmed |  |  |
| Encoder physical mount location |  |  |
| Encoder before/after gearbox |  |  |
| Effective ticks per wheel revolution |  |  |
| Measured odom scale correction |  |  |
| Odom drift over straight-line test |  |  |
| Odom drift over turn test |  |  |

### IMU

| Parameter | Fill value | Method / evidence |
|---|---|---|
| IMU model confirmed | `QMI8658` |  |
| ROS publish rate observed |  |  |
| Accel range confirmed | `+-4 g` |  |
| Gyro range confirmed | `+-1024 dps` |  |
| Magnetometer available / used |  |  |
| IMU physical frame alignment to `base_link` |  |  |
| IMU temperature at steady state |  |  |
| Bias convergence time |  |  |
| Static yaw drift over 5 min |  |  |

### Camera Calibration

| Parameter | Fill value | Method / evidence |
|---|---|---|
| Calibration resolution |  |  |
| Calibration fps |  |  |
| `fx` |  |  |
| `fy` |  |  |
| `cx` |  |  |
| `cy` |  |  |
| Distortion model |  |  |
| Distortion coefficients |  |  |
| Calibration reprojection error |  |  |
| Calibration file path |  |  |

### Sensor Extrinsics

Use `base_link` as the parent frame. Units: meters and radians.

| Transform | `x` | `y` | `z` | `roll` | `pitch` | `yaw` | Method / evidence |
|---|---:|---:|---:|---:|---:|---:|---|
| `base_link -> camera_link` |  |  |  |  |  |  |  |
| `base_link -> laser` |  |  |  |  |  |  |  |
| `base_link -> imu_link` |  |  |  |  |  |  |  |

Chosen source of truth after measurement:

```text
URDF / static TF / generated robot description:
Reason:
Files to update:
```

### Timing / Latency / Sync

| Parameter | Fill value | Method / evidence |
|---|---|---|
| Serial command latency |  |  |
| Serial round-trip latency |  |  |
| Camera timestamp source |  |  |
| Lidar timestamp source |  |  |
| IMU timestamp source |  |  |
| Clock sync method |  |  |
| ROS bag / measurement session path |  |  |

## Minimum Fill Set Before Next Calibration Step

Fill these first:

| Priority | Parameter |
|---:|---|
| 1 | Full vehicle mass |
| 2 | Front/rear weight distribution |
| 3 | Front track |
| 4 | Loaded tire radius |
| 5 | True left/right max steering angle |
| 6 | Steering response time |
| 7 | Battery S count and voltage limits |
| 8 | True max speed and minimum stable speed |
| 9 | Camera intrinsics at runtime resolution |
| 10 | Camera/lidar/IMU measured extrinsics |
| 11 | Serial command latency |
| 12 | Sensor timestamp sync method |
