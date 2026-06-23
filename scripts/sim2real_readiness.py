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
from osracer_lab_assets.hardware_params import hardware_summary


def parse_args():
    parser = argparse.ArgumentParser(description="Summarize OSRacer sim2real readiness.")
    parser.add_argument(
        "--osracer-root",
        default=str(REPO_ROOT.parent / "osracer"),
        help="Path to the upper-computer osracer repo",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
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


def build_report(osracer_root):
    params = hardware_summary()
    required = list(params["required_real_car_measurements"])
    normal_contract = run_runtime_contract(osracer_root, strict_extrinsics=False)
    strict_contract = run_runtime_contract(osracer_root, strict_extrinsics=True)

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
            "required_real_measurements",
            "fail" if required else "pass",
            f"{len(required)} measured real-car parameter item(s) still required",
        ),
    ]
    overall = "pass" if all(item["status"] == "pass" for item in gates) else "fail"
    return {
        "overall": overall,
        "gates": gates,
        "required_real_measurements": required,
        "runtime_contract_log": normal_contract["log"],
        "strict_extrinsics_log": strict_contract["log"],
    }


def print_text(report):
    print(f"sim2real_readiness: {report['overall']}")
    for item in report["gates"]:
        print(f"[{item['status'].upper()}] {item['name']}: {item['detail']}")
    if report["required_real_measurements"]:
        print("missing_measurements:")
        for name in report["required_real_measurements"]:
            print(f"  - {name}")


def main():
    args = parse_args()
    report = build_report(Path(args.osracer_root).resolve())
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    if args.strict and report["overall"] != "pass":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
