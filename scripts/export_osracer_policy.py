"""Export an OSRacer RSL-RL checkpoint to deployment formats.

Example:
    ~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/export_osracer_policy.py \
        --headless \
        --checkpoint logs/rsl_rl/osracer_drift/2026-06-23_17-05-26/model_1999.pt
"""

from osracer_lab_rl.startup import startup

import argparse

parser = argparse.ArgumentParser(description="Export an OSRacer RSL-RL policy.")
parser.add_argument("--task", type=str, default="Isaac-OSRacerDriftRL-v0")
parser.add_argument("--checkpoint", type=str, default=None, help="Path to the RSL-RL checkpoint")
parser.add_argument("--output_dir", type=str, default=None, help="Defaults to <checkpoint_dir>/exported")
parser.add_argument("--num_envs", type=int, default=1, help="Small env count used to build the runner")
parser.add_argument(
    "--format",
    choices=("jit", "onnx", "both"),
    default="jit",
    help="Export format. ONNX can be slow on some Isaac/RSL-RL stacks, so JIT is the default.",
)
parser.add_argument("--jit_filename", type=str, default="policy.pt")
parser.add_argument("--onnx_filename", type=str, default="policy.onnx")
parser.add_argument("--log_dir", type=str, default="logs/rsl_rl")
simulation_app, args_cli = startup(parser=parser)

import importlib.metadata as metadata
import os

import gymnasium as gym
import torch

from isaaclab_tasks.utils import parse_env_cfg
from isaaclab_rl.rsl_rl import RslRlOnPolicyRunnerCfg, RslRlVecEnvWrapper, handle_deprecated_rsl_rl_cfg


def _export_jit(runner, path: str, obs: torch.Tensor) -> tuple[int, ...]:
    policy = runner.alg.get_policy().as_jit().to("cpu")
    policy.eval()
    obs_cpu = obs.detach().cpu()
    traced_model = torch.jit.trace(policy, obs_cpu)
    traced_model.save(path)
    with torch.inference_mode():
        actions = traced_model(obs_cpu)
    return tuple(actions.shape)


def _validate_jit(path: str, obs: torch.Tensor) -> tuple[int, ...]:
    model = torch.jit.load(path, map_location="cpu")
    model.eval()
    with torch.inference_mode():
        actions = model(obs.detach().cpu())
    return tuple(actions.shape)


def _validate_onnx(path: str) -> None:
    import onnx

    onnx.checker.check_model(onnx.load(path))


def _policy_obs(obs) -> torch.Tensor:
    if isinstance(obs, torch.Tensor):
        return obs
    if "policy" in obs:
        return obs["policy"]
    raise KeyError("Expected a 'policy' observation group for export")


def main():
    if args_cli.checkpoint is None:
        raise ValueError("--checkpoint is required")

    installed_version = metadata.version("rsl-rl-lib")
    checkpoint = os.path.abspath(args_cli.checkpoint)
    output_dir = args_cli.output_dir or os.path.join(os.path.dirname(checkpoint), "exported")
    output_dir = os.path.abspath(output_dir)

    env_cfg = parse_env_cfg(
        args_cli.task,
        device="cuda:0",
        num_envs=args_cli.num_envs,
    )
    env = gym.make(args_cli.task, cfg=env_cfg)
    env = RslRlVecEnvWrapper(env)

    from isaaclab_tasks.utils import load_cfg_from_registry
    from rsl_rl.runners import OnPolicyRunner

    runner_cfg: RslRlOnPolicyRunnerCfg = load_cfg_from_registry(args_cli.task, "rsl_rl_cfg_entry_point")
    runner_cfg = handle_deprecated_rsl_rl_cfg(runner_cfg, installed_version)

    runner = OnPolicyRunner(env, runner_cfg.to_dict(), log_dir=None, device="cuda:0")
    print(f"[INFO] Loading checkpoint: {checkpoint}", flush=True)
    runner.load(checkpoint, map_location="cuda:0")

    os.makedirs(output_dir, exist_ok=True)
    obs = _policy_obs(env.get_observations())
    print(f"[INFO] Observation shape: {tuple(obs.shape)}", flush=True)

    exported_paths: list[str] = []
    if args_cli.format in ("jit", "both"):
        jit_path = os.path.join(output_dir, args_cli.jit_filename)
        print(f"[INFO] Exporting JIT policy: {jit_path}", flush=True)
        action_shape = _export_jit(runner, jit_path, obs)
        action_shape = _validate_jit(jit_path, obs)
        exported_paths.append(jit_path)
        print(f"[INFO] JIT export OK: {jit_path} action_shape={action_shape}", flush=True)

    if args_cli.format in ("onnx", "both"):
        runner.export_policy_to_onnx(path=output_dir, filename=args_cli.onnx_filename)
        onnx_path = os.path.join(output_dir, args_cli.onnx_filename)
        _validate_onnx(onnx_path)
        exported_paths.append(onnx_path)
        print(f"[INFO] ONNX export OK: {onnx_path}", flush=True)

    env.close()

    print("[INFO] Exported files:", flush=True)
    for path in exported_paths:
        print(f"  {path} ({os.path.getsize(path)} bytes)", flush=True)


if __name__ == "__main__":
    try:
        main()
    finally:
        simulation_app.close()
