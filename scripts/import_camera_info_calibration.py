#!/usr/bin/env python3
"""Import ROS CameraInfo calibration into real-car measurement JSON."""

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ASSETS_SRC = REPO_ROOT / "source" / "osracer_lab_assets"
if str(ASSETS_SRC) not in sys.path:
    sys.path.insert(0, str(ASSETS_SRC))

from osracer_lab_assets.hardware_params import hardware_summary  # noqa: E402

CAMERA_KEY = "camera_intrinsics_fx_fy_cx_cy_distortion"


def parse_args():
    runtime = hardware_summary()["camera_ar0234"]["ros_runtime"]
    width_px, height_px = runtime["configured_resolution_px"]
    parser = argparse.ArgumentParser(description="Merge ROS CameraInfo calibration into real-car measurements.")
    parser.add_argument("--measurements", required=True, help="Path to docs/real_car_measurements.json")
    parser.add_argument("--camera-info", required=True, help="JSON/YAML-style CameraInfo export")
    parser.add_argument("--output", default=None, help="Output path. Defaults to updating --measurements in place.")
    parser.add_argument("--expected-width-px", type=int, default=width_px)
    parser.add_argument("--expected-height-px", type=int, default=height_px)
    parser.add_argument("--write", action="store_true", help="Write changes instead of printing a dry-run summary.")
    return parser.parse_args()


def load_json(path):
    text = Path(path).read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        try:
            import yaml
        except ImportError as yaml_exc:
            raise ValueError(f"{path} is not JSON and PyYAML is not installed") from yaml_exc
        data = yaml.safe_load(text)
        if data is None:
            raise ValueError(f"{path} is empty") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain an object")
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


def number(value, label, *, min_value=0.001, max_value=10000.0):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a number")
    result = float(value)
    if result < min_value or result > max_value:
        raise ValueError(f"{label} must be between {min_value} and {max_value}")
    return result


def sequence(data, names, label):
    for name in names:
        value = data.get(name)
        if value is not None:
            if not isinstance(value, (list, tuple)):
                raise ValueError(f"{name} must be a list")
            return list(value)
    raise ValueError(f"CameraInfo is missing {label}")


def compact_source(path):
    return str(Path(path).resolve())


def merge_note(existing, addition):
    existing = existing or ""
    if addition in existing:
        return existing
    return (existing + "\n" + addition).strip()


def parse_camera_info(camera_info, expected_width_px, expected_height_px):
    width = int(number(camera_info.get("width"), "width", min_value=1.0))
    height = int(number(camera_info.get("height"), "height", min_value=1.0))
    if width != expected_width_px or height != expected_height_px:
        raise ValueError(
            f"CameraInfo resolution {width}x{height} does not match runtime "
            f"{expected_width_px}x{expected_height_px}"
        )

    matrix = sequence(camera_info, ("k", "K"), "K/k")
    if len(matrix) != 9:
        raise ValueError("CameraInfo K/k must contain 9 numbers")
    coeffs = sequence(camera_info, ("d", "D"), "D/d")
    for index, coeff in enumerate(coeffs):
        number(coeff, f"D[{index}]", min_value=-10.0, max_value=10.0)

    model = camera_info.get("distortion_model") or camera_info.get("distortionModel")
    if not isinstance(model, str) or not model.strip():
        raise ValueError("CameraInfo must include distortion_model")

    value = {
        "fx": number(matrix[0], "K[0]"),
        "fy": number(matrix[4], "K[4]"),
        "cx": number(matrix[2], "K[2]"),
        "cy": number(matrix[5], "K[5]"),
        "width_px": width,
        "height_px": height,
        "distortion_model": model.strip(),
        "distortion_coeffs": [float(item) for item in coeffs],
    }
    if not 0.0 <= value["cx"] <= width:
        raise ValueError("cx must be inside image width")
    if not 0.0 <= value["cy"] <= height:
        raise ValueError("cy must be inside image height")
    return value


def apply_import(measurements, camera_info, camera_info_path, expected_width_px, expected_height_px):
    value = parse_camera_info(camera_info, expected_width_px, expected_height_px)
    source = compact_source(camera_info_path)
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    collection = measurements.setdefault("collection", {})
    collection["camera_info_calibration"] = {
        "camera_info": source,
        "width_px": value["width_px"],
        "height_px": value["height_px"],
        "distortion_model": value["distortion_model"],
    }

    entry = measurement_entry(measurements, CAMERA_KEY)
    entry["value"] = value
    entry["source"] = source
    entry["measured_at"] = now
    entry["notes"] = merge_note(
        entry.get("notes"),
        "Imported from ROS CameraInfo at the deployed camera resolution.",
    )
    return ["collection.camera_info_calibration", f"measurements.{CAMERA_KEY}"]


def main():
    args = parse_args()
    measurements_path = Path(args.measurements)
    output_path = Path(args.output) if args.output else measurements_path
    measurements = load_json(measurements_path)
    try:
        camera_info = load_json(args.camera_info)
        changes = apply_import(
            measurements,
            camera_info,
            args.camera_info,
            args.expected_width_px,
            args.expected_height_px,
        )
    except ValueError as exc:
        print(f"camera_info_not_imported: {exc}")
        return 1
    if args.write:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(measurements, indent=2, sort_keys=False) + "\n", encoding="utf-8")
        print(f"wrote {output_path}")
    else:
        print("dry_run: pass --write to update the measurement file")
    print("changes:")
    for item in changes:
        print(f"  - {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
