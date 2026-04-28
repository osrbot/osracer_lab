"""Action configuration helpers for OSRacer tasks."""

from isaaclab.utils import configclass
from wheeledlab.envs.mdp import RCCarRWDActionCfg


@configclass
class OSRacerAckermannActionCfg:
    """Ackermann-like speed and steering action for OSRacer.

    Action semantics are intentionally aligned with real-robot deployment:
    [target_speed_mps, target_steering_rad].
    """

    throttle_steer = RCCarRWDActionCfg(
        wheel_joint_names=[
            "rear_left_wheel_joint",
            "rear_right_wheel_joint",
        ],
        steering_joint_names=[
            "front_left_steer_joint",
            "front_right_steer_joint",
        ],
        base_length=0.285,
        base_width=0.180,
        wheel_radius=0.050,
        scale=(2.0, 0.488),
        no_reverse=True,
        bounding_strategy="clip",
        asset_name="robot",
    )
