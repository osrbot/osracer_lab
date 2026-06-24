# Training And Export

## Drift Training

Start with the drift task because it does not depend on camera tensors.

Smoke test:

```bash
~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/train_osracer_drift.py \
  --headless --num_envs 64 --max_iterations 2
```

Baseline on RTX 4080 SUPER:

```bash
~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/train_osracer_drift.py \
  --headless --num_envs 2048 --max_iterations 2000
```

For larger runs, increase `--num_envs` only after GPU memory and simulation FPS are stable.

## Visual Training

Run visual training only after drift smoke passes:

```bash
~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/train_osracer_drift.py \
  --task Isaac-OSRacerVisualRL-v0 \
  --headless --num_envs 256
```

Use a smaller probe when debugging:

```bash
~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/train_osracer_drift.py \
  --task Isaac-OSRacerVisualRL-v0 \
  --headless --num_envs 64 --max_iterations 2
```

## Resume Training

Use the same task and checkpoint path:

```bash
~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/train_osracer_drift.py \
  --resume --load_run <run_name> --checkpoint <checkpoint>
```

## Export A Policy

TorchScript export:

```bash
~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/export_osracer_policy.py \
  --headless \
  --checkpoint logs/rsl_rl/osracer_drift/<run>/model_1999.pt
```

ONNX export:

```bash
~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/export_osracer_policy.py \
  --headless --format onnx \
  --checkpoint logs/rsl_rl/osracer_drift/<run>/model_1999.pt
```

## Do Not Put It On The Car Immediately

Before real-car closed loop:

```bash
scripts/validate_osracer_lab.sh runtime-contract
scripts/validate_osracer_lab.sh measurement-gap
scripts/validate_osracer_lab.sh sim2real-readiness
```

If measurement gaps remain, use only offline replay or conservative low-speed tests.
