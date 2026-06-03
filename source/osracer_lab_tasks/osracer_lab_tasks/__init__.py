"""Gym task registration for OSRacer IsaacLab environments."""

import gymnasium as gym

from .drifting import OSRacerDriftPlayEnvCfg, OSRacerDriftRLEnvCfg
from .visual import OSRacerVisualPlayEnvCfg, OSRacerVisualRLEnvCfg


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

gym.register(
    id="Isaac-OSRacerVisualRL-v0",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": OSRacerVisualRLEnvCfg,
        "play_env_cfg_entry_point": OSRacerVisualPlayEnvCfg,
        "rsl_rl_cfg_entry_point": "osracer_lab_tasks.visual.config.agents.osracer.rsl_rl_ppo_cfg:OSRacerVisualPPORunnerCfg",
    },
)
