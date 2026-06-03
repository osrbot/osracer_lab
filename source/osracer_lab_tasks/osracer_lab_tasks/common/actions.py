"""Action configuration for OSRacer tasks."""

from isaaclab.utils import configclass
from wheeledlab.envs.mdp import RCCarRWDActionCfg


@configclass
class OSRacerAckermannActionCfg:
    """RWD Ackermann action for OSRacer.

    Actions: [target_speed_mps, target_steering_rad] — aligns with real-robot deployment.
    """

    throttle_steer = RCCarRWDActionCfg(
        wheel_joint_names=[
            "left_rear_wheel_joint",
            "right_rear_wheel_joint",
        ],
        steering_joint_names=[
            "left_steering_hinge_joint",
            "right_steering_hinge_joint",
        ],
        base_length=0.285,   # wheelbase (front axle to rear axle) from URDF
        base_width=0.235,    # rear track width from URDF (0.10027 + 0.134728 m)
        wheel_radius=0.050,
        scale=(3.0, 0.488),  # (MAX_SPEED m/s, max_steer_rad) — set in env __post_init__
        no_reverse=True,
        bounding_strategy="clip",
        asset_name="robot",
    )
