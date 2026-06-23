"""Train an OSRacer RL policy with RSL-RL.

Usage:
    # Drift task (default)
    ~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/train_osracer_drift.py --headless

    # Visual task
    ~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/train_osracer_drift.py \
        --task Isaac-OSRacerVisualRL-v0 --headless

    # Resume from checkpoint
    ~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/train_osracer_drift.py \
        --resume /path/to/model_1000.pt
"""

from osracer_lab_rl.startup import startup

import argparse

parser = argparse.ArgumentParser(description="Train an OSRacer RL policy.")
parser.add_argument("--task", type=str, default="Isaac-OSRacerDriftRL-v0")
parser.add_argument("--num_envs", type=int, default=None)
parser.add_argument("--max_iterations", type=int, default=None)
parser.add_argument("--resume", type=str, default=None, help="Path to checkpoint to resume from")
parser.add_argument("--log_dir", type=str, default="logs/rsl_rl")
simulation_app, args_cli = startup(parser=parser)

import importlib.metadata as metadata
import os
from datetime import datetime

import gymnasium as gym
import torch

from isaaclab_tasks.utils import get_checkpoint_path, parse_env_cfg
from isaaclab_rl.rsl_rl import RslRlOnPolicyRunnerCfg, RslRlVecEnvWrapper, handle_deprecated_rsl_rl_cfg


def main():
    installed_version = metadata.version("rsl-rl-lib")

    # --- env config ---
    env_cfg = parse_env_cfg(
        args_cli.task,
        device="cuda:0",
        num_envs=args_cli.num_envs,
    )

    env = gym.make(args_cli.task, cfg=env_cfg)
    env = RslRlVecEnvWrapper(env)

    # --- runner config ---
    from isaaclab_tasks.utils import load_cfg_from_registry
    runner_cfg: RslRlOnPolicyRunnerCfg = load_cfg_from_registry(args_cli.task, "rsl_rl_cfg_entry_point")
    if args_cli.max_iterations is not None:
        runner_cfg.max_iterations = args_cli.max_iterations

    # migrate deprecated policy= → actor=/critic= for rsl_rl >= 4.0.0
    runner_cfg = handle_deprecated_rsl_rl_cfg(runner_cfg, installed_version)

    log_dir = os.path.join(
        args_cli.log_dir,
        runner_cfg.experiment_name,
        datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
    )
    os.makedirs(log_dir, exist_ok=True)

    # --- runner ---
    from rsl_rl.runners import OnPolicyRunner

    runner = OnPolicyRunner(env, runner_cfg.to_dict(), log_dir=log_dir, device="cuda:0")

    if args_cli.resume:
        print(f"[INFO] Resuming from: {args_cli.resume}")
        runner.load(args_cli.resume)

    runner.learn(num_learning_iterations=runner_cfg.max_iterations)

    env.close()


if __name__ == "__main__":
    main()
    simulation_app.close()
