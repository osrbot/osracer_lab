"""OSRacer asset definitions for IsaacLab."""

import os
import toml

OSRACER_LAB_ASSETS_EXT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OSRACER_LAB_ASSETS_DATA_DIR = os.path.join(OSRACER_LAB_ASSETS_EXT_DIR, "data")
OSRACER_LAB_ASSETS_METADATA = toml.load(os.path.join(OSRACER_LAB_ASSETS_EXT_DIR, "config", "extension.toml"))

__version__ = OSRACER_LAB_ASSETS_METADATA["package"]["version"]

from .osracer import *
