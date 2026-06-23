#!/usr/bin/env python3
"""Load hardware_params.py without importing IsaacLab task modules."""

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HARDWARE_PARAMS_PATH = REPO_ROOT / "source" / "osracer_lab_assets" / "osracer_lab_assets" / "hardware_params.py"
_spec = importlib.util.spec_from_file_location("osracer_hardware_params", HARDWARE_PARAMS_PATH)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

hardware_summary = _module.hardware_summary
