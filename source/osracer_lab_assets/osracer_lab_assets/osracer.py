"""OSRacer articulation configuration.

The USD asset is intentionally a placeholder path until the robot model is
exported from the ROS description/CAD source. Keep joint names synchronized
with the final USD file.
"""

from isaaclab.assets import ArticulationCfg
import isaaclab.sim as sim_utils

from . import OSRACER_LAB_ASSETS_DATA_DIR

OSRACER_USD_PATH = f"{OSRACER_LAB_ASSETS_DATA_DIR}/Robots/OSRacer/osracer.usd"

OSRACER_INIT_STATE = ArticulationCfg.InitialStateCfg(
    pos=(0.0, 0.0, 0.05),
    joint_pos={
        "front_left_steer_joint": 0.0,
        "front_right_steer_joint": 0.0,
        "rear_left_wheel_joint": 0.0,
        "rear_right_wheel_joint": 0.0,
    },
)

OSRACER_CFG = ArticulationCfg(
    spawn=sim_utils.UsdFileCfg(
        usd_path=OSRACER_USD_PATH,
        rigid_props=sim_utils.RigidBodyPropertiesCfg(
            rigid_body_enabled=True,
            max_linear_velocity=100.0,
            max_angular_velocity=100.0,
            max_depenetration_velocity=10.0,
            enable_gyroscopic_forces=True,
        ),
        articulation_props=sim_utils.ArticulationRootPropertiesCfg(
            enabled_self_collisions=False,
            solver_position_iteration_count=8,
            solver_velocity_iteration_count=2,
            sleep_threshold=0.005,
            stabilization_threshold=0.001,
        ),
    ),
    init_state=OSRACER_INIT_STATE,
    actuators={},
)
