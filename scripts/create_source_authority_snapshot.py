#!/usr/bin/env python3
"""Create a read-only OSRacer source authority snapshot from osrcore and osracer."""

import argparse
import ast
import json
import re
import subprocess
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Create source authority snapshot JSON from read-only source repos.")
    parser.add_argument("--osrcore-root", required=True, help="Read-only osrbot/osrcore checkout")
    parser.add_argument("--osracer-root", required=True, help="Read-only osrbot/osracer feat-demo checkout")
    parser.add_argument("--output", default="-", help="Output JSON path, or '-' for stdout")
    parser.add_argument("--indent", type=int, default=2)
    return parser.parse_args()


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True, stderr=subprocess.STDOUT).strip()


def read_text(path):
    if not path.is_file():
        raise FileNotFoundError(path)
    return path.read_text(errors="replace")


def require_git_repo(path, label):
    path = Path(path).resolve()
    if not (path / ".git").exists():
        raise FileNotFoundError(f"{label} is not a git checkout: {path}")
    return path


def find_define_int(text, name):
    match = re.search(r"#define\s+" + re.escape(name) + r"\s+([-+]?\d+)", text)
    if not match:
        raise ValueError(f"C define not found: {name}")
    return int(match.group(1))


def find_define_float(text, name):
    match = re.search(r"#define\s+" + re.escape(name) + r"\s+([-+]?\d+(?:\.\d+)?)", text)
    if not match:
        raise ValueError(f"C define not found: {name}")
    return float(match.group(1))


def find_launch_default(text, argument_name):
    pattern = re.compile(
        r"DeclareLaunchArgument\(\s*['\"]"
        + re.escape(argument_name)
        + r"['\"].*?default_value\s*=\s*([^,\n)]+)",
        re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        raise ValueError(f"Launch argument not found: {argument_name}")
    return ast.literal_eval(match.group(1).strip())


def source_meta(repo):
    return {
        "branch": git(repo, "branch", "--show-current"),
        "head": git(repo, "rev-parse", "--short", "HEAD"),
        "remote": git(repo, "remote", "get-url", "origin"),
        "status_short": git(repo, "status", "--short"),
    }


def build_snapshot(osrcore_root, osracer_root):
    osrcore_config = read_text(osrcore_root / "main/config.h")
    osrcore_protocol = read_text(osrcore_root / "docs/serial_protocol.md")
    osrcore_serial = read_text(osrcore_root / "main/serial_cmd.cpp")
    osrcore_frames = read_text(osrcore_root / "main/serial_frames.cpp")
    osracer_launch = read_text(osracer_root / "osracer_bringup/launch/chassis_ackermann.launch.py")
    osracer_bridge = read_text(osracer_root / "osracer_bringup/script/chassis_ackermann.py")
    osracer_readme = read_text(osracer_root / "README.md")

    return {
        "schema_version": 1,
        "sources": {
            "osrcore": source_meta(osrcore_root),
            "osracer_feat_demo": source_meta(osracer_root),
        },
        "osrcore_contract": {
            "serial_timeout_ms": find_define_int(osrcore_config, "SERIAL_TIMEOUT"),
            "steering_min_us": find_define_int(osrcore_config, "STEERING_MIN"),
            "steering_center_us": find_define_int(osrcore_config, "STEERING_CENTER"),
            "steering_max_us": find_define_int(osrcore_config, "STEERING_MAX"),
            "steering_trim_default_deg": find_define_float(osrcore_config, "STEERING_TRIM_DEFAULT_DEG"),
            "velocity_command_documented": "v <vx_m/s> <steer_deg>" in osrcore_protocol,
            "stream_modes_documented": "stream sync|legacy|off" in (osrcore_protocol + osrcore_serial),
            "sync_frame_documented": "s px py pz vx vy vz yaw qx qy qz qw ax ay az gx gy gz" in osrcore_protocol,
            "sn_get_supported": "sn get" in (osrcore_protocol + osrcore_serial),
            "sync_frame_sender_present": "serial_frame_send_sync" in osrcore_frames,
        },
        "osracer_contract": {
            "launch_port_name": find_launch_default(osracer_launch, "port_name"),
            "launch_baud_rate": int(find_launch_default(osracer_launch, "baud_rate")),
            "launch_wheelbase_m": float(find_launch_default(osracer_launch, "wheelbase")),
            "launch_max_steering_angle_deg": float(find_launch_default(osracer_launch, "max_steering_angle_deg")),
            "launch_cmd_watchdog_timeout_s": float(find_launch_default(osracer_launch, "cmd_watchdog_timeout_s")),
            "writes_v_command_speed_steering_deg": 'command = f"v {speed:.3f} {steering_angle_deg:.2f}' in osracer_bridge,
            "cmd_vel_writes_v_command": 'command = f"v {linear_x:.3f} {steering_angle_deg:.2f}' in osracer_bridge,
            "converts_ackermann_rad_to_deg": "steering_angle_deg = math.degrees(steering_angle_rad)" in osracer_bridge,
            "readme_documents_stream_sync": "stream sync" in osracer_readme,
            "readme_documents_sync_frames": "s/m/r/b" in osracer_readme,
        },
    }


def main():
    args = parse_args()
    osrcore_root = require_git_repo(args.osrcore_root, "osrcore-root")
    osracer_root = require_git_repo(args.osracer_root, "osracer-root")
    snapshot = build_snapshot(osrcore_root, osracer_root)
    text = json.dumps(snapshot, indent=args.indent, sort_keys=True) + "\n"
    if args.output == "-":
        print(text, end="")
    else:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
