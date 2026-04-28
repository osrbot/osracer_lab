"""Initial OSRacer drift task scaffold.

This file mirrors the WheeledLab task style while staying minimal until the
OSRacer USD asset and actuator model are finalized.
"""

import isaaclab.sim as sim_utils
import isaaclab.envs.mdp as mdp
from isaaclab.assets import ArticulationCfg, AssetBaseCfg
from isaaclab.envs import ManagerBasedRLEnvCfg
from isaaclab.managers import EventTermCfg as EventTerm
from isaaclab.managers import RewardTermCfg as RewTerm
from isaaclab.managers import SceneEntityCfg
from isaaclab.managers import TerminationTermCfg as DoneTerm
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.terrains import TerrainImporterCfg
from isaaclab.utils import configclass

from osracer_lab_assets import OSRACER_CFG
from osracer_lab_tasks.common import OSRacerAckermannActionCfg
from wheeledlab_tasks.common import BlindObsCfg


@configclass
class OSRacerDriftTerrainCfg(TerrainImporterCfg):
    prim_path = "/World/ground"
    terrain_type = "plane"
    collision_group = -1
    physics_material = sim_utils.RigidBodyMaterialCfg(
        friction_combine_mode="multiply",
        restitution_combine_mode="multiply",
        static_friction=1.0,
        dynamic_friction=0.9,
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


@configclass
class OSRacerDriftEventsCfg:
    reset_root_state = EventTerm(
        func=mdp.reset_root_state_uniform,
        mode="reset",
        params={
            "pose_range": {"x": (-0.1, 0.1), "y": (-0.1, 0.1), "yaw": (-0.2, 0.2)},
            "velocity_range": {},
            "asset_cfg": SceneEntityCfg("robot"),
        },
    )


@configclass
class OSRacerDriftRewardsCfg:
    forward_vel = RewTerm(func=mdp.base_lin_vel, weight=1.0)


@configclass
class OSRacerDriftTerminationsCfg:
    time_out = DoneTerm(func=mdp.time_out, time_out=True)


@configclass
class OSRacerDriftRLEnvCfg(ManagerBasedRLEnvCfg):
    seed: int = 42
    num_envs: int = 512
    env_spacing: float = 0.0

    observations: BlindObsCfg = BlindObsCfg()
    actions: OSRacerAckermannActionCfg = OSRacerAckermannActionCfg()
    events: OSRacerDriftEventsCfg = OSRacerDriftEventsCfg()
    rewards: OSRacerDriftRewardsCfg = OSRacerDriftRewardsCfg()
    terminations: OSRacerDriftTerminationsCfg = OSRacerDriftTerminationsCfg()

    def __post_init__(self):
        super().__post_init__()
        self.viewer.eye = [4.0, -4.0, 3.0]
        self.viewer.lookat = [0.0, 0.0, 0.0]
        self.sim.dt = 0.005
        self.decimation = 4
        self.sim.render_interval = 20
        self.episode_length_s = 5.0
        self.scene = OSRacerDriftSceneCfg(num_envs=self.num_envs, env_spacing=self.env_spacing)


@configclass
class OSRacerDriftPlayEnvCfg(OSRacerDriftRLEnvCfg):
    rewards: OSRacerDriftRewardsCfg = None
    terminations: OSRacerDriftTerminationsCfg = None
