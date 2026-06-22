"""Ackermann steering action term — inlined from WheeledLab."""

from __future__ import annotations

import torch
from typing import TYPE_CHECKING

from isaaclab.assets import Articulation
from isaaclab.managers import ActionTerm

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedEnv
    from . import actions_cfg


class AckermannAction(ActionTerm):
    """Action term for controlling Ackermann steering vehicles."""

    cfg: "actions_cfg.AckermannActionCfg"
    _asset: Articulation

    def __init__(self, cfg: "actions_cfg.AckermannActionCfg", env: "ManagerBasedEnv"):
        super().__init__(cfg, env)

        wheel_ids, wheel_names = self._asset.find_joints(cfg.wheel_joint_names)
        self._wheel_ids = wheel_ids
        self._wheel_names = wheel_names

        steering_ids, steering_names = self._asset.find_joints(cfg.steering_joint_names)
        self._steering_ids = steering_ids
        self._steering_names = steering_names

        self._scale = torch.tensor(cfg.scale, device=self.device, dtype=torch.float32)
        self._offset = torch.tensor(cfg.offset, device=self.device, dtype=torch.float32)
        self._bounding_strategy = cfg.bounding_strategy

        self._raw_actions = torch.zeros(env.num_envs, self.action_dim, device=self.device)

        self.base_length = torch.tensor(cfg.base_length, device=self.device)
        self.base_width = torch.tensor(cfg.base_width, device=self.device)
        self.wheel_rad = torch.tensor(cfg.wheel_radius, device=self.device)

    @property
    def action_dim(self) -> int:
        return 2

    @property
    def raw_actions(self) -> torch.Tensor:
        return self._raw_actions

    @property
    def processed_actions(self) -> torch.Tensor:
        return self._processed_actions

    def process_actions(self, actions):
        self._raw_actions[:] = actions
        if self._bounding_strategy == "clip":
            self._processed_actions = torch.clip(actions, min=-1.0, max=1.0) * self._scale + self._offset
        elif self._bounding_strategy == "tanh":
            self._processed_actions = torch.tanh(actions) * self._scale + self._offset
        else:
            self._processed_actions = actions * self._scale + self._offset
        if self.cfg.no_reverse:
            self._processed_actions[:, 0] = torch.clamp(self._processed_actions[:, 0], min=0.0)

    def apply_actions(self):
        left_angle, right_angle, wheel_speeds = self._calculate_ackermann_angles_and_velocities(
            target_velocity=self.processed_actions[:, 0],
            target_steering_angle=self.processed_actions[:, 1],
        )
        front_wheel_angles = torch.stack([left_angle, right_angle], dim=1)
        self._asset.set_joint_velocity_target(wheel_speeds, joint_ids=self._wheel_ids)
        self._asset.set_joint_position_target(front_wheel_angles, joint_ids=self._steering_ids)

    def _calculate_ackermann_angles_and_velocities(self, target_steering_angle, target_velocity):
        L = self.base_length
        W = self.base_width
        wheel_radius = self.wheel_rad

        target_steering_angle = target_steering_angle.float()
        target_velocity = target_velocity.float()

        tan_steering = torch.tan(target_steering_angle)
        R = torch.where(tan_steering == 0, torch.full_like(tan_steering, 1e6), L / tan_steering)

        delta_left = torch.atan(L / (R - W / 2))
        delta_right = torch.atan(L / (R + W / 2))

        R_rear_left = torch.sqrt((R - W / 2) ** 2 + L ** 2)
        R_rear_right = torch.sqrt((R + W / 2) ** 2 + L ** 2)

        v_front_left = target_velocity * torch.abs(R_rear_left / (R * wheel_radius))
        v_front_right = target_velocity * torch.abs(R_rear_right / (R * wheel_radius))
        v_back_left = target_velocity * torch.abs((R - W / 2) / (R * wheel_radius))
        v_back_right = target_velocity * torch.abs((R + W / 2) / (R * wheel_radius))

        wheel_speeds = torch.stack([v_back_left, v_back_right, v_front_left, v_front_right], dim=1)
        return delta_left, delta_right, wheel_speeds
