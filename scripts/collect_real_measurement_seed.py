#!/usr/bin/env python3
"""Create a real-car measurement JSON seed without inventing measurements."""

import argparse
import datetime as dt
import json
import platform
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "source" / "osracer_lab_assets"))

from osracer_lab_assets.hardware_params import hardware_summary  # noqa: E402


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create docs/real_car_measurements.json from the template and known repo facts."
    )
    parser.add_argument(
        "--template",
        default=str(REPO_ROOT / "docs" / "real_car_measurements.template.json"),
        help="Measurement template JSON path.",
    )
    parser.add_argument(
        "--output",
        default=str(REPO_ROOT / "docs" / "real_car_measurements.json"),
        help="Output measurement JSON path.",
    )
    parser.add_argument(
        "--osracer-root",
        default=str(REPO_ROOT.parent / "osracer"),
        help="Path to the osracer feat-demo checkout.",
    )
    parser.add_argument("--overwrite", action="store_true", help="Overwrite output if it already exists.")
    return parser.parse_args()


def run(command, cwd=None):
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def load_json(path):
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path, data, overwrite=False):
    output = Path(path)
    if output.exists() and not overwrite:
        raise FileExistsError(f"{output} already exists; pass --overwrite to replace it")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=False)
        f.write("\n")


def entry(measurements, name):
    value = measurements.get(name)
    if not isinstance(value, dict):
        value = {"value": value, "source": "", "notes": ""}
        measurements[name] = value
    return value


def merge_partial(measurements, name, value, source, measured_at, notes):
    target = entry(measurements, name)
    if target.get("value") in (None, "", [], {}):
        target["value"] = value
    if not target.get("source"):
        target["source"] = source
    if not target.get("measured_at"):
        target["measured_at"] = measured_at
    existing_notes = target.get("notes", "")
    if notes and notes not in existing_notes:
        target["notes"] = (existing_notes + "\n" + notes).strip()


def osracer_git_facts(osracer_root):
    root = Path(osracer_root)
    if not root.exists():
        return {"path": str(root), "available": False}
    return {
        "path": str(root),
        "available": True,
        "branch": run(["git", "branch", "--show-current"], cwd=root),
        "head": run(["git", "rev-parse", "--short", "HEAD"], cwd=root),
        "remote": run(["git", "remote", "-v"], cwd=root),
    }


def main():
    args = parse_args()
    data = load_json(args.template)
    if not isinstance(data, dict) or not isinstance(data.get("measurements"), dict):
        raise ValueError("template must contain a measurements object")

    params = hardware_summary()
    runtime = params["real_runtime"]
    source_authority = params["source_authority"]
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    source = (
        f"{source_authority['upper_computer_repo']} and "
        f"{source_authority['firmware_repo']} protocol contract"
    )

    merge_partial(
        data["measurements"],
        "serial_baud_rate_and_command_latency_s",
        {"baud_rate": runtime["serial_baud"]},
        source,
        now,
        "Seeded only with repo-confirmed baud rate. Measure command_latency_s on the real car before this item can pass.",
    )

    data["collection"] = {
        "created_at": now,
        "host": {
            "hostname": platform.node(),
            "system": platform.platform(),
            "machine": platform.machine(),
        },
        "source_authority": source_authority,
        "osracer_checkout": osracer_git_facts(args.osracer_root),
        "runtime_contract": {
            "serial_port": runtime["serial_port"],
            "serial_baud": runtime["serial_baud"],
            "command_protocol": runtime["command_protocol"],
            "ackermann_cmd_topic": runtime["ackermann_cmd_topic"],
            "imu_topic": runtime["imu_topic"],
            "odom_topic": runtime["odom_topic"],
        },
        "manual_next_steps": [
            "Measure mass, axle weights, front track, tire width, steering limits, steering response, motor/ESC response, and speed limits.",
            "Measure camera, lidar, and IMU extrinsics in base_link and resolve the URDF vs static TF conflict.",
            "Run the Jetson sensor preflight and copy topic-rate evidence into source fields where relevant.",
            "Measure serial command latency; baud rate alone is intentionally not enough for readiness.",
        ],
    }

    write_json(args.output, data, overwrite=args.overwrite)
    print(f"wrote {Path(args.output).resolve()}")
    print("seeded: serial_baud_rate_and_command_latency_s.baud_rate")
    print("remaining measurements still require real hardware evidence")


if __name__ == "__main__":
    raise SystemExit(main())
