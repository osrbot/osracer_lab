# Installation

## Recommended Layout

```text
~/rlgpu_ws/IsaacSim      Isaac Sim
~/rlgpu_ws/IsaacLab      Isaac Lab
~/osracer_ws/osracer_lab This repository
```

## 1. NVIDIA Driver

Use a recent NVIDIA driver compatible with Isaac Sim 5.1. On the current development host, Isaac Sim 5.1 headless camera tasks were verified with NVIDIA driver `580.159.03`.

If camera tasks crash around `librtx.scenedb.plugin`, check Vulkan and the NVIDIA driver before changing training code.

## 2. Install Isaac Sim 5.1

Install the prebuilt Isaac Sim 5.1 package from NVIDIA.

Example layout:

```bash
mkdir -p ~/rlgpu_ws
cd ~/rlgpu_ws
unzip ~/Downloads/isaac-sim-standalone-5.1.0-linux-x86_64.zip -d IsaacSim
```

## 3. Install Isaac Lab

```bash
cd ~/rlgpu_ws
git clone https://github.com/isaac-sim/IsaacLab.git
cd IsaacLab
ln -s ../IsaacSim _isaac_sim
./isaaclab.sh --install
```

Check the environment list:

```bash
./isaaclab.sh -p scripts/environments/list_envs.py
```

## 4. Install This Repository

```bash
mkdir -p ~/osracer_ws
cd ~/osracer_ws
git clone https://github.com/osrbot/osracer_lab.git

cd ~/rlgpu_ws/IsaacLab
./isaaclab.sh -p -m pip install -e ~/osracer_ws/osracer_lab/source/osracer_lab_assets
./isaaclab.sh -p -m pip install -e ~/osracer_ws/osracer_lab/source/osracer_lab_tasks
./isaaclab.sh -p -m pip install -e ~/osracer_ws/osracer_lab/source/osracer_lab_rl
```

## 5. Headless Camera Check

```bash
cd ~/rlgpu_ws/IsaacLab
./isaaclab.sh -p scripts/environments/list_envs.py | grep OSRacer
```

Then run a short visual smoke test after drift smoke works:

```bash
cd ~/osracer_ws/osracer_lab
~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/train_osracer_drift.py \
  --task Isaac-OSRacerVisualRL-v0 \
  --headless --num_envs 64 --max_iterations 2
```

## 6. Common Setup Checks

| Symptom | First check |
|---|---|
| OSRacer tasks are missing | Editable installs for all three `source/*` packages |
| Camera task crashes | NVIDIA driver, Vulkan, Isaac Sim 5.1 |
| Import errors | Run through `~/rlgpu_ws/IsaacLab/isaaclab.sh -p` |
| Slow visual training | Reduce `--num_envs`, then tune after smoke tests pass |
