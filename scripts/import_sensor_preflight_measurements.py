#!/usr/bin/env python3
"""Import Jetson sensor preflight evidence into real-car measurement JSON."""

import argparse
import datetime as dt
import json
from pathlib import Path

DEFAULT_TOPIC_LABELS = {
    "/rgb/image_raw": "camera",
    "/scan": "lidar",
    "/imu_filter": "imu",
    "/odometry/filtered": "odom",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Merge tools/jetson_sensor_preflight.sh summary evidence into real-car measurements."
    )
    parser.add_argument("--measurements", required=True, help="Path to docs/real_car_measurements.json")
    parser.add_argument("--sensor-summary", required=True, help="Path to sensor_summary.json from osracer tools")
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


def topic_rate(report, topic):
    data = report.get("topics", {}).get(topic, {})
    hz = data.get("hz", {})
    info = data.get("info", {})
    return {
        "topic": topic,
        "type": info.get("type"),
        "publisher_count": info.get("publisher_count"),
        "average_rate_hz": hz.get("average_rate_hz"),
        "status_ok": info.get("publisher_count", 0) > 0 and hz.get("average_rate_hz") is not None,
    }


def build_timestamp_value(report):
    required = report.get("required_topics") or list(DEFAULT_TOPIC_LABELS)
    topic_rates = [topic_rate(report, topic) for topic in required]
    if any(not item["status_ok"] for item in topic_rates):
        missing = [item["topic"] for item in topic_rates if not item["status_ok"]]
        return None, topic_rates, f"required topic(s) missing or without rate: {', '.join(missing)}"
    compact = []
    for item in topic_rates:
        label = DEFAULT_TOPIC_LABELS.get(item["topic"], item["topic"])
        compact.append(f"{label} {item['topic']} avg {item['average_rate_hz']:.3f} Hz")
    value = (
        "Jetson ROS 2 preflight observed required sensor topics with ros2 topic hz; "
        "timestamps are treated as ROS/driver message timing evidence, not PPS/PTP hardware sync. "
        + "; ".join(compact)
    )
    return value, topic_rates, None


def merge_note(existing, addition):
    existing = existing or ""
    if addition in existing:
        return existing
    return (existing + "\n" + addition).strip()


def apply_import(measurements, report, summary_path):
    changes = []
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    value, topic_rates, error = build_timestamp_value(report)
    evidence = {
        "sensor_summary": str(Path(summary_path).resolve()),
        "overall": report.get("overall"),
        "topic_rates": topic_rates,
    }
    measurements.setdefault("collection", {})["sensor_preflight"] = evidence
    changes.append("collection.sensor_preflight")

    if value is None:
        return changes, error

    entry = measurement_entry(measurements, "sensor_timestamp_sync_method")
    if not entry.get("value"):
        entry["value"] = value
        changes.append("measurements.sensor_timestamp_sync_method.value")
    if not entry.get("source"):
        entry["source"] = str(Path(summary_path).resolve())
        changes.append("measurements.sensor_timestamp_sync_method.source")
    if not entry.get("measured_at"):
        entry["measured_at"] = now
        changes.append("measurements.sensor_timestamp_sync_method.measured_at")
    entry["notes"] = merge_note(
        entry.get("notes"),
        "Imported from Jetson sensor preflight. This confirms topic visibility/rates only; it does not prove hardware clock synchronization.",
    )
    return changes, None


def main():
    args = parse_args()
    measurements_path = Path(args.measurements)
    output_path = Path(args.output) if args.output else measurements_path
    measurements = load_json(measurements_path)
    report = load_json(args.sensor_summary)
    changes, error = apply_import(measurements, report, args.sensor_summary)

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
        print(f"timestamp_method_not_imported: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
