#!/usr/bin/env python3
"""Create a calibration review pack from OSRacer real-car measurements."""

import argparse
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
ASSETS_SRC = REPO_ROOT / "source" / "osracer_lab_assets"
if str(ASSETS_SRC) not in sys.path:
    sys.path.insert(0, str(ASSETS_SRC))

from export_measured_overlay import build_overlay, load_measurements as load_overlay_measurements  # noqa: E402
from apply_sensor_extrinsics import build_review as build_extrinsics_review  # noqa: E402
from plan_calibration_updates import build_plan  # noqa: E402
from sim2real_readiness import build_report as build_readiness_report  # noqa: E402
from validate_real_measurements import REQUIRED_KEYS, load_measurements, validate_measurements  # noqa: E402

DEFAULT_OUTPUT = Path("/tmp/osracer_calibration_review_pack")


def parse_args():
    parser = argparse.ArgumentParser(description="Create an OSRacer calibration review pack.")
    parser.add_argument("--measurements", required=True, help="Path to real_car_measurements.json")
    parser.add_argument(
        "--osracer-root",
        default=str(REPO_ROOT.parent / "osracer"),
        help="Path to the osracer feat-demo repo",
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT), help="Output review pack directory")
    parser.add_argument("--overwrite", action="store_true", help="Replace output directory if it exists")
    return parser.parse_args()


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def copy_measurements(src, output_dir):
    target = output_dir / "real_car_measurements.review.json"
    shutil.copy2(src, target)
    return target


def build_summary(measurements_path, validation, plan, readiness, extrinsics_review):
    complete_count = len(validation["complete"])
    remaining_count = len(validation["missing"]) + len(validation["incomplete"]) + len(validation["invalid"])
    auto_apply_count = len(plan["auto_apply_ready"])
    review_apply_count = len(plan["review_apply_ready"])
    ready = readiness["overall"] == "pass"
    extrinsics_ready = extrinsics_review["overall"] == "pass"
    if ready:
        next_action = "review auto_apply_ready items, then run sensor-extrinsics-write if approved"
    elif remaining_count:
        next_action = "fill missing or incomplete measurements, then regenerate this review pack"
    elif not extrinsics_ready:
        next_action = "review sensor_extrinsics_review.json, then run sensor-extrinsics-write if approved"
    else:
        next_action = "resolve failed readiness gates before writing calibration changes"
    return {
        "measurements_path": str(Path(measurements_path).resolve()),
        "complete_measurements": complete_count,
        "required_measurements": len(REQUIRED_KEYS),
        "remaining_measurements": remaining_count,
        "invalid_measurements": validation["invalid"],
        "auto_apply_candidate_count": auto_apply_count,
        "review_apply_candidate_count": review_apply_count,
        "sim2real_readiness": readiness["overall"],
        "sensor_extrinsics_review": extrinsics_review["overall"],
        "write_back_allowed_without_review": False,
        "recommended_next_action": next_action,
    }


def build_readme(summary):
    lines = [
        "# OSRacer Calibration Review Pack",
        "",
        "This pack is for reviewing measured real-car parameters before writing them into URDF, static TF, IsaacLab, MuJoCo, or Jetson deployment artifacts.",
        "",
        "## Status",
        "",
        f"- Measurements complete: {summary['complete_measurements']}/{summary['required_measurements']}",
        f"- Remaining measurements: {summary['remaining_measurements']}",
        f"- Sim2real readiness: {summary['sim2real_readiness']}",
        f"- Sensor extrinsics review: {summary['sensor_extrinsics_review']}",
        f"- Auto-apply candidates: {summary['auto_apply_candidate_count']}",
        f"- Review-required candidates: {summary['review_apply_candidate_count']}",
        "- Source write-back allowed without review: no",
        "",
        "## Files",
        "",
        "- `real_car_measurements.review.json`: copied input measurements",
        "- `validation_report.json`: required measurement validation result",
        "- `calibration_plan.json`: candidate source changes grouped by risk",
        "- `measured_overlay.json`: offline sim/replay overlay, safe to consume without mutating source",
        "- `sensor_extrinsics_review.json`: measured-vs-URDF/static-TF alignment check",
        "- `sim2real_readiness.json`: readiness gates and logs",
        "- `review_summary.json`: compact status for handoff",
        "",
        "## Next Action",
        "",
        summary["recommended_next_action"],
    ]
    return "\n".join(lines).rstrip() + "\n"


def main():
    args = parse_args()
    measurements_path = Path(args.measurements).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    if output_dir.exists():
        if not args.overwrite:
            raise FileExistsError(f"{output_dir} exists; pass --overwrite to replace it")
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    copied_measurements = copy_measurements(measurements_path, output_dir)
    measurements = load_measurements(measurements_path)
    validation = validate_measurements(measurements)
    validation["measurements_path"] = str(measurements_path)
    validation["valid"] = not (validation["missing"] or validation["incomplete"] or validation["invalid"])

    measurement_doc, overlay_measurements = load_overlay_measurements(measurements_path)
    overlay = build_overlay(measurement_doc, overlay_measurements)
    plan = build_plan(measurements)
    readiness = build_readiness_report(Path(args.osracer_root).expanduser().resolve(), measurements_path)
    extrinsics_review = build_extrinsics_review(measurements, Path(args.osracer_root).expanduser().resolve())
    summary = build_summary(measurements_path, validation, plan, readiness, extrinsics_review)

    write_json(output_dir / "validation_report.json", validation)
    write_json(output_dir / "calibration_plan.json", plan)
    write_json(output_dir / "measured_overlay.json", overlay)
    write_json(output_dir / "sensor_extrinsics_review.json", extrinsics_review)
    write_json(output_dir / "sim2real_readiness.json", readiness)
    write_json(output_dir / "review_summary.json", summary)
    (output_dir / "README.md").write_text(build_readme(summary), encoding="utf-8")

    print(f"wrote {output_dir}")
    print(f"measurements: {copied_measurements}")
    print(f"summary: {output_dir / 'review_summary.json'}")
    print(f"readme: {output_dir / 'README.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
