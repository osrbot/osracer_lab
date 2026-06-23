#!/usr/bin/env python3
"""Verify an OSRacer calibration review pack after handoff or copy."""

import argparse
import hashlib
import json
from pathlib import Path

REQUIRED_JSON_FILES = (
    "real_car_measurements.review.json",
    "validation_report.json",
    "calibration_plan.json",
    "measured_overlay.json",
    "sensor_extrinsics_review.json",
    "sim2real_readiness.json",
    "evidence_manifest.json",
    "review_summary.json",
)
REQUIRED_TEXT_FILES = ("README.md",)


def parse_args():
    parser = argparse.ArgumentParser(description="Verify a calibration review pack created by create_calibration_review_pack.py.")
    parser.add_argument("pack_dir", help="Directory created by scripts/create_calibration_review_pack.py")
    parser.add_argument("--require-complete", action="store_true", help="Fail unless all required measurements are complete and valid")
    parser.add_argument("--require-readiness-pass", action="store_true", help="Fail unless sim2real readiness is pass")
    return parser.parse_args()


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def ok(message):
    print(f"[OK] {message}")


def fail(message, failures):
    print(f"[FAIL] {message}")
    failures.append(message)


def verify_required_files(pack_dir, failures):
    loaded = {}
    for name in REQUIRED_TEXT_FILES:
        path = pack_dir / name
        if path.is_file():
            ok(f"required file {name}")
        else:
            fail(f"required file missing: {name}", failures)
    for name in REQUIRED_JSON_FILES:
        path = pack_dir / name
        if not path.is_file():
            fail(f"required file missing: {name}", failures)
            continue
        try:
            loaded[name] = load_json(path)
        except Exception as exc:
            fail(f"cannot parse {name}: {exc}", failures)
        else:
            ok(f"required JSON {name}")
    return loaded


def evidence_path(pack_dir, metadata):
    rel = metadata.get("relative_path")
    if rel:
        return pack_dir / rel
    path = metadata.get("path")
    if path:
        candidate = Path(path)
        if candidate.is_absolute():
            return pack_dir / "evidence" / candidate.name
        return pack_dir / candidate
    return None


def verify_evidence_manifest(pack_dir, evidence_manifest, review_summary, failures):
    files = evidence_manifest.get("files", {})
    if not isinstance(files, dict):
        fail("evidence_manifest.files must be an object", failures)
        return
    missing = evidence_manifest.get("missing", {})
    if not isinstance(missing, dict):
        fail("evidence_manifest.missing must be an object", failures)
        missing = {}
    for label, metadata in sorted(files.items()):
        if not isinstance(metadata, dict):
            fail(f"evidence metadata for {label} must be an object", failures)
            continue
        path = evidence_path(pack_dir, metadata)
        if not path or not path.is_file():
            fail(f"evidence file missing: {label}", failures)
            continue
        expected_bytes = metadata.get("bytes")
        expected_sha = metadata.get("sha256")
        actual_bytes = path.stat().st_size
        actual_sha = sha256(path)
        if actual_bytes == expected_bytes:
            ok(f"evidence bytes {label}")
        else:
            fail(f"evidence bytes mismatch {label}: {actual_bytes} != {expected_bytes}", failures)
        if actual_sha == expected_sha:
            ok(f"evidence sha256 {label}")
        else:
            fail(f"evidence sha256 mismatch {label}: {actual_sha} != {expected_sha}", failures)
    summary_count = review_summary.get("evidence_file_count")
    if summary_count == len(files):
        ok(f"evidence_file_count: {summary_count}")
    else:
        fail(f"evidence_file_count mismatch: summary={summary_count} manifest={len(files)}", failures)
    summary_missing = review_summary.get("missing_evidence_files", {})
    if summary_missing == missing:
        ok("missing_evidence_files matches manifest")
    else:
        fail("missing_evidence_files does not match evidence_manifest.missing", failures)


def verify_summary_consistency(loaded, failures, require_complete, require_readiness_pass):
    validation = loaded.get("validation_report.json", {})
    readiness = loaded.get("sim2real_readiness.json", {})
    extrinsics = loaded.get("sensor_extrinsics_review.json", {})
    summary = loaded.get("review_summary.json", {})
    complete = len(validation.get("complete", []))
    remaining = len(validation.get("missing", [])) + len(validation.get("incomplete", [])) + len(validation.get("invalid", []))
    if summary.get("complete_measurements") == complete:
        ok(f"complete_measurements: {complete}")
    else:
        fail(f"complete_measurements mismatch: summary={summary.get('complete_measurements')} validation={complete}", failures)
    if summary.get("remaining_measurements") == remaining:
        ok(f"remaining_measurements: {remaining}")
    else:
        fail(f"remaining_measurements mismatch: summary={summary.get('remaining_measurements')} validation={remaining}", failures)
    if summary.get("sim2real_readiness") == readiness.get("overall"):
        ok(f"sim2real_readiness: {summary.get('sim2real_readiness')}")
    else:
        fail("sim2real_readiness summary does not match sim2real_readiness.json", failures)
    if summary.get("sensor_extrinsics_review") == extrinsics.get("overall"):
        ok(f"sensor_extrinsics_review: {summary.get('sensor_extrinsics_review')}")
    else:
        fail("sensor_extrinsics_review summary does not match sensor_extrinsics_review.json", failures)
    if summary.get("write_back_allowed_without_review") is False:
        ok("write_back_allowed_without_review: false")
    else:
        fail("write_back_allowed_without_review must be false", failures)
    if require_complete and remaining != 0:
        fail(f"review pack is not complete: remaining_measurements={remaining}", failures)
    if require_readiness_pass and readiness.get("overall") != "pass":
        fail(f"sim2real readiness is not pass: {readiness.get('overall')}", failures)


def main():
    args = parse_args()
    pack_dir = Path(args.pack_dir).expanduser().resolve()
    failures = []
    if not pack_dir.is_dir():
        raise NotADirectoryError(pack_dir)
    loaded = verify_required_files(pack_dir, failures)
    if "evidence_manifest.json" in loaded and "review_summary.json" in loaded:
        verify_evidence_manifest(pack_dir, loaded["evidence_manifest.json"], loaded["review_summary.json"], failures)
    required_for_summary = {"validation_report.json", "sim2real_readiness.json", "sensor_extrinsics_review.json", "review_summary.json"}
    if required_for_summary.issubset(loaded):
        verify_summary_consistency(loaded, failures, args.require_complete, args.require_readiness_pass)
    if failures:
        print(f"[FAIL] calibration review pack verification failed: {len(failures)} issue(s)")
        return 1
    print("[OK] calibration review pack verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
