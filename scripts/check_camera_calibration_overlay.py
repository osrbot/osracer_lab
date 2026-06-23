#!/usr/bin/env python3
"""Validate measured AR0234 camera calibration overlay for visual sim2real."""

import argparse
import json
import math
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
    parser = argparse.ArgumentParser(description="Check measured camera calibration overlay.")
    parser.add_argument("overlay", help="Overlay JSON from scripts/export_measured_overlay.py")
    parser.add_argument("--expected-width-px", type=int, default=width_px)
    parser.add_argument("--expected-height-px", type=int, default=height_px)
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    return parser.parse_args()


def load_overlay(path):
    with Path(path).open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("overlay root must be an object")
    return data


def number(value, label, *, min_value=0.001, max_value=10000.0):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label} must be finite")
    if result < min_value or result > max_value:
        raise ValueError(f"{label} must be between {min_value} and {max_value}")
    return result


def check_intrinsics(value, expected_width_px, expected_height_px):
    if not isinstance(value, dict):
        raise ValueError(f"{CAMERA_KEY} must be an object")

    fx = number(value.get("fx"), "fx")
    fy = number(value.get("fy"), "fy")
    cx = number(value.get("cx"), "cx")
    cy = number(value.get("cy"), "cy")
    width_px = int(number(value.get("width_px"), "width_px", min_value=1.0))
    height_px = int(number(value.get("height_px"), "height_px", min_value=1.0))

    if width_px != expected_width_px or height_px != expected_height_px:
        raise ValueError(
            f"camera calibration resolution {width_px}x{height_px} does not match "
            f"runtime {expected_width_px}x{expected_height_px}"
        )
    if not 0.0 <= cx <= width_px:
        raise ValueError("cx must be inside image width")
    if not 0.0 <= cy <= height_px:
        raise ValueError("cy must be inside image height")
    if fx > width_px * 8.0 or fy > height_px * 8.0:
        raise ValueError("fx/fy are implausibly large for the deployed image size")

    model = value.get("distortion_model")
    if not isinstance(model, str) or not model.strip():
        raise ValueError("distortion_model must be a non-empty string")
    coeffs = value.get("distortion_coeffs")
    if not isinstance(coeffs, list):
        raise ValueError("distortion_coeffs must be a list")
    for index, coeff in enumerate(coeffs):
        number(coeff, f"distortion_coeffs[{index}]", min_value=-10.0, max_value=10.0)

    return {
        "fx": fx,
        "fy": fy,
        "cx": cx,
        "cy": cy,
        "width_px": width_px,
        "height_px": height_px,
        "distortion_model": model.strip(),
        "distortion_coeff_count": len(coeffs),
    }


def validate_overlay(overlay, expected_width_px, expected_height_px):
    measured = overlay.get("measured_overlay")
    if not isinstance(measured, dict):
        raise ValueError("overlay must contain measured_overlay object")
    calibration = measured.get("camera_calibration")
    if not isinstance(calibration, dict):
        raise ValueError("overlay must contain measured_overlay.camera_calibration")
    if CAMERA_KEY not in calibration:
        raise ValueError(f"overlay must contain {CAMERA_KEY}")
    return check_intrinsics(calibration[CAMERA_KEY], expected_width_px, expected_height_px)


def main():
    args = parse_args()
    result = {"overlay": str(Path(args.overlay).resolve()), "ok": False}
    try:
        overlay = load_overlay(args.overlay)
        result["camera_calibration"] = validate_overlay(
            overlay,
            args.expected_width_px,
            args.expected_height_px,
        )
        result["ok"] = True
    except Exception as exc:
        result["error"] = str(exc)
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print(f"[FAIL] camera_calibration_overlay: {exc}")
        return 1

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        calibration = result["camera_calibration"]
        print(
            "[OK] camera_calibration_overlay: "
            f"{calibration['width_px']}x{calibration['height_px']} "
            f"fx={calibration['fx']:.3f} fy={calibration['fy']:.3f} "
            f"model={calibration['distortion_model']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
