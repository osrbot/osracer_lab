"""Blind observation config — inlined from WheeledLab."""

import isaaclab.envs.mdp as mdp
from isaaclab.utils import configclass
from isaaclab.managers import ObservationGroupCfg as ObsGroup
from isaaclab.managers import ObservationTermCfg as ObsTerm
from isaaclab.managers import SceneEntityCfg
from isaaclab.utils.noise import AdditiveGaussianNoiseCfg as Gnoise

from osracer_lab_tasks.mdp.observations import base_ang_vel, base_lin_vel, root_euler_xyz, root_pos_w


@configclass
class BlindObsCfg:
    """Default observation configuration (no sensors; no corruption)."""

    @configclass
    class PolicyCfg(ObsGroup):
        root_pos_w_term = ObsTerm(func=root_pos_w, noise=Gnoise(mean=0.0, std=0.1))
        root_euler_xyz_term = ObsTerm(func=root_euler_xyz, noise=Gnoise(mean=0.0, std=0.1))
        base_lin_vel_term = ObsTerm(func=base_lin_vel, noise=Gnoise(mean=0.0, std=0.5))
        base_ang_vel_term = ObsTerm(func=base_ang_vel, noise=Gnoise(std=0.4))
        last_action_term = ObsTerm(func=mdp.last_action, clip=(-1.0, 1.0))

        def __post_init__(self):
            self.concatenate_terms = True
            self.enable_corruption = False

    policy: PolicyCfg = PolicyCfg()
