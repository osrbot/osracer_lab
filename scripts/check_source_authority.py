#!/usr/bin/env python3
"""Check OSRacer source-of-truth repositories and protocol assumptions."""

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

EXPECTED_OSRACER_BRANCH = "feat-demo"
EXPECTED_OSRACER_REMOTE = "osrbot/osracer"
EXPECTED_FIRMWARE_REMOTE = "osrbot/osrcore"


def parse_args():
    parser = argparse.ArgumentParser(description="Check OSRacer source authority assumptions.")
    parser.add_argument(
        "--osracer-root",
        default=str(REPO_ROOT.parent / "osracer"),
        help="Path to ROS upper-computer osracer repo",
    )
    parser.add_argument(
        "--osrcore-root",
        default=str(REPO_ROOT.parent / "osrcore"),
        help="Path to osrbot/osrcore firmware repo for direct firmware protocol checks",
    )
    parser.add_argument("--strict-osrcore", action="store_true", help="Fail when --osrcore-root is missing or invalid")
    return parser.parse_args()


def run_git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True, stderr=subprocess.STDOUT).strip()


def read_text(path):
    if not path.is_file():
        raise FileNotFoundError(path)
    return path.read_text(errors="replace")


def check(condition, label, failures, detail=""):
    if condition:
        print(f"[OK] {label}{': ' + detail if detail else ''}")
    else:
        print(f"[FAIL] {label}{': ' + detail if detail else ''}")
        failures.append(label)


def warn(label, detail=""):
    print(f"[WARN] {label}{': ' + detail if detail else ''}")


def remote_mentions(repo, expected):
    try:
        remotes = run_git(repo, "remote", "-v")
    except subprocess.CalledProcessError:
        return False, ""
    return expected in remotes, remotes


def check_osracer(osracer_root, failures):
    osracer_root = Path(osracer_root)
    check((osracer_root / ".git").exists(), "osracer_repo_exists", failures, str(osracer_root))
    if failures and failures[-1] == "osracer_repo_exists":
        return

    try:
        branch = run_git(osracer_root, "branch", "--show-current")
    except subprocess.CalledProcessError as exc:
        check(False, "osracer_git_branch", failures, exc.output.strip())
        branch = ""
    check(branch == EXPECTED_OSRACER_BRANCH, "osracer_branch_is_feat_demo", failures, branch)

    ok_remote, remotes = remote_mentions(osracer_root, EXPECTED_OSRACER_REMOTE)
    check(ok_remote, "osracer_remote_is_osrbot_osracer", failures, remotes.splitlines()[0] if remotes else "")

    launch = read_text(osracer_root / "osracer_bringup/launch/chassis_ackermann.launch.py")
    bridge = read_text(osracer_root / "osracer_bringup/script/chassis_ackermann.py")
    readme = read_text(osracer_root / "README.md")
    combined = launch + "\n" + bridge + "\n" + readme
    check("/dev/osrbot_base" in combined, "osracer_serial_device_contract", failures, "/dev/osrbot_base")
    check("460800" in combined, "osracer_serial_baud_contract", failures, "460800")
    check("stream sync" in combined, "osracer_stream_sync_contract_documented", failures)
    check("s/m/r/b" in combined, "osracer_sync_frames_contract_documented", failures)
    check('command = f"v {speed:.3f} {steering_angle_deg:.2f}' in bridge, "osracer_writes_osrcore_v_command", failures)
    check("steering_angle_deg = math.degrees(steering_angle_rad)" in bridge, "osracer_converts_steering_rad_to_deg", failures)


def check_osrcore(osrcore_root, failures, strict):
    osrcore_root = Path(osrcore_root)
    if not (osrcore_root / ".git").exists():
        if strict:
            check(False, "osrcore_repo_exists", failures, str(osrcore_root))
        else:
            warn("osrcore_repo_missing", str(osrcore_root))
        return

    ok_remote, remotes = remote_mentions(osrcore_root, EXPECTED_FIRMWARE_REMOTE)
    check(ok_remote, "osrcore_remote_is_osrbot_osrcore", failures, remotes.splitlines()[0] if remotes else "")
    protocol = read_text(osrcore_root / "docs/serial_protocol.md")
    serial_cmd = read_text(osrcore_root / "main/serial_cmd.cpp")
    combined = protocol + "\n" + serial_cmd
    check("v <vx_m/s> <steer_deg>" in protocol, "osrcore_v_command_contract", failures)
    check("stream sync|legacy|off" in combined, "osrcore_stream_contract", failures)
    check("s px py pz vx vy vz yaw qx qy qz qw ax ay az gx gy gz" in protocol, "osrcore_sync_frame_contract", failures)
    check("sn get" in combined, "osrcore_sn_get_contract", failures)
    check("500 ms" in protocol, "osrcore_serial_watchdog_contract", failures)


def main():
    args = parse_args()
    failures = []
    check_osracer(args.osracer_root, failures)
    check_osrcore(args.osrcore_root, failures, args.strict_osrcore)
    if failures:
        print("source_authority: fail")
        return 1
    print("source_authority: pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
