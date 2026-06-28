#!/usr/bin/env python3
"""Check whether policy observations are usable on the real car."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

SIM_ONLY_TERMS = {
    "root_pos_w": "world-frame simulator position is not available on the real car",
    "root_euler_xyz": "simulator Euler-angle truth is not available on the real car",
    "root_quat_w": "simulator world-frame orientation truth is not available on the real car",
    "root_lin_vel_w": "simulator world-frame linear velocity truth is not available on the real car",
    "root_ang_vel_w": "simulator world-frame angular velocity truth is not available on the real car",
}

TASK_CONTRACTS = {
    "Isaac-OSRacerDriftRL-v0": {
        "file": "source/osracer_lab_tasks/osracer_lab_tasks/common/observations.py",
        "deployable": False,
        "required_terms": ("base_lin_vel", "base_ang_vel", "last_action"),
        "note": "drift baseline is a simulator-training task and still uses privileged simulator terms",
    },
    "Isaac-OSRacerVisualRL-v0": {
        "file": "source/osracer_lab_tasks/osracer_lab_tasks/visual/osracer_visual_env_cfg.py",
        "deployable": True,
        "required_terms": ("camera", "base_lin_vel", "base_ang_vel", "last_action"),
        "note": "visual task is the current deployment-oriented policy observation baseline",
    },
}


def parse_args():
    parser = argparse.ArgumentParser(description="Check OSRacer policy observation deployability.")
    parser.add_argument("--task", choices=sorted(TASK_CONTRACTS), help="Check only one task")
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    parser.add_argument(
        "--allow-sim-only",
        action="store_true",
        help="Return zero even when simulator-only observations are found",
    )
    return parser.parse_args()


def strip_comments(text):
    return "\n".join(line.split("#", 1)[0] for line in text.splitlines())


def find_terms(text, terms):
    stripped = strip_comments(text)
    return sorted(term for term in terms if re.search(rf"\b{re.escape(term)}\b", stripped))


def policy_cfg_segment(text):
    match = re.search(r"(?ms)^    class PolicyCfg\(ObsGroup\):.*?(?=^    [a-zA-Z_].*?:|^class |\Z)", text)
    if not match:
        match = re.search(r"(?ms)^class PolicyCfg\(ObsGroup\):.*?(?=^class |\Z)", text)
    if not match:
        raise ValueError("PolicyCfg(ObsGroup) block not found")
    return match.group(0)


def check_contract(task, contract):
    path = REPO_ROOT / contract["file"]
    text = path.read_text(encoding="utf-8", errors="replace")
    policy_text = policy_cfg_segment(text)
    sim_only_terms = find_terms(policy_text, SIM_ONLY_TERMS)
    missing_required = [term for term in contract["required_terms"] if term not in policy_text]
    status = "pass"
    if missing_required:
        status = "fail"
    if contract["deployable"] and sim_only_terms:
        status = "fail"
    if not contract["deployable"] and sim_only_terms:
        status = "blocked"
    return {
        "task": task,
        "status": status,
        "deployable": contract["deployable"],
        "file": contract["file"],
        "sim_only_terms": sim_only_terms,
        "sim_only_reasons": {term: SIM_ONLY_TERMS[term] for term in sim_only_terms},
        "missing_required_terms": missing_required,
        "required_terms": list(contract["required_terms"]),
        "note": contract["note"],
    }


def print_text(results):
    overall = "pass" if all(item["status"] == "pass" for item in results) else "fail"
    print(f"policy_observation_contract: {overall}")
    for item in results:
        print(f"[{item['status'].upper()}] {item['task']}: {item['note']}")
        print(f"  file: {item['file']}")
        if item["sim_only_terms"]:
            print("  simulator_only_terms:")
            for term in item["sim_only_terms"]:
                print(f"    - {term}: {item['sim_only_reasons'][term]}")
        if item["missing_required_terms"]:
            print("  missing_required_terms:")
            for term in item["missing_required_terms"]:
                print(f"    - {term}")


def main():
    args = parse_args()
    tasks = [args.task] if args.task else sorted(TASK_CONTRACTS)
    results = [check_contract(task, TASK_CONTRACTS[task]) for task in tasks]
    if args.json:
        print(json.dumps({"results": results}, indent=2, sort_keys=True))
    else:
        print_text(results)
    if args.allow_sim_only:
        return 0
    return 0 if all(item["status"] == "pass" for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
