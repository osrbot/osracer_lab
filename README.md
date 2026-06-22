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

## Design notes

- `root_link_name="base_link"` — URDF root is `base_footprint` (no inertia); must be explicit.
- `merge_fixed_joints=True` — camera/laser/imu links merged into `base_link`, avoids zero-inertia bodies.
- `joint_drive=None` — URDF drive disabled; actuator properties owned by `DCMotorCfg` / `ImplicitActuatorCfg`.
- Separate USD cache dirs (`usd/blind/` vs `usd/visual/`) prevent USD collision on dual-config load.
- All WheeledLab MDP utilities are inlined under `osracer_lab_tasks/mdp/` — no `wheeledlab*` runtime dependency.
