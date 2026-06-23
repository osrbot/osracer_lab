#!/usr/bin/env python3
"""Summarize OSRacer sim2real readiness gates."""

import argparse
import contextlib
import io
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ASSETS_SRC = REPO_ROOT / "source" / "osracer_lab_assets"
if str(ASSETS_SRC) not in sys.path:
    sys.path.insert(0, str(ASSETS_SRC))
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

from check_runtime_contract import main as runtime_contract_main
from apply_sensor_extrinsics import FRAME_MEASUREMENT_KEYS, build_review as build_extrinsics_review
from hardware_params_loader import hardware_summary
from validate_real_measurements import validate_measurements


def parse_args():
    parser = argparse.ArgumentParser(description="Summarize OSRacer sim2real readiness.")
    parser.add_argument(
        "--osracer-root",
        default=str(REPO_ROOT.parent / "osracer"),
        help="Path to the upper-computer osracer repo",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    parser.add_argument(
        "--measurements",
        default=None,
        help="Path to real-car measurement JSON; defaults to docs/real_car_measurements.json when present",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero when any readiness gate is not pass",
    )
    return parser.parse_args()


def run_runtime_contract(osracer_root, strict_extrinsics=False):
    argv = [
        "check_runtime_contract.py",
        "--osracer-root",
        str(osracer_root),
    ]
    if strict_extrinsics:
        argv.append("--strict-extrinsics")

    old_argv = sys.argv
    output = io.StringIO()
    try:
        sys.argv = argv
        with contextlib.redirect_stdout(output):
            code = runtime_contract_main()
    finally:
        sys.argv = old_argv

    return {
        "status": "pass" if code == 0 else "fail",
        "exit_code": code,
        "log": output.getvalue().strip().splitlines(),
    }


def gate(name, status, detail):
    return {"name": name, "status": status, "detail": detail}


def resolve_measurements_path(path_arg):
    if path_arg:
        return Path(path_arg).expanduser().resolve()
    default_path = REPO_ROOT / "docs" / "real_car_measurements.json"
    return default_path if default_path.exists() else None


def load_measurements(path):
    if path is None:
        return {}, None
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("measurement JSON root must be an object")
    measurements = data.get("measurements", data)
    if not isinstance(measurements, dict):
        raise ValueError("measurement JSON must contain an object at 'measurements'")
    return measurements, str(path)


def summarize_measurements(required, measurements):
    report = validate_measurements(measurements, required)
    return report["complete"], report["missing"], report["incomplete"], report["invalid"]


def summarize_extrinsics(measurements, osracer_root, complete_measurements):
    required = set(FRAME_MEASUREMENT_KEYS.values())
    if not required.issubset(set(complete_measurements)):
        missing = sorted(required - set(complete_measurements))
        return {
            "overall": "fail",
            "all_frames_match": False,
            "missing_or_invalid_measurements": missing,
            "next_action": "record and validate measured sensor extrinsics",
        }
    try:
        return build_extrinsics_review(measurements, osracer_root)
    except Exception as exc:
        return {
            "overall": "fail",
            "all_frames_match": False,
            "error": str(exc),
            "next_action": "fix sensor extrinsics review inputs",
        }


def build_report(osracer_root, measurements_path=None):
    params = hardware_summary()
    required = list(params["required_real_car_measurements"])
    measurements, loaded_measurements_path = load_measurements(measurements_path)
    complete_measurements, missing_measurements, incomplete_measurements, invalid_measurements = summarize_measurements(required, measurements)
    remaining_count = len(missing_measurements) + len(incomplete_measurements) + len(invalid_measurements)
    normal_contract = run_runtime_contract(osracer_root, strict_extrinsics=False)
    strict_contract = run_runtime_contract(osracer_root, strict_extrinsics=True)
    extrinsics_review = summarize_extrinsics(measurements, osracer_root, complete_measurements)

    gates = [
        gate(
            "runtime_contract",
            normal_contract["status"],
            "Upper-computer launch/URDF values match hardware_params.py",
        ),
        gate(
            "strict_extrinsics",
            strict_contract["status"],
            "URDF and static TF must agree before calibrated visual/lidar/IMU sim2real",
        ),
        gate(
            "measured_sensor_extrinsics_applied",
            extrinsics_review["overall"],
            "Measured camera/lidar/IMU extrinsics must match both URDF and static TF",
        ),
        gate(
            "required_real_measurements",
            "fail" if remaining_count else "pass",
            f"{len(complete_measurements)}/{len(required)} measured real-car parameter item(s) complete and format-valid",
        ),
    ]
    overall = "pass" if all(item["status"] == "pass" for item in gates) else "fail"
    return {
        "overall": overall,
        "gates": gates,
        "measurements_path": loaded_measurements_path,
        "complete_real_measurements": complete_measurements,
        "missing_real_measurements": missing_measurements,
        "incomplete_real_measurements": incomplete_measurements,
        "invalid_real_measurements": invalid_measurements,
        "required_real_measurements": missing_measurements
        + incomplete_measurements
        + [item["name"] for item in invalid_measurements],
        "sensor_extrinsics_review": extrinsics_review,
        "runtime_contract_log": normal_contract["log"],
        "strict_extrinsics_log": strict_contract["log"],
    }


def print_text(report):
    print(f"sim2real_readiness: {report['overall']}")
    for item in report["gates"]:
        print(f"[{item['status'].upper()}] {item['name']}: {item['detail']}")
    if report["measurements_path"]:
        print(f"measurements_path: {report['measurements_path']}")
    else:
        print("measurements_path: not provided")
    if report["missing_real_measurements"]:
        print("missing_measurements:")
        for name in report["missing_real_measurements"]:
            print(f"  - {name}")
    if report["incomplete_real_measurements"]:
        print("incomplete_measurements:")
        for name in report["incomplete_real_measurements"]:
            print(f"  - {name}")
    if report["invalid_real_measurements"]:
        print("invalid_measurements:")
        for item in report["invalid_real_measurements"]:
            print(f"  - {item['name']}: {item['error']}")


def main():
    args = parse_args()
    measurements_path = resolve_measurements_path(args.measurements)
    report = build_report(Path(args.osracer_root).resolve(), measurements_path)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    if args.strict and report["overall"] != "pass":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
