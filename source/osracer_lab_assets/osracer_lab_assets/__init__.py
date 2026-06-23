"""OSRacer asset definitions for IsaacLab."""

import os

OSRACER_LAB_ASSETS_EXT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OSRACER_LAB_ASSETS_DATA_DIR = os.path.join(OSRACER_LAB_ASSETS_EXT_DIR, "data")
try:
    import toml
except ModuleNotFoundError:
    OSRACER_LAB_ASSETS_METADATA = {"package": {"version": "0+unknown"}}
else:
    OSRACER_LAB_ASSETS_METADATA = toml.load(os.path.join(OSRACER_LAB_ASSETS_EXT_DIR, "config", "extension.toml"))

__version__ = OSRACER_LAB_ASSETS_METADATA["package"]["version"]

from .hardware_params import *

try:
    from .osracer import *
except ModuleNotFoundError as exc:
    if exc.name not in ("isaaclab", "omni", "omni.client"):
        raise
