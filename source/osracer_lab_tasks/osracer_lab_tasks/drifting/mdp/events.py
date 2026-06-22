"""Track-based reset event — inlined from WheeledLab."""

import torch

import isaaclab.utils.math as math_utils
from isaaclab.assets import Articulation, RigidObject
from isaaclab.managers import EventTermCfg, ManagerTermBase, SceneEntityCfg
from isaaclab.envs import ManagerBasedEnv


class reset_root_state_along_track(ManagerTermBase):
    """Resets the asset root state along a stadium-shaped track path with additive noise."""

    def __init__(self, cfg: EventTermCfg, env: ManagerBasedEnv):
        super().__init__(cfg, env)
        self.track_radius = torch.tensor(cfg.params.get("track_radius", 0.8), device=self.device)
        self.track_straight_dist = torch.tensor(cfg.params.get("track_straight_dist", 0.8), device=self.device)
        self.num_points = cfg.params.get("num_points", 20)
        self.reference_poses = self.generate_reference_poses()

    def generate_reference_poses(self):
        dist_track = 2.0 * torch.pi * self.track_radius + 4.0 * self.track_straight_dist
        dists = torch.rand(self.num_points, device=self.device) * dist_track

        case1_pos = torch.stack([
            self.track_radius.repeat_interleave(dists.shape[0]).to(self.device),
            dists - self.track_straight_dist.repeat_interleave(dists.shape[0]).to(self.device),
            torch.zeros_like(dists),
        ], dim=-1)
        case1_ori = torch.stack([torch.zeros_like(dists), torch.zeros_like(dists), torch.full_like(dists, 90)], dim=-1)

        angle = (dists - 2 * self.track_straight_dist) / self.track_radius
        case2_pos = torch.stack([
            self.track_radius * torch.cos(angle),
            self.track_straight_dist + self.track_radius * torch.sin(angle),
            torch.zeros_like(dists),
        ], dim=-1)
        case2_ori = torch.stack([
            torch.zeros_like(dists), torch.zeros_like(dists), 90 + angle * 180 / torch.pi,
        ], dim=-1)

        remaining = dists - 2 * self.track_straight_dist - torch.pi * self.track_radius
        case3_pos = torch.stack([
            -self.track_radius.repeat_interleave(dists.shape[0]).to(self.device),
            self.track_straight_dist.repeat_interleave(dists.shape[0]).to(self.device) - remaining,
            torch.zeros_like(dists),
        ], dim=-1)
        case3_ori = torch.stack([
            torch.zeros_like(dists), torch.zeros_like(dists), torch.full_like(dists, 270),
        ], dim=-1)

        angle2 = (dists - 4 * self.track_straight_dist - torch.pi * self.track_radius) / self.track_radius
        case4_pos = torch.stack([
            -self.track_radius * torch.cos(angle2),
            -self.track_straight_dist - self.track_radius * torch.sin(angle2),
            torch.zeros_like(dists),
        ], dim=-1)
        case4_ori = torch.stack([
            torch.zeros_like(dists), torch.zeros_like(dists), 270 + angle2 * 180 / torch.pi,
        ], dim=-1)

        def _sel(cond, a, b):
            return torch.where(cond.unsqueeze(-1), a, b)

        pos = _sel(
            dists < 2 * self.track_straight_dist,
            case1_pos,
            _sel(
                dists < 2 * self.track_straight_dist + torch.pi * self.track_radius,
                case2_pos,
                _sel(
                    dists < 4 * self.track_straight_dist + torch.pi * self.track_radius,
                    case3_pos,
                    case4_pos,
                ),
            ),
        )
        ori = _sel(
            dists < 2 * self.track_straight_dist,
            case1_ori,
            _sel(
                dists < 2 * self.track_straight_dist + torch.pi * self.track_radius,
                case2_ori,
                _sel(
                    dists < 4 * self.track_straight_dist + torch.pi * self.track_radius,
                    case3_ori,
                    case4_ori,
                ),
            ),
        )

        return torch.stack([pos, ori], dim=1)

    def __call__(
        self,
        env: ManagerBasedEnv,
        env_ids: torch.Tensor | None,
        track_radius: float,
        track_straight_dist: float,
        num_points: int,
        asset_cfg: SceneEntityCfg,
        pos_noise: float = 0.0,
        yaw_noise: float = 0.0,
    ):
        asset: RigidObject | Articulation = env.scene[asset_cfg.name]

        idx = torch.randint(self.num_points, (len(env_ids),), device=env.device)
        ref_points = self.reference_poses[idx]

        xy_noise = (2 * torch.rand((len(env_ids), 2), device=env.device) - 1.0) * pos_noise
        add_pos_noise = torch.cat((xy_noise, torch.zeros_like(xy_noise[..., 0:1])), dim=-1)
        posns = ref_points[:, 0, :] + add_pos_noise

        yaw_noise_t = (2 * torch.rand(len(env_ids), device=env.device) - 1.0) * yaw_noise
        oris = ref_points[:, 1, :]
        roll, pitch, yaw = torch.unbind(torch.deg2rad(oris), dim=-1)
        yaw = yaw + yaw_noise_t
        oris = math_utils.quat_from_euler_xyz(roll=roll, pitch=pitch, yaw=yaw)

        asset.write_root_pose_to_sim(torch.cat([posns, oris], dim=-1), env_ids=env_ids)
        asset.write_root_velocity_to_sim(torch.zeros((len(env_ids), 6), device=env.device), env_ids=env_ids)
