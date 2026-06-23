"""OSRacer visual RL task environment configuration.

Mirrors the WheeledLab mushr_visual_env_cfg pattern:
  - Procedurally generated traversability terrain (white=traversable, black=obstacle)
  - TiledCameraCfg attached to base_footprint with camera_joint offset
  - Visual observation: cropped + augmented grayscale camera + proprioception
  - Rewards: traversability signal + forward velocity

Camera placement notes:
  URDF camera_joint: xyz=(0.12323, -0.017229, -0.053395), rpy=(-90°, 0°, -90°)
  With merge_fixed_joints=True the camera_link and base_link prims are absorbed
  into base_footprint, so TiledCamera is attached there with the above offset.
  The rpy matches MuSHR exactly → same OffsetCfg rotation values.
"""

import os
import time
import torch

import numpy as np
from collections import Counter
from scipy.spatial.transform import Rotation as R

import isaaclab.envs.mdp as mdp
import isaaclab.sim as sim_utils
from isaaclab.assets import ArticulationCfg, AssetBaseCfg
from isaaclab.envs import ManagerBasedEnv, ManagerBasedRLEnvCfg
from isaaclab.managers import (
    EventTermCfg as EventTerm,
    ObservationGroupCfg as ObsGroup,
    ObservationTermCfg as ObsTerm,
    RewardTermCfg as RewTerm,
    SceneEntityCfg,
    TerminationTermCfg as DoneTerm,
)
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.sensors import TiledCameraCfg
from isaaclab.terrains import TerrainImporterCfg
from isaaclab.utils import configclass
from isaaclab.utils.math import euler_xyz_from_quat
from isaaclab.utils.noise import UniformNoiseCfg as Unoise

from osracer_lab_tasks.visual.mdp import reset_root_state
from osracer_lab_tasks.visual.utils import (
    TraversabilityHashmapUtil,
    create_geometry,
    generate_random_poses,
)

from osracer_lab_assets import OSRACER_LAB_ASSETS_DATA_DIR, OSRACER_VISUAL_CFG
from osracer_lab_tasks.common import OSRacerAckermannActionCfg
from . import mdp_sensors

##########################
###### OBSERVATIONS ######
##########################


@configclass
class VisualObsCfg:
    @configclass
    class PolicyCfg(ObsGroup):
        camera = ObsTerm(
            func=mdp_sensors.camera_data_rgb_flattened_aug,
            params={"sensor_cfg": SceneEntityCfg("camera")},
        )
        base_lin_vel = ObsTerm(func=mdp.base_lin_vel, noise=Unoise(n_min=-0.1, n_max=0.1))
        base_ang_vel = ObsTerm(func=mdp.base_ang_vel, noise=Unoise(n_min=-0.1, n_max=0.1))
        last_action = ObsTerm(func=mdp.last_action, clip=(-1.0, 1.0), noise=Unoise(-0.1, 0.1))

        def __post_init__(self):
            self.enable_corruption = False
            self.concatenate_terms = True

    policy: PolicyCfg = PolicyCfg()


###################
###### SCENE ######
###################


@configclass
class InitialPoseCfg:
    pos: tuple[float, float, float] = (0.0, 0.0, 0.0)
    rot_euler_xyz_deg: tuple[float, float, float] = (0.0, 0.0, 0.0)
    lin_vel: tuple[float, float, float] = (0.0, 0.0, 0.0)
    ang_vel: tuple[float, float, float] = (0.0, 0.0, 0.0)


@configclass
class VisualTerrainImporterCfg(TerrainImporterCfg):
    row_spacing = 0.5
    col_spacing = 0.5
    spacing = (row_spacing, col_spacing)

    num_rows = 500
    num_cols = 500
    map_size = (num_rows, num_cols)

    env_num_rows = 100
    env_num_cols = 100
    env_size = (env_num_rows, env_num_cols)

    group_num_rows = 50
    group_num_cols = 50
    sub_group_size = (group_num_rows, group_num_cols)
    num_walkers = 1
    color_sampling = False

    width = num_rows * row_spacing
    height = num_cols * col_spacing

    file_name = os.path.join(
        OSRACER_LAB_ASSETS_DATA_DIR, "rgb_maps", time.strftime("%Y%m%d_%H%M%S.usd")
    )

    traversability_hashmap = create_geometry(
        file_name, map_size, spacing, env_size, sub_group_size, num_walkers, color_sampling
    )

    prim_path = "/World/plane"
    terrain_type = "usd"
    usd_path = file_name
    collision_group = -1
    physics_material = sim_utils.RigidBodyMaterialCfg(
        friction_combine_mode="multiply",
        restitution_combine_mode="multiply",
        static_friction=2.0,
        dynamic_friction=2.0,
    )
    debug_vis = False

    def generate_random_poses(self, num_poses):
        init_poses = generate_random_poses(
            num_poses, self.row_spacing, self.col_spacing, self.traversability_hashmap, margin=0.1
        )
        return [
            InitialPoseCfg(pos=(x, y, 0.1), rot_euler_xyz_deg=(0.0, 0.0, angle))
            for x, y, angle in init_poses
        ]


@configclass
class OSRacerVisualSceneCfg(InteractiveSceneCfg):
    terrain = VisualTerrainImporterCfg()
    ground = AssetBaseCfg(
        prim_path="/World/base",
        spawn=sim_utils.GroundPlaneCfg(
            size=(terrain.width, terrain.height),
            color=(0, 0, 0),
            physics_material=sim_utils.RigidBodyMaterialCfg(
                friction_combine_mode="multiply",
                restitution_combine_mode="multiply",
                static_friction=2.0,
                dynamic_friction=2.0,
            ),
        ),
    )
    robot: ArticulationCfg = OSRACER_VISUAL_CFG.replace(prim_path="{ENV_REGEX_NS}/Robot")
    ground.init_state.pos = (0.0, 0.0, -1e-4)

    # Camera attached to base_footprint (camera/base links merged via merge_fixed_joints=True).
    # pos = camera_joint xyz from URDF; rot matches camera_joint rpy=(-90°,0°,-90°).
    camera = TiledCameraCfg(
        prim_path="{ENV_REGEX_NS}/Robot/base_footprint/camera",
        update_period=0.1,
        height=60,
        width=80,
        data_types=["rgb"],
        spawn=sim_utils.PinholeCameraCfg(
            focal_length=1.93,
            horizontal_aperture=3.896,
            vertical_aperture=2.453,
            clipping_range=(0.01, 1e2),
        ),
        offset=TiledCameraCfg.OffsetCfg(
            pos=(0.12323, -0.017229, -0.053395),
            rot=tuple(R.from_euler("xyz", [-90.0, 0.0, -90.0], degrees=True).as_quat().tolist()),
            convention="ros",
        ),
        debug_vis=False,
    )

    def __post_init__(self):
        super().__post_init__()
        self.robot.init_state = self.robot.init_state.replace(pos=(0.0, 0.0, 0.10))


#####################
###### EVENTS #######
#####################


@configclass
class VisualEventsCfg:
    reset_root_state = EventTerm(func=reset_root_state, mode="reset")


@configclass
class VisualEventsRandomCfg(VisualEventsCfg):
    change_wheel_friction = EventTerm(
        func=mdp.randomize_rigid_body_material,
        mode="startup",
        params={
            "static_friction_range": (0.4, 0.6),
            "dynamic_friction_range": (0.4, 0.6),
            "restitution_range": (0.0, 0.0),
            "num_buckets": 10,
            "asset_cfg": SceneEntityCfg("robot", body_names=".*wheel_link"),
            "make_consistent": False,
        },
    )
    add_base_mass = EventTerm(
        func=mdp.randomize_rigid_body_mass,
        mode="startup",
        params={
            "asset_cfg": SceneEntityCfg("robot", body_names=["base_footprint"]),
            "mass_distribution_params": (1.0, 3.0),
            "operation": "abs",
        },
    )


######################
###### REWARDS #######
######################


def traversable_reward(env):
    poses = mdp.root_pos_w(env)[..., :2]
    traversability = TraversabilityHashmapUtil().get_traversability(poses)
    return torch.where(traversability, 1.0, -1.0)


def forward_vel(env):
    return mdp.base_lin_vel(env)[:, 0]


@configclass
class VisualRewardsCfg:
    traversability = RewTerm(func=traversable_reward, weight=5.0)
    vel_rew = RewTerm(func=forward_vel, weight=7.0)


##########################
###### TERMINATION #######
##########################


def out_of_map(env):
    poses = mdp.root_pos_w(env)[..., :2]
    terrain = env.scene[SceneEntityCfg("terrain").name]
    w, h = terrain.cfg.width, terrain.cfg.height
    x_out = torch.logical_or(poses[..., 0] > w / 2, poses[..., 0] < -w / 2)
    y_out = torch.logical_or(poses[..., 1] > h / 2, poses[..., 1] < -h / 2)
    return torch.logical_or(x_out, y_out)


@configclass
class VisualTerminationsCfg:
    time_out = DoneTerm(func=mdp.time_out, time_out=True)
    out_range = DoneTerm(func=out_of_map)


######################
###### RL ENV ########
######################


@configclass
class OSRacerVisualRLEnvCfg(ManagerBasedRLEnvCfg):
    seed: int = 42
    num_envs: int = 256          # camera rendering is expensive; keep lower than drift
    env_spacing: float = 0.0

    observations: VisualObsCfg = VisualObsCfg()
    actions: OSRacerAckermannActionCfg = OSRacerAckermannActionCfg()
    events: VisualEventsCfg = VisualEventsCfg()
    rewards: VisualRewardsCfg = VisualRewardsCfg()
    terminations: VisualTerminationsCfg = VisualTerminationsCfg()

    def __post_init__(self):
        super().__post_init__()
        self.viewer.eye = [40.0, 0.0, 45.0]
        self.viewer.lookat = [0.0, 0.0, -3.0]
        self.sim.dt = 0.02          # 50 Hz physics
        self.decimation = 10         # 5 Hz policy — matches camera update_period=0.1s
        self.episode_length_s = 10.0
        self.scene = OSRacerVisualSceneCfg(num_envs=self.num_envs, env_spacing=self.env_spacing)


@configclass
class OSRacerVisualRLRandomEnvCfg(OSRacerVisualRLEnvCfg):
    events: VisualEventsRandomCfg = VisualEventsRandomCfg()


######################
###### PLAY ENV ######
######################


@configclass
class OSRacerVisualPlayEnvCfg(OSRacerVisualRLEnvCfg):
    events: VisualEventsRandomCfg = VisualEventsRandomCfg()
    rewards: VisualRewardsCfg = None
    terminations: VisualTerminationsCfg = None

    def __post_init__(self):
        super().__post_init__()
