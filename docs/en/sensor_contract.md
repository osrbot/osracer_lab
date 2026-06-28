# Sensor And Observation Contract

This page defines the minimum contract between simulated observations, real ROS topics, and deployable OSRacer policies. The goal is to prevent simulator-only truth from being exported as a real-car policy input.

## Layering Rule

| Layer | Allowed | Forbidden For Real-Car Deployment Policy |
|---|---|---|
| Simulation teacher / reward | World pose, track truth, full state, contact state | Allowed only when marked sim-only |
| Deployment student policy | Camera, LiDAR, IMU, chassis speed, steering/motor state, action history | `root_pos_w`, simulator Euler truth, ideal tire slip, contact truth |
| Safety supervisor | LiDAR nearest distances, local free-space, speed and steering gates | Must not depend on the policy being correct |

## Current Task Contract

| Task | Current use | Deployment status |
|---|---|---|
| `Isaac-OSRacerDriftRL-v0` | Drift / control research baseline | sim-only; blocked from default real-car export |
| `Isaac-OSRacerVisualRL-v0` | Camera + IMU/chassis-history deployment candidate | Candidate only; still requires real replay and safety gates |

Check commands:

```bash
scripts/validate_osracer_lab.sh policy-observation-contract
scripts/validate_osracer_lab.sh policy-observation-contract --task Isaac-OSRacerVisualRL-v0
```

The first command intentionally reports the drift baseline as blocked because it still contains simulator truth. The second command checks the current deployment candidate observation.

## Real ROS Data That Must Match

| Data | Minimum requirement | Current use |
|---|---|---|
| Camera | Topic, `frame_id`, resolution, fps, `CameraInfo`, exposure mode, timestamp source | Visual features / student input |
| LiDAR | Topic, `frame_id`, angular resolution, rate, scan direction, timestamp source | Free-space, occupancy, safety supervisor |
| IMU | Topic, rate, range, frame alignment, filtered orientation availability | Angular velocity, acceleration, stability checks |
| Chassis | Speed, steering target/feedback, motor target/feedback, encoder state | Low-dimensional policy input and replay |
| Command | `/ackermann_cmd` units, limits, watchdog, serial latency | Policy output contract |

## Export Rule

The export script blocks sim-only drift exports by default:

```bash
~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/export_osracer_policy.py \
  --headless \
  --task Isaac-OSRacerVisualRL-v0 \
  --checkpoint logs/rsl_rl/osracer_visual/<run>/model_1999.pt
```

For simulation research artifacts, opt in explicitly:

```bash
~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/export_osracer_policy.py \
  --headless \
  --checkpoint logs/rsl_rl/osracer_drift/<run>/model_1999.pt \
  --allow-sim-only-observations
```

That export is not a real-car closed-loop policy.

## Hard Gates Before Real-Car Use

- `policy-observation-contract --task Isaac-OSRacerVisualRL-v0` passes.
- `runtime-contract` runs against a local `osracer feat-demo` checkout.
- `CameraInfo`, LiDAR/Camera/IMU extrinsics, serial latency, and chassis response delay are recorded.
- Real rosbag replay produces policy inputs with the same shape, units, and ordering.
- The LiDAR safety supervisor is enabled.
