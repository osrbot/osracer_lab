"""Visual-task reset event — inlined from WheeledLab."""

import torch

import isaaclab.utils.math as math_utils

from isaaclab.envs import ManagerBasedEnv
from isaaclab.managers import SceneEntityCfg
from isaaclab.assets import Articulation, RigidObject
from isaaclab.terrains import TerrainImporter


def reset_root_state(
    env: ManagerBasedEnv,
    env_ids: torch.Tensor,
    asset_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
):
    asset: RigidObject | Articulation = env.scene[asset_cfg.name]
    terrain: TerrainImporter = env.scene.terrain

    valid_poses = terrain.cfg.generate_random_poses(len(env_ids))

    posns = torch.stack([torch.tensor(p.pos, device=env.device) for p in valid_poses]).float()
    oris_raw = [torch.deg2rad(torch.tensor(p.rot_euler_xyz_deg, device=env.device)) for p in valid_poses]
    oris = torch.stack([math_utils.quat_from_euler_xyz(*o) for o in oris_raw]).float()
    lin_vels = torch.stack([torch.tensor(p.lin_vel, device=env.device) for p in valid_poses]).float()
    ang_vels = torch.stack([torch.tensor(p.ang_vel, device=env.device) for p in valid_poses]).float()

    positions = posns + asset.data.default_root_state[env_ids, :3]
    lin_vels = lin_vels + asset.data.default_root_state[env_ids, 7:10]
    ang_vels = ang_vels + asset.data.default_root_state[env_ids, 10:13]

    asset.write_root_pose_to_sim(torch.cat([positions, oris], dim=-1), env_ids=env_ids)
    asset.write_root_velocity_to_sim(torch.cat([lin_vels, ang_vels], dim=-1), env_ids=env_ids)
