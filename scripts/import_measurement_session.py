#!/usr/bin/env python3
"""Import a Jetson measurement session manifest into real-car measurements."""

import argparse
import importlib.util
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

sensor_importer = load_module("sensor_importer", SCRIPT_DIR / "import_sensor_preflight_measurements.py")
serial_importer = load_module("serial_importer", SCRIPT_DIR / "import_serial_latency_measurement.py")


def parse_args():
    parser = argparse.ArgumentParser(description="Import measurement_session.json evidence into real-car measurements.")
    parser.add_argument("--measurements", required=True, help="Path to docs/real_car_measurements.json")
    parser.add_argument("--session", required=True, help="measurement_session.json from tools/jetson_measurement_session.sh")
    parser.add_argument("--output", default=None, help="Output path. Defaults to updating --measurements in place.")
    parser.add_argument("--write", action="store_true", help="Write changes instead of printing a dry-run summary.")
    return parser.parse_args()


def load_json(path):
    with Path(path).open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def resolve_path(session_file, maybe_path):
    if not maybe_path:
        return None
    path = Path(maybe_path)
    if path.is_absolute():
        return path
    return (Path(session_file).resolve().parent / path).resolve()



def import_environment_report(measurements, report, report_path):
    collection = measurements.setdefault("collection", {})
    jetson = report.get("jetson", {}) if isinstance(report.get("jetson"), dict) else {}
    ros = report.get("ros", {}) if isinstance(report.get("ros"), dict) else {}
    collection["jetson_environment"] = {
        "report_file": str(Path(report_path).resolve()),
        "overall": report.get("overall"),
        "is_jetson": jetson.get("is_jetson"),
        "device_model": jetson.get("device_model"),
        "nv_tegra_release": jetson.get("nv_tegra_release"),
        "ros_distro": ros.get("distro"),
        "ros_setup_exists": ros.get("setup_exists"),
        "failures": report.get("failures", []),
        "warnings": report.get("warnings", []),
    }
    return "collection.jetson_environment"


def apply_session(measurements, session, session_file):
    changes = []
    errors = []
    collection = measurements.setdefault("collection", {})
    collection["measurement_session"] = {
        "session_file": str(Path(session_file).resolve()),
        "created_at": session.get("created_at"),
        "output_dir": session.get("output_dir"),
    }
    changes.append("collection.measurement_session")

    tools = session.get("tools", {})
    sensor = tools.get("sensor_preflight", {})
    sensor_summary = resolve_path(session_file, sensor.get("sensor_summary"))
    if sensor_summary and sensor_summary.exists():
        report = load_json(sensor_summary)
        sub_changes, error = sensor_importer.apply_import(measurements, report, sensor_summary)
        changes.extend(sub_changes)
        if error:
            errors.append(f"sensor_preflight: {error}")
    elif sensor.get("status") not in (None, "skipped"):
        errors.append("sensor_preflight: sensor_summary missing")

    environment = tools.get("jetson_environment", {})
    environment_report = resolve_path(session_file, environment.get("environment_report"))
    if environment_report and environment_report.exists():
        report = load_json(environment_report)
        changes.append(import_environment_report(measurements, report, environment_report))
    elif environment.get("status") not in (None, "skipped"):
        errors.append("jetson_environment: environment_report missing")

    serial = tools.get("serial_latency", {})
    serial_report = resolve_path(session_file, serial.get("serial_report"))
    if serial_report and serial_report.exists():
        report = load_json(serial_report)
        sub_changes, error = serial_importer.apply_import(measurements, report, serial_report)
        changes.extend(sub_changes)
        if error:
            errors.append(f"serial_latency: {error}")
    elif serial.get("status") not in (None, "skipped"):
        errors.append("serial_latency: serial_report missing")

    return changes, errors


def main():
    args = parse_args()
    measurements_path = Path(args.measurements)
    output_path = Path(args.output) if args.output else measurements_path
    measurements = load_json(measurements_path)
    session = load_json(args.session)
    changes, errors = apply_session(measurements, session, args.session)
    if args.write:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(measurements, indent=2, sort_keys=False) + "\n", encoding="utf-8")
        print(f"wrote {output_path}")
    else:
        print("dry_run: pass --write to update the measurement file")
    print("changes:")
    for item in changes:
        print(f"  - {item}")
    if errors:
        print("errors:")
        for item in errors:
            print(f"  - {item}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
