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

# Visual RL
~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/train_osracer_drift.py \
    --task Isaac-OSRacerVisualRL-v0 --headless

# Resume from checkpoint
~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/train_osracer_drift.py \
    --resume logs/rsl_rl/osracer_drift/model_1000.pt
```

## Installation

```bash
cd source/osracer_lab_assets  && pip install -e .
cd source/osracer_lab_tasks   && pip install -e .
cd source/osracer_lab_rl      && pip install -e .
```

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
