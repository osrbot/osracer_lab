#!/usr/bin/env python3
"""Verify a read-only source authority snapshot against OSRacer runtime contracts."""

import argparse
import ast
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ASSETS_SRC = REPO_ROOT / "source" / "osracer_lab_assets"
if str(ASSETS_SRC) not in sys.path:
    sys.path.insert(0, str(ASSETS_SRC))

from osracer_lab_assets.hardware_params import hardware_summary  # noqa: E402

EXPECTED_TRUE = (
    ("osrcore_contract", "velocity_command_documented"),
    ("osrcore_contract", "stream_modes_documented"),
    ("osrcore_contract", "sync_frame_documented"),
    ("osrcore_contract", "sn_get_supported"),
    ("osrcore_contract", "sync_frame_sender_present"),
    ("osracer_contract", "writes_v_command_speed_steering_deg"),
    ("osracer_contract", "cmd_vel_writes_v_command"),
    ("osracer_contract", "converts_ackermann_rad_to_deg"),
    ("osracer_contract", "readme_documents_stream_sync"),
    ("osracer_contract", "readme_documents_sync_frames"),
)


def parse_args():
    parser = argparse.ArgumentParser(description="Verify source authority snapshot facts.")
    parser.add_argument("snapshot", help="JSON snapshot produced from read-only osrcore/osracer sources")
    parser.add_argument("--osracer-root", default=str(REPO_ROOT.parent / "osracer"), help="Current osracer feat-demo checkout")
    return parser.parse_args()


def load_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("snapshot root must be an object")
    return data


def read_text(path):
    if not path.is_file():
        raise FileNotFoundError(path)
    return path.read_text(errors="replace")


def find_default_launch_value(text, argument_name):
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


def ok(message):
    print(f"[OK] {message}")


def fail(message, failures):
    print(f"[FAIL] {message}")
    failures.append(message)


def expect_equal(name, actual, expected, failures):
    if actual == expected:
        ok(f"{name}: {actual}")
    else:
        fail(f"{name}: actual={actual!r} expected={expected!r}", failures)


def expect_float(name, actual, expected, failures, tol=1e-9):
    if abs(float(actual) - float(expected)) <= tol:
        ok(f"{name}: {actual}")
    else:
        fail(f"{name}: actual={actual!r} expected={expected!r}", failures)


def main():
    args = parse_args()
    snapshot = load_json(args.snapshot)
    failures = []
    sources = snapshot.get("sources", {})
    osrcore_source = sources.get("osrcore", {})
    osracer_source = sources.get("osracer_feat_demo", {})
    osrcore = snapshot.get("osrcore_contract", {})
    osracer = snapshot.get("osracer_contract", {})
    params = hardware_summary()
    runtime = params["real_runtime"]
    chassis = params["chassis"]

    expect_equal("schema_version", snapshot.get("schema_version"), 1, failures)
    expect_equal("osrcore_branch", osrcore_source.get("branch"), "main", failures)
    expect_equal("osracer_branch", osracer_source.get("branch"), "feat-demo", failures)
    expect_equal("osrcore_remote", osrcore_source.get("remote"), "https://github.com/osrbot/osrcore.git", failures)
    expect_equal("osracer_remote", osracer_source.get("remote"), "https://github.com/osrbot/osracer.git", failures)
    expect_equal("osrcore_status_clean", osrcore_source.get("status_short"), "", failures)
    expect_equal("osracer_status_clean", osracer_source.get("status_short"), "", failures)

    for section, key in EXPECTED_TRUE:
        actual = snapshot.get(section, {}).get(key)
        expect_equal(f"{section}.{key}", actual, True, failures)

    expect_equal("osrcore.serial_timeout_ms", osrcore.get("serial_timeout_ms"), 500, failures)
    expect_equal("osrcore.steering_min_us", osrcore.get("steering_min_us"), 1000, failures)
    expect_equal("osrcore.steering_center_us", osrcore.get("steering_center_us"), 1500, failures)
    expect_equal("osrcore.steering_max_us", osrcore.get("steering_max_us"), 2000, failures)
    expect_float("osrcore.steering_trim_default_deg", osrcore.get("steering_trim_default_deg"), 0.0, failures)

    expect_equal("snapshot.launch_port_name", osracer.get("launch_port_name"), runtime["serial_port"], failures)
    expect_equal("snapshot.launch_baud_rate", osracer.get("launch_baud_rate"), runtime["serial_baud"], failures)
    expect_float("snapshot.launch_wheelbase_m", osracer.get("launch_wheelbase_m"), chassis["wheelbase_m"], failures)
    expect_float("snapshot.launch_max_steering_angle_deg", osracer.get("launch_max_steering_angle_deg"), 30.0, failures)
    expect_float("snapshot.launch_cmd_watchdog_timeout_s", osracer.get("launch_cmd_watchdog_timeout_s"), runtime["command_watchdog_timeout_s"], failures)

    osracer_root = Path(args.osracer_root)
    launch_text = read_text(osracer_root / "osracer_bringup/launch/chassis_ackermann.launch.py")
    expect_equal("current.launch_port_name", find_default_launch_value(launch_text, "port_name"), osracer.get("launch_port_name"), failures)
    expect_equal("current.launch_baud_rate", int(find_default_launch_value(launch_text, "baud_rate")), osracer.get("launch_baud_rate"), failures)
    expect_float("current.launch_wheelbase_m", find_default_launch_value(launch_text, "wheelbase"), osracer.get("launch_wheelbase_m"), failures)
    expect_float("current.launch_max_steering_angle_deg", find_default_launch_value(launch_text, "max_steering_angle_deg"), osracer.get("launch_max_steering_angle_deg"), failures)
    expect_float("current.launch_cmd_watchdog_timeout_s", find_default_launch_value(launch_text, "cmd_watchdog_timeout_s"), osracer.get("launch_cmd_watchdog_timeout_s"), failures)

    if failures:
        print(f"[FAIL] source authority snapshot verification failed: {len(failures)} issue(s)")
        return 1
    print("[OK] source authority snapshot verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
