#!/usr/bin/env python3
"""Import serial latency probe output into real-car measurement JSON."""

import argparse
import datetime as dt
import json
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Merge serial latency probe output into real-car measurements.")
    parser.add_argument("--measurements", required=True, help="Path to docs/real_car_measurements.json")
    parser.add_argument("--serial-report", required=True, help="JSON produced by tools/serial_latency_probe.py")
    parser.add_argument("--output", default=None, help="Output path. Defaults to updating --measurements in place.")
    parser.add_argument("--write", action="store_true", help="Write changes instead of printing a dry-run summary.")
    return parser.parse_args()


def load_json(path):
    with Path(path).open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def measurement_entry(data, key):
    measurements = data.setdefault("measurements", {})
    if not isinstance(measurements, dict):
        raise ValueError("measurements must be a JSON object")
    entry = measurements.setdefault(key, {"value": None, "source": "", "measured_at": "", "notes": ""})
    if not isinstance(entry, dict):
        entry = {"value": entry, "source": "", "measured_at": "", "notes": ""}
        measurements[key] = entry
    return entry


def choose_latency(report):
    latency = report.get("latency_s", {})
    for key in ("p95", "max", "mean", "median", "min"):
        value = latency.get(key)
        if value is not None:
            return float(value), key
    return None, None


def merge_note(existing, addition):
    existing = existing or ""
    if addition in existing:
        return existing
    return (existing + "\n" + addition).strip()


def apply_import(measurements, report, report_path):
    changes = []
    if report.get("overall") != "pass" or int(report.get("successful_samples", 0)) <= 0:
        return changes, "serial report has no successful samples"
    baud_rate = report.get("baud_rate")
    if baud_rate is None:
        return changes, "serial report is missing baud_rate"
    latency_s, latency_source = choose_latency(report)
    if latency_s is None:
        return changes, "serial report is missing latency statistics"

    measured_at = report.get("measured_at") or dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    value = {"baud_rate": int(baud_rate), "command_latency_s": latency_s}
    measurements.setdefault("collection", {})["serial_latency_probe"] = {
        "serial_report": str(Path(report_path).resolve()),
        "command": report.get("command"),
        "successful_samples": report.get("successful_samples"),
        "latency_stat_used": latency_source,
        "latency_s": report.get("latency_s"),
    }
    changes.append("collection.serial_latency_probe")

    entry = measurement_entry(measurements, "serial_baud_rate_and_command_latency_s")
    entry["value"] = value
    entry["source"] = str(Path(report_path).resolve())
    entry["measured_at"] = measured_at
    entry["notes"] = merge_note(
        entry.get("notes"),
        f"Imported from read-only serial latency probe using command {report.get('command')!r}; command_latency_s uses {latency_source} latency.",
    )
    changes.append("measurements.serial_baud_rate_and_command_latency_s")
    return changes, None


def main():
    args = parse_args()
    measurements_path = Path(args.measurements)
    output_path = Path(args.output) if args.output else measurements_path
    measurements = load_json(measurements_path)
    report = load_json(args.serial_report)
    changes, error = apply_import(measurements, report, args.serial_report)
    if args.write:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(measurements, indent=2, sort_keys=False) + "\n", encoding="utf-8")
        print(f"wrote {output_path}")
    else:
        print("dry_run: pass --write to update the measurement file")
    print("changes:")
    for item in changes:
        print(f"  - {item}")
    if error:
        print(f"serial_latency_not_imported: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
