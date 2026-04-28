"""Train the initial OSRacer drift task.

This is a thin launcher scaffold. It will become executable once the OSRacer
USD asset and final joint names are added.
"""

from osracer_lab_rl.startup import startup

import argparse

parser = argparse.ArgumentParser(description="Train OSRacer drift policy.")
parser.add_argument("--task", type=str, default="Isaac-OSRacerDriftRL-v0")
simulation_app, args_cli = startup(parser=parser)

import gymnasium as gym


def main():
    env = gym.make(args_cli.task)
    print(env)
    env.close()


if __name__ == "__main__":
    main()
    simulation_app.close()
