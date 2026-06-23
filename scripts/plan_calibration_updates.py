#!/usr/bin/env python3
"""Plan repo updates from measured OSRacer real-car parameters without writing files."""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

from validate_real_measurements import validate_measurements  # noqa: E402

AUTO_APPLY = {
    "camera_extrinsic_xyz_rpy_in_base_link": [
        "osracer/osracer_description/urdf/osracer.urdf camera_joint origin",
        "osracer/osracer_description/launch/robot_description_tf.launch.py base_link2camera",
        "osracer_lab_assets.hardware_params camera extrinsic tuples",
    ],
    "lidar_extrinsic_xyz_rpy_in_base_link": [
        "osracer/osracer_description/urdf/osracer.urdf laser_joint origin",
        "osracer/osracer_description/launch/robot_description_tf.launch.py base_link2laser",
        "osracer_lab_assets.hardware_params lidar extrinsic tuples",
    ],
    "imu_extrinsic_xyz_rpy_in_base_link": [
        "osracer/osracer_description/urdf/osracer.urdf imu_joint origin",
        "osracer/osracer_description/launch/robot_description_tf.launch.py base_link2imu",
        "osracer_lab_assets.hardware_params imu extrinsic tuples",
    ],
}

REVIEW_APPLY = {
    "full_vehicle_mass_kg_with_battery_jetson_sensors": [
        "IsaacLab/MuJoCo body mass after deciding chassis vs payload distribution",
    ],
    "front_track_m": ["vehicle geometry and wheel collision/contact layout"],
    "tire_width_m": ["wheel collision geometry and contact model"],
    "front_rear_weight_distribution": ["body inertial distribution after component layout review"],
    "true_max_steering_rad_left_right": ["policy action clamp and ROS bridge clamp after left/right asymmetry decision"],
    "steering_servo_pwm_min_center_max_or_protocol_units": ["firmware/host calibration notes; do not write without osrcore contract review"],
    "steering_response_time_s": ["actuator delay model in IsaacLab/MuJoCo"],
    "motor_kv_or_rated_rpm": ["motor model metadata; needs ESC/gearing context"],
    "battery_voltage_s_count": ["Jetson/runtime safety notes and motor model voltage envelope"],
    "true_max_speed_mps": ["policy speed clamp after safety review"],
    "minimum_stable_speed_mps": ["first-drive command lower bound and low-speed model"],
    "throttle_deadband_and_response_delay_s": ["actuator deadband/delay model"],
    "encoder_ticks_per_revolution_and_mount_location": ["odom model and firmware/host consistency checks"],
    "imu_model_rate_ranges_and_frame_alignment": ["IMU noise/range model and frame convention docs"],
    "serial_baud_rate_and_command_latency_s": ["runtime timing notes; already importable, not a geometry write"],
    "sensor_timestamp_sync_method": ["replay timing assumptions; already importable, not a geometry write"],
    "resolve_urdf_vs_static_tf_sensor_extrinsics": ["strict extrinsics gate after measured transforms are applied"],
}


def parse_args():
    parser = argparse.ArgumentParser(description="Plan measured-parameter updates before writing repo files.")
    parser.add_argument("--measurements", required=True, help="Path to docs/real_car_measurements.json")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    return parser.parse_args()


def load_measurements(path):
    with Path(path).open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("measurement JSON root must be an object")
    measurements = data.get("measurements", data)
    if not isinstance(measurements, dict):
        raise ValueError("measurement JSON must contain a measurements object")
    return measurements


def build_plan(measurements):
    report = validate_measurements(measurements)
    complete = set(report["complete"])
    auto_ready = [key for key in AUTO_APPLY if key in complete]
    review_ready = [key for key in REVIEW_APPLY if key in complete and key not in AUTO_APPLY]
    blocked_auto = [key for key in AUTO_APPLY if key not in complete]
    return {
        "valid_measurement_count": len(report["complete"]),
        "auto_apply_ready": [
            {"measurement": key, "writes": AUTO_APPLY[key]} for key in auto_ready
        ],
        "review_apply_ready": [
            {"measurement": key, "requires_review_before_writing": REVIEW_APPLY[key]} for key in review_ready
        ],
        "blocked_auto_apply": [
            {"measurement": key, "reason": "missing, incomplete, or invalid measurement"} for key in blocked_auto
        ],
        "missing": report["missing"],
        "incomplete": report["incomplete"],
        "invalid": report["invalid"],
        "next_commands": [
            "MEASUREMENTS_FILE=docs/real_car_measurements.json scripts/validate_osracer_lab.sh real-measurements",
            "MEASUREMENTS_FILE=docs/real_car_measurements.json scripts/validate_osracer_lab.sh sensor-extrinsics-check",
            "MEASUREMENTS_FILE=docs/real_car_measurements.json scripts/validate_osracer_lab.sh sensor-extrinsics-write",
            "scripts/validate_osracer_lab.sh runtime-contract",
            "python3 scripts/check_runtime_contract.py --osracer-root /home/osrbot/Desktop/osracer/osracer --strict-extrinsics",
        ],
    }


def print_text(plan):
    print(f"calibration_update_plan: {plan['valid_measurement_count']}/20 valid measurement item(s)")
    print("auto_apply_ready:")
    for item in plan["auto_apply_ready"]:
        print(f"  - {item['measurement']}")
        for target in item["writes"]:
            print(f"    -> {target}")
    if not plan["auto_apply_ready"]:
        print("  - none")
    print("review_apply_ready:")
    for item in plan["review_apply_ready"]:
        print(f"  - {item['measurement']}")
        for target in item["requires_review_before_writing"]:
            print(f"    -> {target}")
    if not plan["review_apply_ready"]:
        print("  - none")
    print("blocked_auto_apply:")
    for item in plan["blocked_auto_apply"]:
        print(f"  - {item['measurement']}: {item['reason']}")
    if plan["invalid"]:
        print("invalid_measurements:")
        for item in plan["invalid"]:
            print(f"  - {item['name']}: {item['error']}")


def main():
    args = parse_args()
    plan = build_plan(load_measurements(args.measurements))
    if args.json:
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        print_text(plan)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
