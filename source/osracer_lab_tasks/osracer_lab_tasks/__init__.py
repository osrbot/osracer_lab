"""Gym task registration for OSRacer IsaacLab environments."""

import gymnasium as gym

from .drifting import OSRacerDriftPlayEnvCfg, OSRacerDriftRLEnvCfg


gym.register(
    id="Isaac-OSRacerDriftRL-v0",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": OSRacerDriftRLEnvCfg,
        "play_env_cfg_entry_point": OSRacerDriftPlayEnvCfg,
        "rsl_rl_cfg_entry_point": "osracer_lab_tasks.drifting.config.agents.osracer.rsl_rl_ppo_cfg:OSRacerPPORunnerCfg",
    },
)
