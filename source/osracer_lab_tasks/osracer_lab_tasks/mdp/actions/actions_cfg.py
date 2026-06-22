"""Action config classes for OSRacer — inlined from WheeledLab."""

from dataclasses import MISSING
from isaaclab.managers import ActionTerm, ActionTermCfg
from isaaclab.utils import configclass
from . import ackermann_actions, rc_car_actions


@configclass
class AckermannActionCfg(ActionTermCfg):
    class_type: type[ActionTerm] = ackermann_actions.AckermannAction

    wheel_joint_names: list[str] = MISSING
    steering_joint_names: list[str] = MISSING
    scale: tuple[float, float] = (1.0, 1.0)
    offset: tuple[float, float] = (0.0, 0.0)
    bounding_strategy: str | None = "tanh"
    base_length: float = 1.0
    base_width: float = 1.0
    wheel_radius: float = 1.0
    no_reverse: bool = False


@configclass
class RCCarRWDActionCfg(AckermannActionCfg):
    class_type: type[ActionTerm] = rc_car_actions.RCCarRWDAction


@configclass
class RCCar4WDActionCfg(AckermannActionCfg):
    class_type: type[ActionTerm] = rc_car_actions.RCCar4WDAction
