# OSRacer Isaac Lab

Isaac Lab training, sim2sim, and sim2real workflow for OSRacer Ackermann vehicles.

This repository is the training and validation layer. It is designed to work with:

| Layer | Repository | Purpose |
|---|---|---|
| Firmware | [`osrbot/osrcore`](https://github.com/osrbot/osrcore) | ESP32 chassis control, IMU, encoder, serial protocol |
| ROS upper computer | [`osrbot/osracer`](https://github.com/osrbot/osracer/tree/feat-demo) `feat-demo` | Jetson runtime, sensors, policy inference, real-car tools |
| Isaac Lab | [`osrbot/osracer_lab`](https://github.com/osrbot/osracer_lab) | training, export, sim2sim, sim2real checks |

## Documentation

The beginner documentation is built with VitePress:

- Online site target: `https://osrbot.github.io/osracer_lab/`
- Local source: [`docs/index.md`](docs/index.md)
- Start here: [`docs/getting-started.md`](docs/getting-started.md)

Build locally:

```bash
npm install
npm run docs:dev
```

## Quick Start

```bash
mkdir -p ~/osracer_ws
cd ~/osracer_ws
git clone https://github.com/osrbot/osracer_lab.git

cd ~/rlgpu_ws/IsaacLab
./isaaclab.sh -p -m pip install -e ~/osracer_ws/osracer_lab/source/osracer_lab_assets
./isaaclab.sh -p -m pip install -e ~/osracer_ws/osracer_lab/source/osracer_lab_tasks
./isaaclab.sh -p -m pip install -e ~/osracer_ws/osracer_lab/source/osracer_lab_rl

cd ~/osracer_ws/osracer_lab
scripts/validate_osracer_lab.sh static
scripts/validate_osracer_lab.sh source-authority-snapshot
scripts/validate_osracer_lab.sh runtime-contract
```

Smoke test:

```bash
~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/train_osracer_drift.py \
  --headless --num_envs 64 --max_iterations 2
```

## Tasks

| Gym ID | Description |
|---|---|
| `Isaac-OSRacerDriftRL-v0` | Drift RL on a stadium loop, blind observation |
| `Isaac-OSRacerVisualRL-v0` | Visual RL on procedural traversability terrain |

## Recommended Training Baselines

```bash
# Drift baseline on RTX 4080 SUPER
~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/train_osracer_drift.py \
  --headless --num_envs 2048 --max_iterations 2000

# Visual baseline
~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/train_osracer_drift.py \
  --task Isaac-OSRacerVisualRL-v0 --headless --num_envs 256
```

Export a checkpoint:

```bash
~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/export_osracer_policy.py \
  --headless --checkpoint logs/rsl_rl/osracer_drift/<run>/model_1999.pt
```

## Real-Car Runtime Interface

Current runtime interface:

| Item | Value |
|---|---|
| Jetson runtime | JetPack 6.x / Ubuntu 22.04 / ROS 2 Humble |
| Serial device | `/dev/osrbot_base` |
| Serial baud | `460800` |
| Control command | `v <speed_mps> <steering_deg>` |
| Default telemetry | `stream sync`, `s/m/r/b` |
| Sync frame | `s px py pz vx vy vz yaw qx qy qz qw ax ay az gx gy gz` |
| Firmware version | ROS startup queries `fw version` and logs `OSRCORE ProjectVer` |

Do not treat a trained policy as real-car ready until the measurement gaps in
[`docs/real_car_parameter_fill_sheet.md`](docs/real_car_parameter_fill_sheet.md)
are filled and the sim2real readiness checks pass.

## Layout

```text
source/osracer_lab_assets/      Robot URDF, meshes, USD, ArticulationCfg
source/osracer_lab_tasks/       Task environments, MDP modules
source/osracer_lab_rl/          RSL-RL startup helpers
scripts/                        Training, export, validation, sim2real tools
docs/                           VitePress site and reference docs
```

## Validation

```bash
scripts/validate_osracer_lab.sh static
scripts/validate_osracer_lab.sh source-authority-snapshot
scripts/validate_osracer_lab.sh runtime-contract
scripts/validate_osracer_lab.sh measurement-gap
scripts/validate_osracer_lab.sh sim2real-readiness
```
