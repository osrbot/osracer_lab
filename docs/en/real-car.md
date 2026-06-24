# Real-Car Parameters

## Confirmed Software Interfaces

| Item | Value |
|---|---|
| Firmware repo | `osrbot/osrcore` `main` |
| ROS upper computer | `osrbot/osracer` `feat-demo` |
| Serial device | `/dev/osrbot_base` |
| Serial baud | `460800` |
| Command | `v <speed_mps> <steering_deg>` |
| Ackermann topic | `/ackermann_cmd` |
| Initial real-car speed limit | `0.3 m/s` |

## Confirmed Firmware Parameters

| Item | Value |
|---|---:|
| Encoder PPR | `1024` |
| Gear ratio | `10.55` |
| Firmware wheel radius | `0.0425 m` |
| Firmware max steering | `30 deg` |
| Serial command timeout | `500 ms` |

## Must Measure

| Priority | Parameter | Why |
|---:|---|---|
| 1 | Loaded wheel radius | Resolve the `0.050 m` vs `0.0425 m` conflict |
| 2 | Left/right max steering | Match simulation and real servo limits |
| 3 | Steering zero and deadband | Avoid biased real-car control |
| 4 | Vehicle mass | Improve dynamics and replay assumptions |
| 5 | Camera intrinsics | Required for visual sim2real |
| 6 | Sensor extrinsics | Required for camera/lidar/IMU fusion |
| 7 | Serial latency | Required for timing and watchdog tuning |

## Wheel Radius Conflict

| Source | Current value |
|---|---:|
| `osrcore` firmware encoder model | `0.0425 m` |
| `osracer_sim` | `0.0425 m` |
| `osracer_lab` Isaac / URDF model | `0.050 m` |

Do not pick one blindly. Measure the loaded wheel radius and decide whether encoder odometry and collision geometry should use the same value.

## Extrinsics Conflict

URDF and static TF currently disagree for camera, lidar, and IMU mounting. Resolve this before calibrated visual or lidar sim2real work. See [Extrinsics Alignment](extrinsics_alignment.md).
