#!/usr/bin/env python3
"""Check that simulation sensor configs stay tied to hardware_params.py."""

import argparse
import math
import re
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ASSETS_SRC = REPO_ROOT / "source" / "osracer_lab_assets"
if str(ASSETS_SRC) not in sys.path:
    sys.path.insert(0, str(ASSETS_SRC))
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

from mujoco_sim2sim_smoke import build_mjcf
from hardware_params_loader import hardware_summary


def parse_args():
    parser = argparse.ArgumentParser(description="Validate OSRacer simulation sensor contract.")
    parser.add_argument("--json", action="store_true", help="Print JSON-compatible key=value lines only")
    return parser.parse_args()


def nearly_equal(left, right, tol=1e-9):
    return abs(float(left) - float(right)) <= tol


def check(condition, label, failures, detail=""):
    if condition:
        print(f"[OK] {label}{': ' + detail if detail else ''}")
    else:
        print(f"[FAIL] {label}{': ' + detail if detail else ''}")
        failures.append(label)


def camera_fov_deg(camera_cfg):
    focal = camera_cfg["focal_length"]
    horizontal = camera_cfg["horizontal_aperture"]
    vertical = camera_cfg["vertical_aperture"]
    return (
        math.degrees(2.0 * math.atan(horizontal / (2.0 * focal))),
        math.degrees(2.0 * math.atan(vertical / (2.0 * focal))),
    )


def read_text(path):
    return Path(path).read_text(encoding="utf-8", errors="replace")


def check_visual_config(params, failures):
    visual_cfg_path = REPO_ROOT / "source/osracer_lab_tasks/osracer_lab_tasks/visual/osracer_visual_env_cfg.py"
    text = read_text(visual_cfg_path)
    check("ar0234_pinhole_camera_cfg" in text, "visual_cfg_uses_ar0234_pinhole_helper", failures)
    check("OSRACER_SENSOR_EXTRINSICS" in text, "visual_cfg_uses_sensor_extrinsics_source", failures)
    check("focal_length=1.93" not in text, "visual_cfg_no_legacy_focal_literal", failures)
    check("horizontal_aperture=3.896" not in text, "visual_cfg_no_legacy_aperture_literal", failures)

    camera_cfg = params["camera_pinhole_cfg"]
    camera = params["camera_ar0234"]
    expected_width_mm = camera["resolution_px"][0] * camera["pixel_size_um"][0] / 1000.0
    expected_height_mm = camera["resolution_px"][1] * camera["pixel_size_um"][1] / 1000.0
    check(nearly_equal(camera_cfg["focal_length"], camera["lens_focal_length_mm"]), "camera_focal_from_hardware", failures)
    check(nearly_equal(camera_cfg["horizontal_aperture"], expected_width_mm), "camera_horizontal_aperture_from_sensor", failures)
    check(nearly_equal(camera_cfg["vertical_aperture"], expected_height_mm), "camera_vertical_aperture_from_sensor", failures)
    hfov, vfov = camera_fov_deg(camera_cfg)
    check(abs(hfov - camera["advertised_fov_deg"]) > 5.0, "camera_advertised_fov_not_used_as_calibrated_intrinsic", failures, f"pinhole_hfov={hfov:.3f} vfov={vfov:.3f}")


def check_lidar_config(params, failures):
    lidar = params["lidar_25m"]
    scan = params["lidar_planar_scan_cfg"]
    expected_ray_count = int(round(scan["horizontal_fov_deg"] / scan["angular_resolution_deg"])) + 1
    check(nearly_equal(scan["horizontal_fov_deg"], lidar["horizontal_fov_deg"]), "lidar_fov_from_hardware", failures)
    check(scan["angular_resolution_deg"] in lidar["angular_resolution_deg"], "lidar_resolution_supported", failures)
    check(scan["scan_rate_hz"] in lidar["scan_rate_hz"], "lidar_scan_rate_supported", failures)
    check(nearly_equal(scan["max_range_m"], lidar["range_m_at_70pct_reflectivity"]), "lidar_range_from_hardware", failures)
    check(scan["ray_count"] == expected_ray_count, "lidar_ray_count_matches_fov_resolution", failures, f"rays={scan['ray_count']}")

    with tempfile.TemporaryDirectory() as tmp:
        xml_path = Path(tmp) / "osracer.xml"
        xml_path.write_text(build_mjcf(params, mass_kg=3.0, wheel_width_m=0.025, timestep=0.01))
        xml = xml_path.read_text()
    metadata = {
        "lidar_horizontal_fov_deg": scan["horizontal_fov_deg"],
        "lidar_angular_resolution_deg": scan["angular_resolution_deg"],
        "lidar_scan_rate_hz": scan["scan_rate_hz"],
        "lidar_ray_count": scan["ray_count"],
        "lidar_max_range_m": scan["max_range_m"],
    }
    for key, expected in metadata.items():
        match = re.search(rf"{key}=([-+0-9.eE]+)", xml)
        check(match is not None and nearly_equal(match.group(1), expected), f"mujoco_metadata_{key}", failures)


def main():
    parse_args()
    failures = []
    params = hardware_summary()
    check_visual_config(params, failures)
    check_lidar_config(params, failures)
    if failures:
        print("sim_sensor_contract: fail")
        return 1
    print("sim_sensor_contract: pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
