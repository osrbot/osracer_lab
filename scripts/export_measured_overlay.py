#!/usr/bin/env python3
"""Export a measured-parameter overlay JSON without mutating source files."""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ASSETS_SRC = REPO_ROOT / "source" / "osracer_lab_assets"
if str(ASSETS_SRC) not in sys.path:
    sys.path.insert(0, str(ASSETS_SRC))
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

from osracer_lab_assets.hardware_params import hardware_summary  # noqa: E402
from plan_calibration_updates import build_plan  # noqa: E402
from validate_real_measurements import entry_value, validate_measurements  # noqa: E402

OVERLAY_GROUPS = {
    "chassis": [
        "full_vehicle_mass_kg_with_battery_jetson_sensors",
        "front_track_m",
        "tire_width_m",
        "front_rear_weight_distribution",
    ],
    "steering": [
        "true_max_steering_rad_left_right",
        "steering_servo_pwm_min_center_max_or_protocol_units",
        "steering_response_time_s",
    ],
    "powertrain": [
        "motor_kv_or_rated_rpm",
        "battery_voltage_s_count",
        "true_max_speed_mps",
        "minimum_stable_speed_mps",
        "throttle_deadband_and_response_delay_s",
        "encoder_ticks_per_revolution_and_mount_location",
    ],
    "imu": ["imu_model_rate_ranges_and_frame_alignment"],
    "camera_calibration": ["camera_intrinsics_fx_fy_cx_cy_distortion"],
    "sensor_extrinsics": [
        "camera_extrinsic_xyz_rpy_in_base_link",
        "lidar_extrinsic_xyz_rpy_in_base_link",
        "imu_extrinsic_xyz_rpy_in_base_link",
        "resolve_urdf_vs_static_tf_sensor_extrinsics",
    ],
    "timing": [
        "serial_baud_rate_and_command_latency_s",
        "sensor_timestamp_sync_method",
    ],
}


def parse_args():
    parser = argparse.ArgumentParser(description="Export measured OSRacer overlay JSON for sim/replay consumers.")
    parser.add_argument("--measurements", required=True, help="Path to docs/real_car_measurements.json")
    parser.add_argument("--output", default="-", help="Output JSON path, or '-' for stdout")
    parser.add_argument("--indent", type=int, default=2)
    return parser.parse_args()


def load_measurements(path):
    with Path(path).open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("measurement JSON root must be an object")
    measurements = data.get("measurements", data)
    if not isinstance(measurements, dict):
        raise ValueError("measurement JSON must contain a measurements object")
    return data, measurements


def measured_value(measurements, key):
    return entry_value(measurements[key])


def measured_source(measurements, key):
    entry = measurements[key]
    return entry.get("source") if isinstance(entry, dict) else None


def build_overlay(measurement_doc, measurements):
    report = validate_measurements(measurements)
    complete = set(report["complete"])
    overlay = {}
    sources = {}
    for group, keys in OVERLAY_GROUPS.items():
        group_values = {}
        group_sources = {}
        for key in keys:
            if key in complete:
                group_values[key] = measured_value(measurements, key)
                group_sources[key] = measured_source(measurements, key)
        if group_values:
            overlay[group] = group_values
            sources[group] = group_sources

    plan = build_plan(measurements)
    return {
        "schema_version": 1,
        "vehicle": measurement_doc.get("vehicle", "osracer_real_car"),
        "base_hardware_params": hardware_summary(),
        "measured_overlay": overlay,
        "measurement_sources": sources,
        "validation": report,
        "calibration_plan": {
            "auto_apply_ready": plan["auto_apply_ready"],
            "review_apply_ready": plan["review_apply_ready"],
            "blocked_auto_apply": plan["blocked_auto_apply"],
        },
        "usage_note": (
            "This overlay is safe for offline sim/replay experiments. Do not write review_apply_ready "
            "values into source parameters without reviewing the calibration plan."
        ),
    }


def main():
    args = parse_args()
    measurement_doc, measurements = load_measurements(args.measurements)
    payload = build_overlay(measurement_doc, measurements)
    text = json.dumps(payload, indent=args.indent, sort_keys=True)
    if args.output == "-":
        print(text)
    else:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + "\n", encoding="utf-8")
        print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
