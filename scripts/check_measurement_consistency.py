#!/usr/bin/env python3
"""Self-check real-car measurement cross-field consistency rules."""

import copy
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts" / "validate_real_measurements.py"
spec = importlib.util.spec_from_file_location("validate_real_measurements", VALIDATOR_PATH)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def entry(value):
    return {"value": value, "source": "measurement consistency self-check"}


BASE_VALUES = {
    "full_vehicle_mass_kg_with_battery_jetson_sensors": 3.2,
    "front_track_m": 0.22,
    "tire_width_m": 0.035,
    "front_rear_weight_distribution": {"front_percent": 50, "rear_percent": 50},
    "true_max_steering_rad_left_right": {"left_rad": 0.5, "right_rad": 0.48},
    "steering_servo_pwm_min_center_max_or_protocol_units": [1000, 1500, 2000],
    "steering_response_time_s": 0.12,
    "motor_kv_or_rated_rpm": {"rated_rpm": 12000},
    "battery_voltage_s_count": {"s_count": 3, "charged_v": 12.6, "nominal_v": 11.1, "cutoff_v": 9.6},
    "true_max_speed_mps": 4.0,
    "minimum_stable_speed_mps": 0.2,
    "throttle_deadband_and_response_delay_s": {"deadband": 0.04, "response_delay_s": 0.08},
    "encoder_ticks_per_revolution_and_mount_location": {"ticks_per_revolution": 1024, "mount_location": "rear axle"},
    "imu_model_rate_ranges_and_frame_alignment": {
        "model": "osrcore imu",
        "rate_hz": 100,
        "accel_range_g": 16,
        "gyro_range_dps": 2000,
        "frame_alignment": "base_link aligned",
    },
    "camera_intrinsics_fx_fy_cx_cy_distortion": {
        "fx": 300,
        "fy": 300,
        "cx": 320,
        "cy": 240,
        "width_px": 640,
        "height_px": 480,
        "distortion_model": "plumb_bob",
        "distortion_coeffs": [0, 0, 0, 0, 0],
    },
    "camera_extrinsic_xyz_rpy_in_base_link": [0.1, 0, 0.2, 0, 0, 0],
    "lidar_extrinsic_xyz_rpy_in_base_link": [0.05, 0, 0.15, 0, 0, 0],
    "imu_extrinsic_xyz_rpy_in_base_link": [0, 0, 0.05, 0, 0, 0],
    "serial_baud_rate_and_command_latency_s": {"baud_rate": 460800, "command_latency_s": 0.02},
    "sensor_timestamp_sync_method": "ROS host clock with measured topic timestamps",
    "resolve_urdf_vs_static_tf_sensor_extrinsics": "URDF and static TF reconciled to measured extrinsics",
}


def measurements(values):
    return {key: entry(value) for key, value in values.items()}


def assert_valid(values):
    report = validator.validate_measurements(measurements(values))
    if report["missing"] or report["incomplete"] or report["invalid"]:
        raise AssertionError(report)


def assert_invalid(values, name):
    report = validator.validate_measurements(measurements(values))
    if not any(item["name"] == name for item in report["invalid"]):
        raise AssertionError(report)


def main():
    assert_valid(BASE_VALUES)

    case = copy.deepcopy(BASE_VALUES)
    case["minimum_stable_speed_mps"] = 0.4
    assert_invalid(case, "minimum_stable_speed_mps")

    case = copy.deepcopy(BASE_VALUES)
    case["camera_intrinsics_fx_fy_cx_cy_distortion"]["width_px"] = 1920
    case["camera_intrinsics_fx_fy_cx_cy_distortion"]["height_px"] = 1200
    assert_invalid(case, "camera_intrinsics_fx_fy_cx_cy_distortion")

    case = copy.deepcopy(BASE_VALUES)
    case["serial_baud_rate_and_command_latency_s"]["baud_rate"] = 115200
    assert_invalid(case, "serial_baud_rate_and_command_latency_s")

    case = copy.deepcopy(BASE_VALUES)
    case["true_max_steering_rad_left_right"] = {"left_rad": 0.6, "right_rad": 0.3}
    assert_invalid(case, "true_max_steering_rad_left_right")

    case = copy.deepcopy(BASE_VALUES)
    case["battery_voltage_s_count"] = {"s_count": 3, "charged_v": 10.0, "nominal_v": 11.1, "cutoff_v": 9.6}
    assert_invalid(case, "battery_voltage_s_count")

    print("measurement consistency checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
