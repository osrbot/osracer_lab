#!/usr/bin/env python3
"""Report OSRacer real-car measurement gaps with grouped next actions."""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

from create_measurement_pack import GROUPS, METHODS  # noqa: E402
from validate_real_measurements import (  # noqa: E402
    REQUIRED_KEYS,
    entry_source,
    entry_value,
    has_source,
    has_value,
    validate_measurements,
)


def parse_args():
    parser = argparse.ArgumentParser(description="Report OSRacer real-car measurement gaps.")
    parser.add_argument("measurements", help="Path to docs/real_car_measurements.json or template JSON")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    parser.add_argument("--strict", action="store_true", help="Return nonzero if any required measurement is missing, incomplete, or invalid")
    return parser.parse_args()


def load_doc(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("measurement JSON root must be an object")
    measurements = data.get("measurements", data)
    if not isinstance(measurements, dict):
        raise ValueError("measurement JSON must contain a measurements object")
    return data, measurements


def invalid_by_name(validation):
    return {item["name"]: item["error"] for item in validation["invalid"]}


def measurement_status(name, measurements, invalid_errors):
    if name not in measurements:
        return {"name": name, "status": "missing"}
    entry = measurements[name]
    value = entry_value(entry)
    source = entry_source(entry)
    result = {
        "name": name,
        "status": "complete",
        "has_value": has_value(value),
        "has_source": has_source(entry),
        "source": source,
        "expected_format": entry.get("expected_format") if isinstance(entry, dict) else None,
        "method": METHODS.get(name, "Record measured value and evidence source."),
    }
    if name in invalid_errors:
        result["status"] = "invalid"
        result["error"] = invalid_errors[name]
    elif not result["has_value"] or not result["has_source"]:
        result["status"] = "incomplete"
    return result


def build_group_report(measurements, validation):
    invalid_errors = invalid_by_name(validation)
    grouped = {}
    for group, names in GROUPS.items():
        items = [measurement_status(name, measurements, invalid_errors) for name in names]
        grouped[group] = {
            "complete": [item["name"] for item in items if item["status"] == "complete"],
            "open": [item for item in items if item["status"] != "complete"],
        }
    grouped_names = {name for names in GROUPS.values() for name in names}
    ungrouped = [name for name in REQUIRED_KEYS if name not in grouped_names]
    if ungrouped:
        items = [measurement_status(name, measurements, invalid_errors) for name in ungrouped]
        grouped["ungrouped"] = {
            "complete": [item["name"] for item in items if item["status"] == "complete"],
            "open": [item for item in items if item["status"] != "complete"],
        }
    return grouped


def summarize_sensor_specs(doc):
    specs = doc.get("confirmed_sensor_specs", {})
    result = {}
    for name in ("camera", "lidar"):
        spec = specs.get(name)
        if isinstance(spec, dict):
            result[name] = {
                "status": "confirmed",
                "source": spec.get("source"),
                "keys": sorted(k for k in spec if k != "source"),
            }
        else:
            result[name] = {"status": "missing"}
    return result


def build_report(path):
    doc, measurements = load_doc(path)
    validation = validate_measurements(measurements)
    open_count = len(validation["missing"]) + len(validation["incomplete"]) + len(validation["invalid"])
    return {
        "measurements_path": str(Path(path).resolve()),
        "vehicle": doc.get("vehicle", "osracer_real_car"),
        "required_count": len(REQUIRED_KEYS),
        "complete_count": len(validation["complete"]),
        "open_count": open_count,
        "valid": open_count == 0,
        "confirmed_sensor_specs": summarize_sensor_specs(doc),
        "validation": validation,
        "groups": build_group_report(measurements, validation),
        "next_commands": [
            "MEASUREMENTS_FILE=docs/real_car_measurements.json scripts/validate_osracer_lab.sh measurement-gap",
            "MEASUREMENTS_FILE=docs/real_car_measurements.json scripts/validate_osracer_lab.sh real-measurements",
            "MEASUREMENTS_FILE=docs/real_car_measurements.json scripts/validate_osracer_lab.sh calibration-plan",
        ],
    }


def print_text(report):
    status = "pass" if report["valid"] else "open"
    print(f"measurement_gap_report: {status}")
    print(f"complete: {report['complete_count']}/{report['required_count']}")
    print("confirmed_sensor_specs:")
    for name, spec in report["confirmed_sensor_specs"].items():
        source = spec.get("source") or ""
        print(f"  - {name}: {spec['status']} {source}".rstrip())
    print("open_measurements:")
    any_open = False
    for group, group_report in report["groups"].items():
        if not group_report["open"]:
            continue
        any_open = True
        print(f"  {group}:")
        for item in group_report["open"]:
            detail = item.get("error") or item.get("expected_format") or "record measured value and source"
            print(f"    - [{item['status']}] {item['name']}: {detail}")
            print(f"      method: {item['method']}")
    if not any_open:
        print("  - none")


def main():
    args = parse_args()
    report = build_report(args.measurements)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    if args.strict and not report["valid"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
