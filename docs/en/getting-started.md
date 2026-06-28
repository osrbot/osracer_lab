# Quick Start

This page helps a new user confirm that the repository can run. It is not meant to produce a real-car-ready policy.

## Requirements

| Item | Recommendation |
|---|---|
| Training host | Ubuntu + NVIDIA GPU, currently RTX 4080 SUPER |
| Inference computer | Jetson Orin Nano Super 8G, JetPack 6.x / Ubuntu 22.04 |
| Isaac Sim | Isaac Sim 5.1 recommended |
| Isaac Lab | Latest / main version matching Isaac Sim 5.1 |
| ROS real-car repo | `osrbot/osracer` branch `feat-demo` |
| Firmware repo | `osrbot/osrcore` branch `main` |

::: info
Training runs on the server. Jetson handles inference and real-car sensors. Do not run large Isaac Lab training jobs on Jetson Orin Nano Super 8G.
:::

## 1. Clone The Repository

```bash
mkdir -p ~/osracer_ws
cd ~/osracer_ws
git clone https://github.com/osrbot/osracer_lab.git
cd osracer_lab
```

## 2. Enter The Isaac Lab Environment

Assume Isaac Lab is installed at `~/rlgpu_ws/IsaacLab`:

```bash
cd ~/rlgpu_ws/IsaacLab
./isaaclab.sh -p scripts/environments/list_envs.py
```

If this cannot list Isaac Lab environments, read [Installation](installation.md).

## 3. Install OSRacer Extensions

```bash
cd ~/rlgpu_ws/IsaacLab
./isaaclab.sh -p -m pip install -e ~/osracer_ws/osracer_lab/source/osracer_lab_assets
./isaaclab.sh -p -m pip install -e ~/osracer_ws/osracer_lab/source/osracer_lab_tasks
./isaaclab.sh -p -m pip install -e ~/osracer_ws/osracer_lab/source/osracer_lab_rl
```

## 4. Check Task Registration

```bash
cd ~/rlgpu_ws/IsaacLab
./isaaclab.sh -p scripts/environments/list_envs.py | grep OSRacer
```

Expected tasks:

```text
Isaac-OSRacerDriftRL-v0
Isaac-OSRacerVisualRL-v0
```

## 5. Run Minimal Static Checks

These checks only depend on the `osracer_lab` repository:

```bash
cd ~/osracer_ws/osracer_lab
scripts/validate_osracer_lab.sh static
scripts/validate_osracer_lab.sh sim-sensor-contract
scripts/validate_osracer_lab.sh policy-observation-contract --task Isaac-OSRacerVisualRL-v0
```

They confirm:

- Python files and package layout are valid.
- Simulated camera / LiDAR parameters still come from the hardware parameter source.
- The deployment-candidate observation does not directly use simulator truth.

When a local `osracer feat-demo` checkout is available, run:

```bash
OSRACER_ROOT=/path/to/osracer scripts/validate_osracer_lab.sh runtime-contract
```

If `OSRACER_ROOT` is not set, the check reports the missing upper-computer path instead of printing a Python traceback.

## 6. Run A Drift Smoke Test

```bash
cd ~/osracer_ws/osracer_lab
~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/train_osracer_drift.py \
  --headless --num_envs 64 --max_iterations 2
```

This is a smoke test, not a real training run.

## 7. Next Step

| Goal | Page |
|---|---|
| Install Isaac Sim / Isaac Lab | [Installation](installation.md) |
| Train and export policies | [Training and Export](training.md) |
| Prepare real-car parameters | [Real-Car Parameters](real-car.md) |
| Deploy on Jetson | [Sim2Real / Jetson](sim2real.md) |
