#!/usr/bin/env python3
"""Validate real-car measurement JSON for OSRacer sim2real readiness."""

import argparse
import json
import re
from pathlib import Path
import importlib.util

REPO_ROOT = Path(__file__).resolve().parents[1]
HARDWARE_PARAMS_PATH = REPO_ROOT / "source" / "osracer_lab_assets" / "osracer_lab_assets" / "hardware_params.py"
_hardware_spec = importlib.util.spec_from_file_location("osracer_hardware_params", HARDWARE_PARAMS_PATH)
_hardware_module = importlib.util.module_from_spec(_hardware_spec)
_hardware_spec.loader.exec_module(_hardware_module)
hardware_summary = _hardware_module.hardware_summary

REQUIRED_KEYS = (
    "full_vehicle_mass_kg_with_battery_jetson_sensors",
    "front_track_m",
    "tire_width_m",
    "front_rear_weight_distribution",
    "true_max_steering_rad_left_right",
    "steering_servo_pwm_min_center_max_or_protocol_units",
    "steering_response_time_s",
    "motor_kv_or_rated_rpm",
    "battery_voltage_s_count",
    "true_max_speed_mps",
    "minimum_stable_speed_mps",
    "throttle_deadband_and_response_delay_s",
    "encoder_ticks_per_revolution_and_mount_location",
    "imu_model_rate_ranges_and_frame_alignment",
    "camera_intrinsics_fx_fy_cx_cy_distortion",
    "camera_extrinsic_xyz_rpy_in_base_link",
    "lidar_extrinsic_xyz_rpy_in_base_link",
    "imu_extrinsic_xyz_rpy_in_base_link",
    "serial_baud_rate_and_command_latency_s",
    "sensor_timestamp_sync_method",
    "resolve_urdf_vs_static_tf_sensor_extrinsics",
)


def parse_args():
    parser = argparse.ArgumentParser(description="Validate OSRacer real-car measurement JSON.")
    parser.add_argument("measurements", help="Path to docs/real_car_measurements.json")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    return parser.parse_args()


def load_measurements(path):
    with Path(path).open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("measurement JSON root must be an object")
    measurements = data.get("measurements", data)
    if not isinstance(measurements, dict):
        raise ValueError("measurement JSON must contain an object at 'measurements'")
    return measurements


def entry_value(entry):
    if isinstance(entry, dict):
        return entry.get("value")
    return entry


def entry_source(entry):
    if isinstance(entry, dict):
        return entry.get("source")
    return None


def has_text(value):
    return isinstance(value, str) and bool(value.strip())


def has_source(entry):
    return has_text(entry_source(entry))


def number(value, *, min_value=None, max_value=None):
    if isinstance(value, bool):
        raise ValueError("must be a number, got bool")
    if isinstance(value, (int, float)):
        result = float(value)
    elif isinstance(value, str):
        match = re.search(r"[-+]?\d+(?:\.\d+)?", value.strip())
        if not match:
            raise ValueError("must contain a numeric value")
        result = float(match.group(0))
    else:
        raise ValueError("must be a number")
    if min_value is not None and result < min_value:
        raise ValueError(f"must be >= {min_value}")
    if max_value is not None and result > max_value:
        raise ValueError(f"must be <= {max_value}")
    return result


def numeric_sequence(value, count, label, *, min_value=None, max_value=None):
    if isinstance(value, dict):
        if "xyz_rpy" in value:
            value = value["xyz_rpy"]
        elif "values" in value:
            value = value["values"]
        else:
            value = list(value.values())
    if isinstance(value, str):
        parts = [p for p in re.split(r"[\s,]+", value.strip()) if p]
    elif isinstance(value, (list, tuple)):
        parts = list(value)
    else:
        raise ValueError(f"{label} must be a list or whitespace/comma-separated string")
    if len(parts) != count:
        raise ValueError(f"{label} must contain {count} numbers, got {len(parts)}")
    return [number(v, min_value=min_value, max_value=max_value) for v in parts]


def validate_positive_m(value, name):
    number(value, min_value=0.001, max_value=5.0)


def validate_positive_s(value, name):
    number(value, min_value=0.0, max_value=10.0)


def validate_speed(value, name):
    number(value, min_value=0.0, max_value=30.0)


def validate_weight_distribution(value, name):
    if isinstance(value, dict):
        if "front_percent" in value and "rear_percent" in value:
            front = number(value["front_percent"], min_value=0.0, max_value=100.0)
            rear = number(value["rear_percent"], min_value=0.0, max_value=100.0)
            if abs(front + rear - 100.0) > 2.0:
                raise ValueError("front_percent + rear_percent should be about 100")
            return
        if "front_kg" in value and "rear_kg" in value:
            number(value["front_kg"], min_value=0.0, max_value=20.0)
            number(value["rear_kg"], min_value=0.0, max_value=20.0)
            return
    numeric_sequence(value, 2, name, min_value=0.0, max_value=100.0)


def validate_steering_limits(value, name):
    if isinstance(value, dict):
        values = [value.get("left_rad"), value.get("right_rad")]
    else:
        values = numeric_sequence(value, 2, name, min_value=0.0, max_value=1.5)
        return
    numeric_sequence(values, 2, name, min_value=0.0, max_value=1.5)


def validate_servo_units(value, name):
    if isinstance(value, dict):
        values = [value.get("min"), value.get("center"), value.get("max")]
    else:
        values = numeric_sequence(value, 3, name)
        if not values[0] < values[1] < values[2]:
            raise ValueError("servo min/center/max must be increasing")
        return
    values = numeric_sequence(values, 3, name)
    if not values[0] < values[1] < values[2]:
        raise ValueError("servo min/center/max must be increasing")


def validate_motor(value, name):
    if isinstance(value, dict):
        if "kv" in value:
            number(value["kv"], min_value=1.0, max_value=20000.0)
            return
        if "rated_rpm" in value:
            number(value["rated_rpm"], min_value=1.0, max_value=200000.0)
            return
    number(value, min_value=1.0, max_value=200000.0)


def validate_battery(value, name):
    if not isinstance(value, dict):
        number(value, min_value=1.0, max_value=50.0)
        return
    if "s_count" not in value:
        raise ValueError("battery value must include s_count")
    number(value["s_count"], min_value=1.0, max_value=12.0)
    for key in ("nominal_v", "charged_v", "cutoff_v"):
        if key in value:
            number(value[key], min_value=1.0, max_value=60.0)


def validate_throttle(value, name):
    if not isinstance(value, dict):
        numeric_sequence(value, 2, name, min_value=0.0)
        return
    if "response_delay_s" not in value:
        raise ValueError("throttle value must include response_delay_s")
    number(value["response_delay_s"], min_value=0.0, max_value=10.0)
    if "deadband" in value:
        number(value["deadband"], min_value=0.0)


def validate_encoder(value, name):
    if not isinstance(value, dict):
        number(value, min_value=1.0, max_value=1000000.0)
        return
    if "ticks_per_revolution" not in value:
        raise ValueError("encoder value must include ticks_per_revolution")
    number(value["ticks_per_revolution"], min_value=1.0, max_value=1000000.0)
    if not has_text(str(value.get("mount_location", ""))):
        raise ValueError("encoder value must include mount_location")


def validate_imu(value, name):
    if not isinstance(value, dict):
        raise ValueError("IMU value must be an object with model, rate_hz, ranges, and frame_alignment")
    if not has_text(str(value.get("model", ""))):
        raise ValueError("IMU value must include model")
    if "rate_hz" not in value:
        raise ValueError("IMU value must include rate_hz")
    number(value["rate_hz"], min_value=1.0, max_value=2000.0)
    if "accel_range_g" not in value:
        raise ValueError("IMU value must include accel_range_g")
    number(value["accel_range_g"], min_value=0.1, max_value=200.0)
    if "gyro_range_dps" not in value:
        raise ValueError("IMU value must include gyro_range_dps")
    number(value["gyro_range_dps"], min_value=1.0, max_value=100000.0)
    if not has_text(str(value.get("frame_alignment", ""))):
        raise ValueError("IMU value must include frame_alignment")


def validate_extrinsic(value, name):
    numeric_sequence(value, 6, name)


def validate_camera_intrinsics(value, name):
    if not isinstance(value, dict):
        raise ValueError("camera intrinsics value must be an object")
    for key in ("fx", "fy", "cx", "cy"):
        if key not in value:
            raise ValueError(f"camera intrinsics value must include {key}")
        number(value[key], min_value=0.001, max_value=10000.0)
    for key in ("width_px", "height_px"):
        if key not in value:
            raise ValueError(f"camera intrinsics value must include {key}")
        number(value[key], min_value=1.0, max_value=10000.0)
    if not has_text(str(value.get("distortion_model", ""))):
        raise ValueError("camera intrinsics value must include distortion_model")
    coeffs = value.get("distortion_coeffs")
    if not isinstance(coeffs, (list, tuple)):
        raise ValueError("camera intrinsics value must include distortion_coeffs list")
    for coeff in coeffs:
        number(coeff, min_value=-10.0, max_value=10.0)


def validate_serial(value, name):
    if not isinstance(value, dict):
        numeric_sequence(value, 2, name, min_value=0.0)
        return
    if "baud_rate" not in value:
        raise ValueError("serial value must include baud_rate")
    number(value["baud_rate"], min_value=9600.0, max_value=10000000.0)
    if "command_latency_s" not in value:
        raise ValueError("serial value must include command_latency_s")
    number(value["command_latency_s"], min_value=0.0, max_value=5.0)


def validate_description(value, name):
    if not has_text(value) or len(value.strip()) < 8:
        raise ValueError("must be a descriptive string")


VALIDATORS = {
    "full_vehicle_mass_kg_with_battery_jetson_sensors": validate_positive_m,
    "front_track_m": validate_positive_m,
    "tire_width_m": validate_positive_m,
    "front_rear_weight_distribution": validate_weight_distribution,
    "true_max_steering_rad_left_right": validate_steering_limits,
    "steering_servo_pwm_min_center_max_or_protocol_units": validate_servo_units,
    "steering_response_time_s": validate_positive_s,
    "motor_kv_or_rated_rpm": validate_motor,
    "battery_voltage_s_count": validate_battery,
    "true_max_speed_mps": validate_speed,
    "minimum_stable_speed_mps": validate_speed,
    "throttle_deadband_and_response_delay_s": validate_throttle,
    "encoder_ticks_per_revolution_and_mount_location": validate_encoder,
    "imu_model_rate_ranges_and_frame_alignment": validate_imu,
    "camera_intrinsics_fx_fy_cx_cy_distortion": validate_camera_intrinsics,
    "camera_extrinsic_xyz_rpy_in_base_link": validate_extrinsic,
    "lidar_extrinsic_xyz_rpy_in_base_link": validate_extrinsic,
    "imu_extrinsic_xyz_rpy_in_base_link": validate_extrinsic,
    "serial_baud_rate_and_command_latency_s": validate_serial,
    "sensor_timestamp_sync_method": validate_description,
    "resolve_urdf_vs_static_tf_sensor_extrinsics": validate_description,
}



def get_measurement_value(measurements, name):
    if name not in measurements:
        return None
    return entry_value(measurements[name])


def steering_pair(value):
    if isinstance(value, dict):
        values = [value.get("left_rad"), value.get("right_rad")]
    else:
        values = value
    return numeric_sequence(values, 2, "true_max_steering_rad_left_right", min_value=0.0, max_value=1.5)


def serial_value(value):
    if isinstance(value, dict):
        return {
            "baud_rate": number(value.get("baud_rate"), min_value=9600.0, max_value=10000000.0),
            "command_latency_s": number(value.get("command_latency_s"), min_value=0.0, max_value=5.0),
        }
    baud, latency = numeric_sequence(value, 2, "serial_baud_rate_and_command_latency_s", min_value=0.0)
    return {"baud_rate": baud, "command_latency_s": latency}


def add_consistency_error(invalid, name, error):
    invalid.append({"name": name, "error": error})


def validate_consistency(measurements, complete, invalid):
    complete_set = set(complete)
    params = hardware_summary()
    chassis = params["chassis"]
    runtime = params["real_runtime"]
    camera_runtime = params["camera_ar0234"]["ros_runtime"]

    if {"minimum_stable_speed_mps", "true_max_speed_mps"}.issubset(complete_set):
        minimum = number(get_measurement_value(measurements, "minimum_stable_speed_mps"), min_value=0.0, max_value=30.0)
        maximum = number(get_measurement_value(measurements, "true_max_speed_mps"), min_value=0.0, max_value=30.0)
        if minimum > maximum:
            add_consistency_error(invalid, "minimum_stable_speed_mps", "minimum stable speed must be <= true max speed")
        initial_limit = float(chassis["initial_real_test_max_speed_mps"])
        if minimum > initial_limit:
            add_consistency_error(
                invalid,
                "minimum_stable_speed_mps",
                f"minimum stable speed must be <= initial real-test speed limit {initial_limit}",
            )

    if "true_max_steering_rad_left_right" in complete_set:
        left, right = steering_pair(get_measurement_value(measurements, "true_max_steering_rad_left_right"))
        if min(left, right) <= 0.0:
            add_consistency_error(invalid, "true_max_steering_rad_left_right", "left/right steering limits must be positive")
        elif abs(left - right) / max(left, right) > 0.25:
            add_consistency_error(invalid, "true_max_steering_rad_left_right", "left/right steering limits differ by more than 25%")

    if "battery_voltage_s_count" in complete_set:
        value = get_measurement_value(measurements, "battery_voltage_s_count")
        if isinstance(value, dict) and all(key in value for key in ("charged_v", "nominal_v", "cutoff_v")):
            charged = number(value["charged_v"], min_value=1.0, max_value=60.0)
            nominal = number(value["nominal_v"], min_value=1.0, max_value=60.0)
            cutoff = number(value["cutoff_v"], min_value=1.0, max_value=60.0)
            if not charged >= nominal >= cutoff:
                add_consistency_error(invalid, "battery_voltage_s_count", "battery voltages must satisfy charged_v >= nominal_v >= cutoff_v")

    if "camera_intrinsics_fx_fy_cx_cy_distortion" in complete_set:
        value = get_measurement_value(measurements, "camera_intrinsics_fx_fy_cx_cy_distortion")
        expected_width, expected_height = camera_runtime["configured_resolution_px"]
        width = int(number(value.get("width_px"), min_value=1.0, max_value=10000.0))
        height = int(number(value.get("height_px"), min_value=1.0, max_value=10000.0))
        if (width, height) != (expected_width, expected_height):
            add_consistency_error(
                invalid,
                "camera_intrinsics_fx_fy_cx_cy_distortion",
                f"camera calibration resolution {width}x{height} must match runtime {expected_width}x{expected_height}",
            )

    if "serial_baud_rate_and_command_latency_s" in complete_set:
        value = serial_value(get_measurement_value(measurements, "serial_baud_rate_and_command_latency_s"))
        expected_baud = float(runtime["serial_baud"])
        if value["baud_rate"] != expected_baud:
            add_consistency_error(
                invalid,
                "serial_baud_rate_and_command_latency_s",
                f"baud_rate must match runtime serial_baud {int(expected_baud)}",
            )
        if value["command_latency_s"] > 0.05:
            add_consistency_error(invalid, "serial_baud_rate_and_command_latency_s", "command latency must be <= 0.05 s")


def has_value(value):
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict)):
        return bool(value)
    return True


def validate_measurements(measurements, required=REQUIRED_KEYS):
    complete = []
    missing = []
    incomplete = []
    invalid = []
    for name in required:
        if name not in measurements:
            missing.append(name)
            continue
        entry = measurements[name]
        value = entry_value(entry)
        if not has_value(value) or not has_source(entry):
            incomplete.append(name)
            continue
        try:
            VALIDATORS[name](value, name)
        except (TypeError, ValueError) as exc:
            invalid.append({"name": name, "error": str(exc)})
        else:
            complete.append(name)
    validate_consistency(measurements, complete, invalid)
    return {
        "complete": complete,
        "missing": missing,
        "incomplete": incomplete,
        "invalid": invalid,
    }


def main():
    args = parse_args()
    measurements = load_measurements(args.measurements)
    report = validate_measurements(measurements)
    report["measurements_path"] = str(Path(args.measurements).resolve())
    report["valid"] = not (report["missing"] or report["incomplete"] or report["invalid"])
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"real_car_measurements: {'pass' if report['valid'] else 'fail'}")
        print(f"complete: {len(report['complete'])}/{len(REQUIRED_KEYS)}")
        for key in ("missing", "incomplete"):
            if report[key]:
                print(f"{key}:")
                for name in report[key]:
                    print(f"  - {name}")
        if report["invalid"]:
            print("invalid:")
            for item in report["invalid"]:
                print(f"  - {item['name']}: {item['error']}")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
