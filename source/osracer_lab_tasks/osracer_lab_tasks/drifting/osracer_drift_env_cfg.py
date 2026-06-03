"""OSRacer drift RL task environment configuration.

Mirrors the WheeledLab mushr_drift_env_cfg pattern, adapted for OSRacer joint names.
Reward functions are robot-agnostic and copied verbatim from WheeledLab; only
turn_left_go_right uses an OSRacer-specific joint regex.
"""

import torch

import isaaclab.envs.mdp as mdp
import isaaclab.sim as sim_utils
from isaaclab.assets import ArticulationCfg, AssetBaseCfg, RigidObject
from isaaclab.envs import ManagerBasedRLEnvCfg
from isaaclab.managers import (
    CurriculumTermCfg as CurrTerm,
    EventTermCfg as EventTerm,
    RewardTermCfg as RewTerm,
    SceneEntityCfg,
    TerminationTermCfg as DoneTerm,
)
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.terrains import TerrainImporterCfg
from isaaclab.utils import configclass

from wheeledlab.envs.mdp import increase_reward_weight_over_time
from wheeledlab_tasks.common import BlindObsCfg
from wheeledlab_tasks.drifting.mdp import reset_root_state_along_track

from osracer_lab_assets import OSRACER_CFG
from osracer_lab_tasks.common import OSRacerAckermannActionCfg

##############################
###### COMMON CONSTANTS ######
##############################

CORNER_IN_RADIUS = 0.3
CORNER_OUT_RADIUS = 2.0
LINE_RADIUS = 0.8
STRAIGHT = 0.8
SLIP_THRESHOLD = 0.55
MAX_SPEED = 3.0

###################
###### SCENE ######
###################


@configclass
class OSRacerDriftTerrainCfg(TerrainImporterCfg):
    prim_path = "/World/ground"
    terrain_type = "plane"
    collision_group = -1
    physics_material = sim_utils.RigidBodyMaterialCfg(
        friction_combine_mode="multiply",
        restitution_combine_mode="multiply",
        static_friction=1.1,
        dynamic_friction=1.0,
    )
    debug_vis = False


@configclass
class OSRacerDriftSceneCfg(InteractiveSceneCfg):
    terrain = OSRacerDriftTerrainCfg()
    robot: ArticulationCfg = OSRACER_CFG.replace(prim_path="{ENV_REGEX_NS}/Robot")
    light = AssetBaseCfg(
        prim_path="/World/light",
        spawn=sim_utils.DistantLightCfg(color=(0.75, 0.75, 0.75), intensity=3000.0),
    )

    def __post_init__(self):
        super().__post_init__()
        self.robot.init_state = self.robot.init_state.replace(pos=(0.0, 0.0, 0.10))


#####################
###### EVENTS #######
#####################


@configclass
class DriftEventsCfg:
    reset_root_state = EventTerm(
        func=reset_root_state_along_track,
        mode="reset",
        params={
            "track_radius": LINE_RADIUS,
            "track_straight_dist": STRAIGHT,
            "num_points": 20,
            "pos_noise": 0.5,
            "yaw_noise": 1.0,
            "asset_cfg": SceneEntityCfg("robot"),
        },
    )


@configclass
class DriftEventsRandomCfg(DriftEventsCfg):
    change_wheel_friction = EventTerm(
        func=mdp.randomize_rigid_body_material,
        mode="startup",
        params={
            "static_friction_range": (0.3, 0.5),
            "dynamic_friction_range": (0.3, 0.5),
            "restitution_range": (0.0, 0.0),
            "num_buckets": 20,
            # ".*wheel_link" matches Left_front_wheel_link via the .* prefix
            "asset_cfg": SceneEntityCfg("robot", body_names=".*wheel_link"),
            "make_consistent": True,
        },
    )

    randomize_gains = EventTerm(
        func=mdp.randomize_actuator_gains,
        mode="startup",
        params={
            "asset_cfg": SceneEntityCfg("robot", joint_names=[".*rear.*wheel.*"]),
            "damping_distribution_params": (10.0, 50.0),
            "operation": "abs",
        },
    )

    push_robots_hf = EventTerm(
        func=mdp.push_by_setting_velocity,
        mode="interval",
        interval_range_s=(0.1, 0.4),
        params={
            "velocity_range": {
                "x": (-0.1, 0.1),
                "y": (-0.03, 0.03),
                "yaw": (-0.3, 0.3),
            },
        },
    )

    push_robots_lf = EventTerm(
        func=mdp.push_by_setting_velocity,
        mode="interval",
        interval_range_s=(0.8, 1.2),
        params={
            "velocity_range": {"yaw": (-0.6, 0.6)},
        },
    )

    add_base_mass = EventTerm(
        func=mdp.randomize_rigid_body_mass,
        mode="startup",
        params={
            "asset_cfg": SceneEntityCfg("robot", body_names=["base_link"]),
            "mass_distribution_params": (0.3, 0.5),
            "operation": "add",
            "distribution": "uniform",
        },
    )


######################
###### REWARDS #######
######################


def track_progress_rate(env):
    """Positive z angular velocity → forward track progress."""
    asset: RigidObject = env.scene[SceneEntityCfg("robot").name]
    return asset.data.root_link_ang_vel_w[..., 2]


def vel_dist(env, speed_target: float = MAX_SPEED, offset: float = -(MAX_SPEED**2)):
    lin_vel = mdp.base_lin_vel(env)
    ground_speed = torch.norm(lin_vel[..., :2], dim=-1)
    return (ground_speed - speed_target) ** 2 + offset


def cross_track_dist(
    env,
    straight: float,
    track_radius: float = (CORNER_IN_RADIUS + CORNER_OUT_RADIUS) / 2,
    offset: float = -1.0,
    p: float = 1.0,
):
    poses = mdp.root_pos_w(env)
    on_straights = torch.abs(poses[..., 1]) < straight
    sq_ctd = torch.where(
        on_straights,
        torch.where(
            poses[..., 0] > 0,
            (poses[..., 0] - track_radius) ** 2,
            (poses[..., 0] + track_radius) ** 2,
        ),
        torch.where(
            poses[..., 1] > 0,
            (torch.sqrt((poses[..., 1] - straight) ** 2 + poses[..., 0] ** 2) - track_radius) ** 2,
            (torch.sqrt((poses[..., 1] + straight) ** 2 + poses[..., 0] ** 2) - track_radius) ** 2,
        ),
    )
    return torch.pow(torch.sqrt(sq_ctd) + offset, p)


def energy_through_turn(env, straight: float):
    poses = mdp.root_pos_w(env)
    speed = torch.norm(mdp.base_lin_vel(env), dim=-1)
    return torch.where(torch.abs(poses[..., 1]) > straight, speed**2, 0.0)


def in_range(env, straight, corner_in_radius):
    poses = mdp.root_pos_w(env)
    return torch.where(
        torch.abs(poses[..., 1]) < straight,
        torch.where(torch.abs(poses[..., 0]) < corner_in_radius, 1, 0),
        torch.where(
            poses[..., 1] > 0,
            torch.where((poses[..., 1] - straight) ** 2 + poses[..., 0] ** 2 < corner_in_radius**2, 1, 0),
            torch.where((poses[..., 1] + straight) ** 2 + poses[..., 0] ** 2 < corner_in_radius**2, 1, 0),
        ),
    )


def off_track(env, straight, corner_out_radius):
    poses = mdp.root_pos_w(env)
    return torch.where(
        torch.abs(poses[..., 1]) < straight,
        torch.where(torch.abs(poses[..., 0]) > corner_out_radius, 1, 0),
        torch.where(
            poses[..., 1] > 0,
            torch.where((poses[..., 1] - straight) ** 2 + poses[..., 0] ** 2 > corner_out_radius**2, 1, 0),
            torch.where((poses[..., 1] + straight) ** 2 + poses[..., 0] ** 2 > corner_out_radius**2, 1, 0),
        ),
    )


def side_slip(env, min_thresh: float, max_thresh: float, min_vel_x: float = 0.5):
    vel = mdp.base_lin_vel(env)
    slip_angle = torch.abs(torch.atan2(vel[..., 1], vel[..., 0]))
    valid_angle = torch.where(
        torch.logical_or(torch.abs(vel[..., 0]) < min_vel_x, slip_angle > max_thresh),
        0.0,
        slip_angle,
    )
    return torch.where(valid_angle < min_thresh, 0.0, valid_angle)


def turn_left_go_right(env, ang_vel_thresh: float = torch.pi / 4):
    asset = env.scene[SceneEntityCfg("robot").name]
    # OSRacer steering joints: left/right_steering_hinge_joint
    steer_joints = asset.find_joints(".*steering_hinge.*")[0]
    steer_joint_pos = mdp.joint_pos(env)[..., steer_joints].mean(dim=-1)
    ang_vel = torch.clamp(mdp.base_ang_vel(env)[..., 2], max=ang_vel_thresh, min=-ang_vel_thresh)
    return torch.clamp(steer_joint_pos * ang_vel * -1.0, min=0.0)


@configclass
class DriftRewardsCfg:
    side_slip = RewTerm(
        func=side_slip,
        weight=10.0,
        params={"min_thresh": 0.25, "max_thresh": SLIP_THRESHOLD, "min_vel_x": 1.0},
    )
    vel = RewTerm(
        func=vel_dist,
        weight=-5.0,
        params={"speed_target": MAX_SPEED},
    )
    progress = RewTerm(func=track_progress_rate, weight=40.0)
    tlgr = RewTerm(func=turn_left_go_right, params={"ang_vel_thresh": 1.0}, weight=0.0)
    turn_energy = RewTerm(func=energy_through_turn, weight=20.0, params={"straight": STRAIGHT})
    cross_track = RewTerm(
        func=cross_track_dist,
        weight=-50.0,
        params={"straight": STRAIGHT, "track_radius": LINE_RADIUS, "p": 1, "offset": -1.0},
    )
    term_pens = RewTerm(
        func=mdp.rewards.is_terminated_term,
        params={"term_keys": ["out_of_bounds"]},
        weight=-5000.0,
    )


########################
###### CURRICULUM ######
########################


@configclass
class DriftCurriculumCfg:
    more_slip = CurrTerm(
        func=increase_reward_weight_over_time,
        params={"reward_term_name": "side_slip", "increase": 20.0, "episodes_per_increase": 20, "max_increases": 10},
    )
    more_tlgr = CurrTerm(
        func=increase_reward_weight_over_time,
        params={"reward_term_name": "tlgr", "increase": 10.0, "episodes_per_increase": 20, "max_increases": 5},
    )
    more_term_pens = CurrTerm(
        func=increase_reward_weight_over_time,
        params={"reward_term_name": "term_pens", "increase": -1000.0, "episodes_per_increase": 50, "max_increases": 5},
    )


##########################
###### TERMINATION #######
##########################


def cart_off_track(env, straight: float, corner_in_radius: float, corner_out_radius: float):
    return torch.logical_or(
        off_track(env, straight, corner_out_radius) > 0.5,
        in_range(env, straight, corner_in_radius) > 0.5,
    )


@configclass
class DriftTerminationsCfg:
    time_out = DoneTerm(func=mdp.time_out, time_out=True)
    out_of_bounds = DoneTerm(
        func=cart_off_track,
        params={"straight": STRAIGHT, "corner_in_radius": CORNER_IN_RADIUS, "corner_out_radius": CORNER_OUT_RADIUS},
    )


######################
###### RL ENV ########
######################


@configclass
class OSRacerDriftRLEnvCfg(ManagerBasedRLEnvCfg):
    seed: int = 42
    # Conservative start vs. MuSHR's 1024 — URDF mesh colliders add sim cost
    num_envs: int = 512
    env_spacing: float = 0.0

    observations: BlindObsCfg = BlindObsCfg()
    actions: OSRacerAckermannActionCfg = OSRacerAckermannActionCfg()
    rewards: DriftRewardsCfg = DriftRewardsCfg()
    events: DriftEventsRandomCfg = DriftEventsRandomCfg()
    terminations: DriftTerminationsCfg = DriftTerminationsCfg()
    curriculum: DriftCurriculumCfg = DriftCurriculumCfg()

    def __post_init__(self):
        super().__post_init__()
        self.viewer.eye = [4.0, -4.0, 4.0]
        self.viewer.lookat = [0.0, 0.0, 0.0]
        self.sim.dt = 0.005
        self.decimation = 4
        self.sim.render_interval = 20
        self.episode_length_s = 5.0
        self.actions.throttle_steer.scale = (MAX_SPEED, 0.488)
        self.observations.policy.enable_corruption = True
        self.scene = OSRacerDriftSceneCfg(num_envs=self.num_envs, env_spacing=self.env_spacing)


######################
###### PLAY ENV ######
######################


@configclass
class OSRacerDriftPlayEnvCfg(OSRacerDriftRLEnvCfg):
    events: DriftEventsRandomCfg = DriftEventsRandomCfg(
        reset_root_state=EventTerm(
            func=reset_root_state_along_track,
            mode="reset",
            params={
                "track_radius": LINE_RADIUS,
                "track_straight_dist": STRAIGHT,
                "num_points": 20,
                "pos_noise": 0.0,
                "yaw_noise": 0.0,
                "asset_cfg": SceneEntityCfg("robot"),
            },
        )
    )
    rewards: DriftRewardsCfg = None
    terminations: DriftTerminationsCfg = None
    curriculum: DriftCurriculumCfg = None

    def __post_init__(self):
        super().__post_init__()
