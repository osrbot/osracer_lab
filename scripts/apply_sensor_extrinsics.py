#!/usr/bin/env python3
"""Check or apply measured OSRacer sensor extrinsics."""

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ASSETS_SRC = REPO_ROOT / "source" / "osracer_lab_assets"
if str(ASSETS_SRC) not in sys.path:
    sys.path.insert(0, str(ASSETS_SRC))
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

from check_runtime_contract import parse_static_tf_extrinsics, parse_urdf_extrinsics

FRAME_MEASUREMENT_KEYS = {
    "camera_link": "camera_extrinsic_xyz_rpy_in_base_link",
    "laser": "lidar_extrinsic_xyz_rpy_in_base_link",
    "imu_link": "imu_extrinsic_xyz_rpy_in_base_link",
}

HARDWARE_PARAM_KEYS = {
    "camera_link": (
        "urdf_base_link_to_camera_link_xyz_rpy",
        "static_tf_base_link_to_camera_link_xyz_rpy",
    ),
    "laser": (
        "urdf_base_link_to_laser_xyz_rpy",
        "static_tf_base_link_to_laser_xyz_rpy",
    ),
    "imu_link": (
        "urdf_base_link_to_imu_link_xyz_rpy",
        "static_tf_base_link_to_imu_link_xyz_rpy",
    ),
}

JOINT_NAMES = {
    "camera_link": "camera_joint",
    "laser": "laser_joint",
    "imu_link": "imu_joint",
}

STATIC_TF_NAMES = {
    "camera_link": "base_link2camera",
    "laser": "base_link2laser",
    "imu_link": "base_link2imu",
}


def parse_args():
    parser = argparse.ArgumentParser(description="Check or apply measured OSRacer sensor extrinsics.")
    parser.add_argument("--measurements", required=True, help="Real-car measurement JSON path")
    parser.add_argument(
        "--osracer-root",
        default=str(REPO_ROOT.parent / "osracer"),
        help="Path to the upper-computer osracer repo",
    )
    parser.add_argument(
        "--hardware-params",
        default=str(ASSETS_SRC / "osracer_lab_assets" / "hardware_params.py"),
        help="Path to osracer_lab hardware_params.py",
    )
    parser.add_argument("--write", action="store_true", help="Write measured extrinsics into repo files")
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


def parse_extrinsic_value(value):
    if isinstance(value, dict):
        if "xyz_rpy" in value:
            return parse_extrinsic_value(value["xyz_rpy"])
        if "xyz" in value and "rpy" in value:
            return tuple(float(v) for v in value["xyz"] + value["rpy"])
    if isinstance(value, (list, tuple)):
        values = tuple(float(v) for v in value)
    elif isinstance(value, str):
        values = tuple(float(v) for v in re.split(r"[\s,]+", value.strip()) if v)
    else:
        raise ValueError(f"unsupported extrinsic value: {value!r}")
    if len(values) != 6:
        raise ValueError(f"extrinsic value must contain 6 numbers, got {len(values)}")
    return values


def measured_extrinsics(measurements):
    result = {}
    for frame, key in FRAME_MEASUREMENT_KEYS.items():
        if key not in measurements:
            raise ValueError(f"missing required measurement: {key}")
        entry = measurements[key]
        value = entry.get("value") if isinstance(entry, dict) else entry
        result[frame] = parse_extrinsic_value(value)
    return result


def fmt_num(value):
    text = f"{float(value):.12g}"
    return "0.0" if text == "-0" else text


def fmt_tuple(values):
    return "(" + ", ".join(fmt_num(v) for v in values) + ")"


def fmt_attr(values):
    return " ".join(fmt_num(v) for v in values)


def nearly_equal(left, right, tol=1e-9):
    return len(left) == len(right) and all(abs(a - b) <= tol for a, b in zip(left, right))


def replace_urdf_joint(text, frame, values):
    joint_name = JOINT_NAMES[frame]
    xyz = fmt_attr(values[:3])
    rpy = fmt_attr(values[3:])
    pattern = re.compile(
        r'(<joint\s+.*?name="' + re.escape(joint_name) + r'".*?type="fixed".*?<origin\s+)'
        r'xyz="[^"]*"\s+rpy="[^"]*"',
        re.DOTALL,
    )
    new_text, count = pattern.subn(r'\1xyz="' + xyz + r'"\n      rpy="' + rpy + r'"', text, count=1)
    if count != 1:
        raise ValueError(f"could not update URDF joint: {joint_name}")
    return new_text


def replace_static_tf_node(text, frame, values):
    node_name = STATIC_TF_NAMES[frame]
    block_pattern = re.compile(
        r'(Node\(\s*package="tf2_ros",\s*executable="static_transform_publisher",\s*name="'
        + re.escape(node_name)
        + r'".*?\],\s*\))',
        re.DOTALL,
    )
    match = block_pattern.search(text)
    if not match:
        raise ValueError(f"could not find static TF node: {node_name}")
    block = match.group(1)
    replacements = {
        "x": values[0],
        "y": values[1],
        "z": values[2],
        "roll": values[3],
        "pitch": values[4],
        "yaw": values[5],
    }
    for key, value in replacements.items():
        pattern = re.compile(r'("--' + key + r'",\s*")([^"]+)(")')
        block, count = pattern.subn(lambda m, v=fmt_num(value): m.group(1) + v + m.group(3), block, count=1)
        if count != 1:
            raise ValueError(f"could not update static TF argument: {node_name} --{key}")
    return text[: match.start(1)] + block + text[match.end(1) :]


def replace_hardware_param(text, key, values):
    replacement = f'"{key}": {fmt_tuple(values)},'
    pattern = re.compile(r'"' + re.escape(key) + r'"\s*:\s*\([^)]*\),', re.DOTALL)
    new_text, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        raise ValueError(f"could not update hardware param: {key}")
    return new_text


def status_line(label, actual, expected):
    status = "OK" if nearly_equal(actual, expected) else "DIFF"
    return f"[{status}] {label}: actual={fmt_tuple(actual)} measured={fmt_tuple(expected)}"


def build_review(measurements, osracer_root):
    osracer_root = Path(osracer_root).resolve()
    urdf_path = osracer_root / "osracer_description" / "urdf" / "osracer.urdf"
    static_tf_path = osracer_root / "osracer_description" / "launch" / "robot_description_tf.launch.py"
    measured = measured_extrinsics(measurements)
    current_urdf = parse_urdf_extrinsics(urdf_path)
    current_static = parse_static_tf_extrinsics(static_tf_path.read_text(errors="replace"))
    frames = {}
    all_match = True
    for frame, values in measured.items():
        urdf_value = current_urdf.get(frame, ())
        static_value = current_static.get(frame, ())
        urdf_match = nearly_equal(urdf_value, values)
        static_tf_match = nearly_equal(static_value, values)
        frames[frame] = {
            "measurement_key": FRAME_MEASUREMENT_KEYS[frame],
            "measured_xyz_rpy": list(values),
            "urdf_xyz_rpy": list(urdf_value),
            "static_tf_xyz_rpy": list(static_value),
            "urdf_matches_measured": urdf_match,
            "static_tf_matches_measured": static_tf_match,
            "ready": urdf_match and static_tf_match,
        }
        all_match = all_match and frames[frame]["ready"]
    return {
        "overall": "pass" if all_match else "fail",
        "all_frames_match": all_match,
        "osracer_root": str(osracer_root),
        "urdf_path": str(urdf_path),
        "static_tf_path": str(static_tf_path),
        "frames": frames,
        "next_action": (
            "strict extrinsics are aligned"
            if all_match
            else "review measured extrinsics, then run sensor-extrinsics-write if approved"
        ),
    }


def main():
    args = parse_args()
    osracer_root = Path(args.osracer_root).resolve()
    hardware_params = Path(args.hardware_params).resolve()
    urdf_path = osracer_root / "osracer_description" / "urdf" / "osracer.urdf"
    static_tf_path = osracer_root / "osracer_description" / "launch" / "robot_description_tf.launch.py"

    measurements = load_measurements(args.measurements)
    measured = measured_extrinsics(measurements)
    current_urdf = parse_urdf_extrinsics(urdf_path)
    current_static = parse_static_tf_extrinsics(static_tf_path.read_text(errors="replace"))

    has_diff = False
    for frame, values in measured.items():
        print(status_line(f"urdf {frame}", current_urdf.get(frame, ()), values))
        print(status_line(f"static_tf {frame}", current_static.get(frame, ()), values))
        has_diff = has_diff or not nearly_equal(current_urdf.get(frame, ()), values)
        has_diff = has_diff or not nearly_equal(current_static.get(frame, ()), values)

    if not args.write:
        if has_diff:
            print("[INFO] rerun with --write after reviewing measured extrinsics")
            return 1
        print("[OK] measured extrinsics already match URDF and static TF")
        return 0

    urdf_text = urdf_path.read_text(errors="replace")
    static_text = static_tf_path.read_text(errors="replace")
    hardware_text = hardware_params.read_text(errors="replace")
    for frame, values in measured.items():
        urdf_text = replace_urdf_joint(urdf_text, frame, values)
        static_text = replace_static_tf_node(static_text, frame, values)
        for key in HARDWARE_PARAM_KEYS[frame]:
            hardware_text = replace_hardware_param(hardware_text, key, values)

    urdf_path.write_text(urdf_text)
    static_tf_path.write_text(static_text)
    hardware_params.write_text(hardware_text)
    print("[OK] wrote measured extrinsics to URDF, static TF, and hardware_params.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
