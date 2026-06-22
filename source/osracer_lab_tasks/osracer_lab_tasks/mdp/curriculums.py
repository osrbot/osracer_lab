"""Curriculum functions — inlined from WheeledLab."""

import torch
from collections.abc import Sequence

from isaaclab.envs.manager_based_rl_env import ManagerBasedRLEnv


def increase_reward_weight_over_time(
    env: ManagerBasedRLEnv,
    env_ids: Sequence[int],
    reward_term_name: str,
    increase: float,
    episodes_per_increase: int = 1,
    max_increases: int = torch.inf,
) -> torch.Tensor:
    num_episodes = env.common_step_counter // env.max_episode_length
    num_increases = num_episodes // episodes_per_increase

    if num_increases > max_increases:
        return

    if env.common_step_counter % env.max_episode_length != 0:
        return

    if (num_episodes + 1) % episodes_per_increase == 0:
        term_cfg = env.reward_manager.get_term_cfg(reward_term_name)
        term_cfg.weight += increase
        env.reward_manager.set_term_cfg(reward_term_name, term_cfg)
