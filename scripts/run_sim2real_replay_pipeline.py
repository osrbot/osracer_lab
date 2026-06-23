#!/usr/bin/env python3
"""Run the offline sim2real replay chain.

Input:
  recorded observation CSV from osracer_bringup policy_observation_recorder.py

Output:
  policy_replay.csv with speed_cmd / steering_cmd
  mujoco_replay.xml plus MuJoCo kinematic replay metrics
"""

import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path


def default_policy_runner():
    env_value = os.environ.get("OSRACER_POLICY_RUNNER")
    if env_value:
        return env_value
    isaaclab = Path("/home/osrbot/rlgpu_ws/IsaacLab/isaaclab.sh")
    if isaaclab.exists():
        return f"{isaaclab} -p"
    return sys.executable


def default_mujoco_python():
    return os.environ.get("OSRACER_MUJOCO_PYTHON", sys.executable)


def default_summary_runner():
    return os.environ.get("OSRACER_SUMMARY_RUNNER", sys.executable)


def parse_args():
    parser = argparse.ArgumentParser(description="Run OSRacer observation CSV through policy replay and MuJoCo replay.")
    parser.add_argument("--observations", required=True, help="Recorded observation CSV")
    parser.add_argument("--policy", required=True, help="TorchScript policy.pt")
    parser.add_argument("--output-dir", default="/tmp/osracer_sim2real_replay")
    parser.add_argument("--osracer-ws", default=None, help="Sibling OSRacer ROS workspace")
    parser.add_argument("--policy-runner", default=default_policy_runner(), help="Command prefix used to run policy_replay_csv.py")
    parser.add_argument("--summary-runner", default=default_summary_runner(), help="Command prefix used to run policy_replay_summary.py")
    parser.add_argument("--mujoco-python", default=default_mujoco_python(), help="Python executable with mujoco installed")
    parser.add_argument("--max-speed-mps", type=float, default=0.3)
    parser.add_argument("--max-steering-rad", type=float, default=0.488)
    parser.add_argument("--steps-per-action", type=int, default=1)
    parser.add_argument("--measured-overlay", default=None, help="Measured overlay JSON passed to MuJoCo replay")
    parser.add_argument("--skip-summary", action="store_true", help="Skip policy replay summary gate")
    parser.add_argument("--min-rows", type=int, default=1)
    parser.add_argument("--max-clamped-ratio", type=float, default=None)
    parser.add_argument("--max-abs-raw-speed", type=float, default=None)
    parser.add_argument("--max-abs-raw-steering", type=float, default=None)
    return parser.parse_args()


def run_command(command, env=None):
    print("+ " + " ".join(shlex.quote(str(part)) for part in command), flush=True)
    subprocess.run(command, check=True, env=env)


def main():
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    osracer_ws = Path(args.osracer_ws).resolve() if args.osracer_ws else repo_root.parent / "osracer"
    policy_replay = osracer_ws / "tools" / "policy_replay_csv.py"
    policy_summary = osracer_ws / "tools" / "policy_replay_summary.py"
    mujoco_replay = repo_root / "scripts" / "mujoco_sim2sim_smoke.py"

    observations = Path(args.observations).resolve()
    policy = Path(args.policy).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if not observations.exists():
        raise FileNotFoundError(f"observations CSV does not exist: {observations}")
    if not policy.exists():
        raise FileNotFoundError(f"policy does not exist: {policy}")
    if not policy_replay.exists():
        raise FileNotFoundError(f"policy replay tool does not exist: {policy_replay}")
    if not args.skip_summary and not policy_summary.exists():
        raise FileNotFoundError(f"policy replay summary tool does not exist: {policy_summary}")
    if not mujoco_replay.exists():
        raise FileNotFoundError(f"MuJoCo replay tool does not exist: {mujoco_replay}")
    if args.steps_per_action <= 0:
        raise ValueError("--steps-per-action must be > 0")

    policy_out = output_dir / "policy_replay.csv"
    mujoco_xml = output_dir / "mujoco_replay.xml"

    policy_command = shlex.split(args.policy_runner) + [
        str(policy_replay),
        "--policy",
        str(policy),
        "--input",
        str(observations),
        "--output",
        str(policy_out),
        "--max-speed-mps",
        str(args.max_speed_mps),
        "--max-steering-rad",
        str(args.max_steering_rad),
    ]
    run_command(policy_command)

    if not args.skip_summary:
        summary_command = shlex.split(args.summary_runner) + [
            str(policy_summary),
            str(policy_out),
            "--min-rows",
            str(args.min_rows),
            "--max-speed-cmd",
            str(args.max_speed_mps),
            "--max-abs-steering-cmd",
            str(args.max_steering_rad),
        ]
        if args.max_clamped_ratio is not None:
            summary_command.extend(["--max-clamped-ratio", str(args.max_clamped_ratio)])
        if args.max_abs_raw_speed is not None:
            summary_command.extend(["--max-abs-raw-speed", str(args.max_abs_raw_speed)])
        if args.max_abs_raw_steering is not None:
            summary_command.extend(["--max-abs-raw-steering", str(args.max_abs_raw_steering)])
        run_command(summary_command)

    mujoco_env = os.environ.copy()
    assets_path = str(repo_root / "source" / "osracer_lab_assets")
    existing_pythonpath = mujoco_env.get("PYTHONPATH")
    mujoco_env["PYTHONPATH"] = assets_path if not existing_pythonpath else f"{assets_path}:{existing_pythonpath}"
    mujoco_command = [
        args.mujoco_python,
        str(mujoco_replay),
        "--xml-out",
        str(mujoco_xml),
        "--actions-csv",
        str(policy_out),
        "--steps-per-action",
        str(args.steps_per_action),
    ]
    if args.measured_overlay:
        mujoco_command.extend(["--measured-overlay", str(Path(args.measured_overlay).resolve())])
    run_command(mujoco_command, env=mujoco_env)

    print(f"policy_replay={policy_out}", flush=True)
    print(f"mujoco_xml={mujoco_xml}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print(f"pipeline command failed with exit code {exc.returncode}", file=sys.stderr)
        sys.exit(exc.returncode)
