"""IsaacLab startup helper for OSRacer Lab."""

import argparse
import sys


def startup(parser=None, prelaunch_callback=None, register_cfgs=True):
    from isaaclab.app import AppLauncher

    if parser is None:
        parser = argparse.ArgumentParser(description="OSRacer Lab launcher")

    AppLauncher.add_app_launcher_args(parser)
    args_cli, hydra_args = parser.parse_known_args()

    if prelaunch_callback is not None:
        prelaunch_callback(args_cli)

    # Enable cameras for visual RL, but keep blind tasks on the lighter headless path.
    # Forcing cameras on drift loads the RTX Hydra engine and has crashed headless runs.
    if not getattr(args_cli, "enable_cameras", False):
        args_cli.enable_cameras = "Visual" in getattr(args_cli, "task", "")
    sys.argv = [sys.argv[0]] + hydra_args

    app_launcher = AppLauncher(args_cli)
    simulation_app = app_launcher.app

    if register_cfgs:
        import osracer_lab_tasks  # noqa: F401

    return simulation_app, args_cli
