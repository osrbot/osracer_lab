#!/usr/bin/env python3
"""Create a field measurement pack for remaining OSRacer sim2real measurements."""

import argparse
import json
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = REPO_ROOT / "docs" / "real_car_measurements.template.json"
DEFAULT_OUTPUT = Path("/tmp/osracer_real_measurement_pack")

GROUPS = {
    "mass_geometry": [
        "full_vehicle_mass_kg_with_battery_jetson_sensors",
        "front_rear_weight_distribution",
        "front_track_m",
        "tire_width_m",
    ],
    "steering": [
        "true_max_steering_rad_left_right",
        "steering_servo_pwm_min_center_max_or_protocol_units",
        "steering_response_time_s",
    ],
    "motor_battery_encoder": [
        "motor_kv_or_rated_rpm",
        "battery_voltage_s_count",
        "true_max_speed_mps",
        "minimum_stable_speed_mps",
        "throttle_deadband_and_response_delay_s",
        "encoder_ticks_per_revolution_and_mount_location",
    ],
    "imu": [
        "imu_model_rate_ranges_and_frame_alignment",
    ],
    "camera_calibration": [
        "camera_intrinsics_fx_fy_cx_cy_distortion",
    ],
    "extrinsics": [
        "camera_extrinsic_xyz_rpy_in_base_link",
        "lidar_extrinsic_xyz_rpy_in_base_link",
        "imu_extrinsic_xyz_rpy_in_base_link",
        "resolve_urdf_vs_static_tf_sensor_extrinsics",
    ],
    "auto_importable": [
        "serial_baud_rate_and_command_latency_s",
        "sensor_timestamp_sync_method",
    ],
}

METHODS = {
    "full_vehicle_mass_kg_with_battery_jetson_sensors": "Weigh the ready-to-run car with battery, Jetson, camera, lidar, and wiring installed.",
    "front_rear_weight_distribution": "Use two scales under front and rear axles, or calculate front/rear percentages from axle weights.",
    "front_track_m": "Measure front tire center to front tire center on the ground.",
    "tire_width_m": "Measure loaded tire width with calipers or tape while the car is on the ground.",
    "true_max_steering_rad_left_right": "Lift front wheels, command steering limits, and measure left/right wheel angle in radians.",
    "steering_servo_pwm_min_center_max_or_protocol_units": "Record firmware/servo min, center, max units from firmware config or a lifted sweep.",
    "steering_response_time_s": "Step steering command and measure delay/settling with video, encoder, or IMU timestamp evidence.",
    "motor_kv_or_rated_rpm": "Use motor datasheet, ESC config, or tachometer evidence.",
    "battery_voltage_s_count": "Record battery S count plus measured nominal, charged, and cutoff voltage.",
    "true_max_speed_mps": "Run a short straight low-risk test and compute speed from odom/video distance over time.",
    "minimum_stable_speed_mps": "Increase speed command until repeatable movement on ground; record the lowest stable value.",
    "throttle_deadband_and_response_delay_s": "Step throttle command and record deadband plus response delay from odom/tachometer evidence.",
    "encoder_ticks_per_revolution_and_mount_location": "Read firmware/config/datasheet and note the physical mount location.",
    "imu_model_rate_ranges_and_frame_alignment": "Record IMU part number, topic/config rate, accel/gyro ranges, and base_link frame alignment.",
    "camera_intrinsics_fx_fy_cx_cy_distortion": "Run checkerboard or AprilTag camera calibration at the deployed resolution and record fx, fy, cx, cy, image size, distortion model, and coefficients.",
    "camera_extrinsic_xyz_rpy_in_base_link": "Measure or calibrate base_link to camera_link as [x,y,z,roll,pitch,yaw] in meters/radians.",
    "lidar_extrinsic_xyz_rpy_in_base_link": "Measure base_link to laser as [x,y,z,roll,pitch,yaw] in meters/radians.",
    "imu_extrinsic_xyz_rpy_in_base_link": "Measure base_link to imu_link as [x,y,z,roll,pitch,yaw] in meters/radians.",
    "resolve_urdf_vs_static_tf_sensor_extrinsics": "State which measured extrinsics source was applied to URDF/static TF and why.",
    "serial_baud_rate_and_command_latency_s": "Prefer tools/jetson_measurement_session.sh and import-measurement-session.",
    "sensor_timestamp_sync_method": "Prefer tools/jetson_measurement_session.sh and import-measurement-session.",
}


def parse_args():
    parser = argparse.ArgumentParser(description="Create a field measurement pack for OSRacer real-car calibration.")
    parser.add_argument("--measurements", default=None, help="Existing measurement JSON to merge into the pack.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT), help="Output directory for the pack.")
    parser.add_argument("--overwrite", action="store_true", help="Replace output directory if it exists.")
    return parser.parse_args()


def load_json(path):
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def measurement_root(data):
    measurements = data.get("measurements", data)
    if not isinstance(measurements, dict):
        raise ValueError("measurement JSON must contain a measurements object")
    return measurements


def merge_existing(template, existing):
    result = json.loads(json.dumps(template))
    if not existing:
        return result
    target = measurement_root(result)
    source = measurement_root(existing)
    for key, value in source.items():
        if key in target:
            target[key].update(value if isinstance(value, dict) else {"value": value})
    if isinstance(existing, dict) and "collection" in existing:
        result["collection"] = existing["collection"]
    return result


def has_value(value):
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict)):
        return bool(value)
    return True


def entry_complete(entry):
    if not isinstance(entry, dict):
        return has_value(entry)
    return has_value(entry.get("value")) and bool(str(entry.get("source", "")).strip())


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def build_markdown(pack, measurements):
    lines = [
        "# OSRacer Field Measurement Pack",
        "",
        "Fill `real_car_measurements.field.json`, keep evidence in `evidence/`, then copy or rename it to `docs/real_car_measurements.json`.",
        "",
        "## Commands",
        "",
        "```bash",
        "cd /home/osrbot/Desktop/osracer/osracer",
        "tools/jetson_measurement_session.sh \\",
        "  --output-dir /tmp/osracer_measurement_session \\",
        "  --camera-topic /rgb/image_raw \\",
        "  --lidar-topic /scan \\",
        "  --imu-topic /imu_filter \\",
        "  --odom-topic /odometry/filtered \\",
        "  --camera-info-topic /camera_info",
        "cd /home/osrbot/Desktop/osracer/osracer_lab",
        f"MEASUREMENTS_FILE={pack}/real_car_measurements.field.json \\",
        "MEASUREMENT_SESSION_FILE=/tmp/osracer_measurement_session/measurement_session.json \\",
        "  scripts/validate_osracer_lab.sh import-measurement-session",
        f"MEASUREMENTS_FILE={pack}/real_car_measurements.field.json scripts/validate_osracer_lab.sh real-measurements",
        "```",
        "",
        "## Remaining Manual Measurements",
        "",
    ]
    for group, keys in GROUPS.items():
        lines.append(f"### {group}")
        lines.append("")
        for key in keys:
            entry = measurements[key]
            status = "complete" if entry_complete(entry) else "missing"
            lines.append(f"- [{status}] `{key}`")
            lines.append(f"  - format: {entry.get('expected_format', '')}")
            lines.append(f"  - method: {METHODS.get(key, 'Record measured value and evidence source.')}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_summary(measurements):
    complete = []
    remaining = []
    grouped_remaining = {}
    for group, keys in GROUPS.items():
        grouped_remaining[group] = []
        for key in keys:
            if entry_complete(measurements[key]):
                complete.append(key)
            else:
                remaining.append(key)
                grouped_remaining[group].append(key)
    return {
        "complete_count_by_value_source": len(complete),
        "remaining_count_by_value_source": len(remaining),
        "complete": complete,
        "remaining": remaining,
        "remaining_by_group": grouped_remaining,
    }


def main():
    args = parse_args()
    output_dir = Path(args.output_dir)
    if output_dir.exists():
        if not args.overwrite:
            raise FileExistsError(f"{output_dir} exists; pass --overwrite to replace it")
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    (output_dir / "evidence").mkdir()

    template = load_json(TEMPLATE_PATH)
    existing = load_json(args.measurements) if args.measurements else None
    pack_json = merge_existing(template, existing)
    measurements = measurement_root(pack_json)
    write_json(output_dir / "real_car_measurements.field.json", pack_json)
    (output_dir / "README.md").write_text(build_markdown(output_dir, measurements), encoding="utf-8")
    write_json(output_dir / "measurement_gap_summary.json", build_summary(measurements))
    print(f"wrote {output_dir}")
    print(f"field_json: {output_dir / 'real_car_measurements.field.json'}")
    print(f"readme: {output_dir / 'README.md'}")
    print(f"summary: {output_dir / 'measurement_gap_summary.json'}")


if __name__ == "__main__":
    raise SystemExit(main())
