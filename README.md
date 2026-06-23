# osracer_lab

IsaacLab RL simulation framework for OSRacer — **fully self-contained**, no WheeledLab runtime dependency.

## Layout

```text
source/osracer_lab_assets/      Robot URDF, meshes, USD, ArticulationCfg
source/osracer_lab_tasks/       Task environments (drift + visual), MDP modules
  osracer_lab_tasks/
    common/                     BlindObsCfg, OSRacerAckermannActionCfg
    mdp/                        Ackermann actions, curriculum, observations (inlined)
    drifting/                   OSRacerDriftRLEnvCfg + mdp/events
    visual/                     OSRacerVisualRLEnvCfg + mdp/events + utils
source/osracer_lab_rl/          RSL-RL startup helpers
scripts/                        train_osracer_drift.py
```

## Tasks

| Gym ID | Description |
|---|---|
| `Isaac-OSRacerDriftRL-v0` | Drift RL on a stadium loop (blind) |
| `Isaac-OSRacerVisualRL-v0` | Visual RL on procedural traversability terrain |

## Running

```bash
# Drift (headless)
~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/train_osracer_drift.py --headless

# Drift training baseline on RTX 4080 SUPER
~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/train_osracer_drift.py \
    --headless --num_envs 2048 --max_iterations 2000

# Visual RL
~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/train_osracer_drift.py \
    --task Isaac-OSRacerVisualRL-v0 --headless

# Visual RL higher-throughput probe on RTX 4080 SUPER
~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/train_osracer_drift.py \
    --task Isaac-OSRacerVisualRL-v0 --headless --num_envs 512

# Reproducible validation wrapper
scripts/validate_osracer_lab.sh static
scripts/validate_osracer_lab.sh drift-smoke
scripts/validate_osracer_lab.sh visual-smoke
scripts/validate_osracer_lab.sh visual-perf

# Resume from checkpoint
~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/train_osracer_drift.py \
    --resume logs/rsl_rl/osracer_drift/model_1000.pt

# Export checkpoint for deployment
~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/export_osracer_policy.py \
    --headless --checkpoint logs/rsl_rl/osracer_drift/2026-06-23_17-05-26/model_1999.pt

# Optional ONNX export
~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/export_osracer_policy.py \
    --headless --format onnx --checkpoint logs/rsl_rl/osracer_drift/2026-06-23_17-05-26/model_1999.pt
```

## Installation

```bash
cd source/osracer_lab_assets  && pip install -e .
cd source/osracer_lab_tasks   && pip install -e .
cd source/osracer_lab_rl      && pip install -e .
```

## Deployment Contract

See `docs/deployment.md` for the current policy-to-vehicle contract.
The simulation action is `[target_speed_mps, target_steering_rad]`; the preferred real-vehicle bridge is `ackermann_msgs/msg/AckermannDrive` on `ackermann_cmd`.
The sibling OSRacer ROS 2 workspace converts that to the firmware serial command `v <speed_mps> <steering_deg>`.
Use `scripts/export_osracer_policy.py` to export trained checkpoints to TorchScript before building a ROS 2 inference node; ONNX export is available with `--format onnx`.

## Performance Baseline

On the RTX 4080 SUPER dev host, drift training is verified with `--num_envs 2048 --max_iterations 2000`.
This run finished successfully and wrote `model_1999.pt`, with about 75k-80k steps/s near the end and no non-finite state resets.

Short probes:

| num_envs | Result |
|---:|---|
| 1024 | Stable, about 61k steps/s, underutilizes the GPU |
| 2048 | Recommended drift baseline, about 75k-92k steps/s |
| 4096 | Runs, but throughput fluctuates and can drop near 50k-63k steps/s |
| 8192 | Runs, but initialization and PhysX/CPU synchronization dominate; not recommended by default |

Visual RL camera rendering is heavier than drift, but still leaves headroom on the RTX 4080 SUPER.
The default `--num_envs 256` is the conservative training baseline: a 50-iteration validation run finished with `model_49.pt`, about 2.0k-2.1k steps/s, and about 7.1 GB VRAM.
For higher GPU utilization, `--num_envs 512` completed a 10-iteration probe with `model_9.pt`, about 2.9k steps/s, and about 8.5 GB VRAM.
The visual task includes finite observation wrappers and a non-finite root-state termination guard so rare unstable physics states reset before they reach RSL-RL as NaN observations.

## Headless Rendering

Visual RL requires IsaacLab cameras, so `scripts/train_osracer_drift.py` enables cameras automatically for `Isaac-OSRacerVisualRL-v0`. If the app crashes before task creation in `omni.kit.widget.viewport` / `librtx.scenedb.plugin`, first check the host Vulkan and NVIDIA driver stack:

```bash
nvidia-smi
find /usr/share/vulkan /etc/vulkan -name '*nvidia*icd*.json*' -o -name '*nvidia*.json*'
```

On the RTX 4080 SUPER dev host, Isaac Sim 5.1 camera startup is verified with NVIDIA driver `580.159.03`. The Ubuntu `595.71.05` open and non-open drivers both crashed in `librtx.scenedb.plugin` before task creation.

Minimal camera check:

```bash
~/rlgpu_ws/IsaacLab/isaaclab.sh -p -c 'from isaaclab.app import AppLauncher; app=AppLauncher(headless=True, enable_cameras=True).app; print("APP_HEADLESS_CAMERA_OK"); app.close()'
```

The drift task does not need cameras and should run with plain `--headless`.

## Design notes

- `root_link_name=None` — `merge_fixed_joints=True` merges `base_link` into the effective `base_footprint` root.
- `merge_fixed_joints=True` — camera/laser/imu links merge into `base_footprint`, avoiding zero-inertia bodies.
- `joint_drive=None` — URDF drive disabled; actuator properties owned by `DCMotorCfg` / `ImplicitActuatorCfg`.
- Separate USD cache dirs (`usd/blind/` vs `usd/visual/`) prevent USD collision on dual-config load.
- All WheeledLab MDP utilities are inlined under `osracer_lab_tasks/mdp/` — no `wheeledlab*` runtime dependency.
