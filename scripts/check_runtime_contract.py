#!/usr/bin/env python3
"""Check that osracer_lab hardware parameters match the upper-computer repo."""

import argparse
import ast
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ASSETS_SRC = REPO_ROOT / "source" / "osracer_lab_assets"
if str(ASSETS_SRC) not in sys.path:
    sys.path.insert(0, str(ASSETS_SRC))

from hardware_params_loader import hardware_summary


def parse_args():
    parser = argparse.ArgumentParser(description="Check OSRacer runtime contract drift.")
    parser.add_argument(
        "--osracer-root",
        default=str(REPO_ROOT.parent / "osracer"),
        help="Path to the upper-computer osracer repo",
    )
    parser.add_argument("--strict-extrinsics", action="store_true", help="Fail on URDF vs static TF disagreement")
    return parser.parse_args()


def read_text(path):
    if not path.is_file():
        raise FileNotFoundError(path)
    return path.read_text(errors="replace")


def find_default_launch_value(text, argument_name):
    pattern = re.compile(
        r"DeclareLaunchArgument\(\s*['\"]"
        + re.escape(argument_name)
        + r"['\"].*?default_value\s*=\s*([^,\n)]+)",
        re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        raise ValueError(f"Launch argument not found: {argument_name}")
    expr = match.group(1).strip()
    if expr.startswith("TextSubstitution"):
        inner = re.search(r"text\s*=\s*(['\"].*?['\"])", expr)
        if inner:
            return ast.literal_eval(inner.group(1))
    return ast.literal_eval(expr)


def find_declared_parameter_default(text, parameter_name):
    pattern = re.compile(
        r"declare_parameter\(\s*['\"]"
        + re.escape(parameter_name)
        + r"['\"]\s*,\s*([^)]+)\)",
        re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        raise ValueError(f"Declared parameter not found: {parameter_name}")
    return ast.literal_eval(match.group(1).strip())


def find_camera_param(text, key):
    pattern = re.compile(r"['\"]" + re.escape(key) + r"['\"]\s*:\s*([^,\n}]+)")
    match = pattern.search(text)
    if not match:
        raise ValueError(f"Camera parameter not found: {key}")
    return ast.literal_eval(match.group(1).strip())


def parse_urdf_extrinsics(urdf_path):
    root = ET.parse(urdf_path).getroot()
    result = {}
    for joint in root.findall("joint"):
        parent = joint.find("parent")
        child = joint.find("child")
        origin = joint.find("origin")
        if parent is None or child is None or origin is None:
            continue
        if parent.attrib.get("link") != "base_link":
            continue
        child_name = child.attrib.get("link")
        if child_name not in {"camera_link", "laser", "imu_link"}:
            continue
        xyz = tuple(float(v) for v in origin.attrib.get("xyz", "0 0 0").split())
        rpy = tuple(float(v) for v in origin.attrib.get("rpy", "0 0 0").split())
        result[child_name] = xyz + rpy
    return result


def parse_static_tf_extrinsics(text):
    frames = {}
    current = None
    values = {}
    for line in text.splitlines():
        child_match = re.search(r'"--child-frame-id",\s*"([^"]+)"', line)
        if child_match:
            current = child_match.group(1)
            frames[current] = values
            values = {}
        key_match = re.search(r'"--(x|y|z|roll|pitch|yaw)",\s*"([^"]+)"', line)
        if key_match:
            values[key_match.group(1)] = float(key_match.group(2))
    return {
        name: (
            value.get("x", 0.0),
            value.get("y", 0.0),
            value.get("z", 0.0),
            value.get("roll", 0.0),
            value.get("pitch", 0.0),
            value.get("yaw", 0.0),
        )
        for name, value in frames.items()
        if name in {"camera_link", "laser", "imu_link", "base_link"}
    }


def nearly_equal_tuple(left, right, tol=1e-9):
    return len(left) == len(right) and all(abs(a - b) <= tol for a, b in zip(left, right))


def check_equal(name, actual, expected, failures):
    if actual == expected:
        print(f"[OK] {name}: {actual}")
    else:
        print(f"[FAIL] {name}: actual={actual!r} expected={expected!r}")
        failures.append(name)


def check_float(name, actual, expected, failures, tol=1e-9):
    if abs(float(actual) - float(expected)) <= tol:
        print(f"[OK] {name}: {actual}")
    else:
        print(f"[FAIL] {name}: actual={actual!r} expected={expected!r}")
        failures.append(name)


def main():
    args = parse_args()
    osracer_root = Path(args.osracer_root).resolve()
    params = hardware_summary()
    runtime = params["real_runtime"]
    chassis = params["chassis"]
    camera = params["camera_ar0234"]["ros_runtime"]
    extrinsics = params["sensor_extrinsics"]
    failures = []
    warnings = []

    chassis_launch = read_text(osracer_root / "osracer_bringup/launch/chassis_ackermann.launch.py")
    chassis_bridge = read_text(osracer_root / "osracer_bringup/script/chassis_ackermann.py")
    camera_launch = read_text(osracer_root / "osracer_bringup/launch/usb_cam.launch.py")
    static_tf_launch = read_text(osracer_root / "osracer_description/launch/robot_description_tf.launch.py")
    preflight_tool = read_text(osracer_root / "tools/jetson_preflight.sh")
    sensor_preflight_tool = read_text(osracer_root / "tools/jetson_sensor_preflight.sh")
    measurement_session_tool = read_text(osracer_root / "tools/jetson_measurement_session.sh")
    readiness_tool = read_text(osracer_root / "tools/real_car_readiness_check.sh")
    urdf_path = osracer_root / "osracer_description/urdf/osracer.urdf"

    check_equal("serial_port", find_default_launch_value(chassis_launch, "port_name"), runtime["serial_port"], failures)
    check_equal("serial_baud", int(find_default_launch_value(chassis_launch, "baud_rate")), runtime["serial_baud"], failures)
    check_float("wheelbase", find_default_launch_value(chassis_launch, "wheelbase"), chassis["wheelbase_m"], failures)
    check_float(
        "bridge_max_steering_deg",
        find_default_launch_value(chassis_launch, "max_steering_angle_deg"),
        30.0,
        failures,
    )
    check_float(
        "cmd_watchdog_timeout_s",
        find_default_launch_value(chassis_launch, "cmd_watchdog_timeout_s"),
        runtime["command_watchdog_timeout_s"],
        failures,
    )
    check_float(
        "firmware_version_timeout_s",
        find_declared_parameter_default(chassis_bridge, "firmware_version_timeout_s"),
        runtime["firmware_version_timeout_s"],
        failures,
    )
    check_equal("queries_fw_version_on_startup", 'serial_conn.write(b"fw version\\n")' in chassis_bridge, True, failures)
    check_equal("logs_projectver_on_startup", "OSRCORE ProjectVer:" in chassis_bridge, True, failures)
    check_equal("forces_stream_sync_on_startup", 'self.write_serial("stream sync\\n")' in chassis_bridge, True, failures)
    check_equal("requests_initial_sync_frame", 'self.write_serial("s\\n")' in chassis_bridge, True, failures)
    check_equal("camera_device", find_camera_param(camera_launch, "video_device"), camera["device"], failures)
    check_equal(
        "camera_resolution",
        (find_camera_param(camera_launch, "image_width"), find_camera_param(camera_launch, "image_height")),
        camera["configured_resolution_px"],
        failures,
    )
    check_float("camera_fps", find_camera_param(camera_launch, "framerate"), camera["configured_fps"], failures)
    check_equal("camera_pixel_format", find_camera_param(camera_launch, "pixel_format"), camera["pixel_format"], failures)
    ros_default = f'ROS_DISTRO_NAME="${{ROS_DISTRO:-{runtime["ros_distro"]}}}"'
    for name, text in (
        ("jetson_preflight_ros_distro", preflight_tool),
        ("jetson_sensor_preflight_ros_distro", sensor_preflight_tool),
        ("jetson_measurement_session_ros_distro", measurement_session_tool),
        ("real_car_readiness_ros_distro", readiness_tool),
    ):
        check_equal(name, ros_default in text, True, failures)

    urdf = parse_urdf_extrinsics(urdf_path)
    static_tf = parse_static_tf_extrinsics(static_tf_launch)
    expected_pairs = {
        "camera_link": (
            extrinsics["urdf_base_link_to_camera_link_xyz_rpy"],
            extrinsics["static_tf_base_link_to_camera_link_xyz_rpy"],
        ),
        "laser": (
            extrinsics["urdf_base_link_to_laser_xyz_rpy"],
            extrinsics["static_tf_base_link_to_laser_xyz_rpy"],
        ),
        "imu_link": (
            extrinsics["urdf_base_link_to_imu_link_xyz_rpy"],
            extrinsics["static_tf_base_link_to_imu_link_xyz_rpy"],
        ),
    }
    for frame, (expected_urdf, expected_static) in expected_pairs.items():
        if not nearly_equal_tuple(urdf.get(frame, ()), expected_urdf):
            failures.append(f"urdf_extrinsic_{frame}")
            print(f"[FAIL] urdf_extrinsic_{frame}: actual={urdf.get(frame)!r} expected={expected_urdf!r}")
        else:
            print(f"[OK] urdf_extrinsic_{frame}: {expected_urdf}")
        if not nearly_equal_tuple(static_tf.get(frame, ()), expected_static):
            failures.append(f"static_tf_extrinsic_{frame}")
            print(f"[FAIL] static_tf_extrinsic_{frame}: actual={static_tf.get(frame)!r} expected={expected_static!r}")
        else:
            print(f"[OK] static_tf_extrinsic_{frame}: {expected_static}")
        if not nearly_equal_tuple(expected_urdf, expected_static):
            warnings.append(f"{frame}: URDF and static TF differ")

    for warning in warnings:
        print(f"[WARN] {warning}")
    if args.strict_extrinsics and warnings:
        failures.extend(warnings)

    if failures:
        print(f"[FAIL] runtime contract check failed: {len(failures)} issue(s)")
        return 1
    print("[OK] runtime contract check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
