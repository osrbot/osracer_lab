"""RC-car action terms — inlined from WheeledLab."""

import torch
from . import ackermann_actions


class RCCarRWDAction(ackermann_actions.AckermannAction):
    """RWD with tan steering and open-diff throttle."""

    def _calculate_ackermann_angles_and_velocities(self, target_velocity, target_steering_angle):
        tan_steering = torch.tan(target_steering_angle)
        target_ang_vel = target_velocity / self.wheel_rad

        delta_left = tan_steering
        delta_right = tan_steering
        v_back_left = target_ang_vel
        v_back_right = target_ang_vel

        throttle = torch.stack([v_back_left, v_back_right], dim=1)
        return delta_left, delta_right, throttle


class RCCar4WDAction(ackermann_actions.AckermannAction):
    """4WD with tan steering and Ackermann-adjusted throttle."""

    def _calculate_ackermann_angles_and_velocities(self, target_velocity, target_steering_angle):
        L = self.base_length
        W = self.base_width
        wheel_radius = self.wheel_rad

        tan_steering = torch.tan(target_steering_angle)
        R = torch.where(tan_steering == 0, torch.full_like(tan_steering, 1e6), L / tan_steering)

        delta_left = tan_steering
        delta_right = tan_steering

        R_rear_left = torch.sqrt((R - W / 2) ** 2 + L ** 2)
        R_rear_right = torch.sqrt((R + W / 2) ** 2 + L ** 2)

        v_front_left = target_velocity * torch.abs(R_rear_left / (R * wheel_radius))
        v_front_right = target_velocity * torch.abs(R_rear_right / (R * wheel_radius))
        v_back_left = target_velocity * torch.abs((R - W / 2) / (R * wheel_radius))
        v_back_right = target_velocity * torch.abs((R + W / 2) / (R * wheel_radius))

        wheel_speeds = torch.stack([v_back_left, v_back_right, v_front_left, v_front_right], dim=1)
        return delta_left, delta_right, wheel_speeds
