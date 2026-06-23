"""MDP observation functions — inlined from WheeledLab."""

import torch

import isaaclab.envs.mdp as mdp
import isaaclab.utils.math as math_utils

from isaaclab.envs import ManagerBasedEnv
from isaaclab.managers import SceneEntityCfg


def _finite(value: torch.Tensor) -> torch.Tensor:
    """Replace non-finite physics values so RSL-RL can reset bad envs cleanly."""
    return torch.nan_to_num(value, nan=0.0, posinf=0.0, neginf=0.0)


def root_pos_w(
    env: ManagerBasedEnv,
    asset_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
) -> torch.Tensor:
    """Finite root position in the environment frame."""
    return _finite(mdp.root_pos_w(env, asset_cfg))


def root_euler_xyz(
    env: ManagerBasedEnv,
    asset_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
) -> torch.Tensor:
    """Root Euler XYZ angles in the environment frame."""
    xyz_tuple = math_utils.euler_xyz_from_quat(mdp.root_quat_w(env, asset_cfg))
    return _finite(torch.stack(xyz_tuple, dim=-1))


def base_lin_vel(
    env: ManagerBasedEnv,
    asset_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
) -> torch.Tensor:
    """Finite root linear velocity in the asset's root frame."""
    return _finite(mdp.base_lin_vel(env, asset_cfg))


def base_ang_vel(
    env: ManagerBasedEnv,
    asset_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
) -> torch.Tensor:
    """Finite root angular velocity in the asset's root frame."""
    return _finite(mdp.base_ang_vel(env, asset_cfg))
