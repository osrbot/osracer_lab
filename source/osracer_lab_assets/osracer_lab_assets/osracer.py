"""OSRacer articulation configurations for IsaacLab.

Two configs are provided:
  OSRACER_CFG        — blind/drift RL tasks (fixed sensor joints merged into base_link)
  OSRACER_VISUAL_CFG — visual RL tasks (same merge, different USD cache; camera attached
                        at scene level via TiledCameraCfg with camera_joint offset)
"""

from isaaclab.actuators import DCMotorCfg, ImplicitActuatorCfg
from isaaclab.assets import ArticulationCfg
import isaaclab.sim as sim_utils

from . import OSRACER_LAB_ASSETS_DATA_DIR

OSRACER_URDF_PATH = (
    "/home/osrbot/Desktop/osracer/osracer/osracer_description/urdf/osracer.urdf"
)

OSRACER_ACTUATOR_CFG = {
    "steering_joints": ImplicitActuatorCfg(
        joint_names_expr=["left_steering_hinge_joint", "right_steering_hinge_joint"],
        velocity_limit=10.0,
        effort_limit=3.2,
        stiffness=100.0,
        damping=10.0,
        friction=0.0,
    ),
    "throttle_joints": DCMotorCfg(
        joint_names_expr=["left_rear_wheel_joint", "right_rear_wheel_joint"],
        saturation_effort=1.05,
        effort_limit=0.25,
        velocity_limit=450.0,
        stiffness=0.0,
        damping=1000.0,
        friction=0.0,
    ),
    # Front wheel spin joints are passive — free to rotate, no drive torque
    # Capital L in Left_front_wheel_joint must match exactly.
    "passive_front_wheels": ImplicitActuatorCfg(
        joint_names_expr=["Left_front_wheel_joint", "right_front_wheel_joint"],
        effort_limit=0.0,
        velocity_limit=450.0,
        stiffness=0.0,
        damping=0.0,
        friction=0.0,
    ),
}

OSRACER_INIT_STATE = ArticulationCfg.InitialStateCfg(
    # Rear wheel joint is ~0.100m below base_link; with ~0.050m wheel radius the
    # contact point sits ~0.050m below base_link. Spawn at 0.10m gives clearance.
    pos=(0.0, 0.0, 0.10),
    joint_pos={
        "left_steering_hinge_joint": 0.0,
        "right_steering_hinge_joint": 0.0,
        "left_rear_wheel_joint": 0.0,
        "right_rear_wheel_joint": 0.0,
        "Left_front_wheel_joint": 0.0,
        "right_front_wheel_joint": 0.0,
    },
)

_RIGID_PROPS = sim_utils.RigidBodyPropertiesCfg(
    rigid_body_enabled=True,
    max_linear_velocity=1000.0,
    max_angular_velocity=100000.0,
    max_depenetration_velocity=100.0,
    max_contact_impulse=0.0,
    enable_gyroscopic_forces=True,
)

_ARTICULATION_PROPS = sim_utils.ArticulationRootPropertiesCfg(
    enabled_self_collisions=False,
    solver_position_iteration_count=4,
    solver_velocity_iteration_count=0,
    sleep_threshold=0.005,
    stabilization_threshold=0.001,
)

# joint_drive=None: let the actuators= dict own all drive properties; the URDF
# converter default (target_type="position") conflicts with DCMotorCfg velocity drive.
_OSRACER_SPAWN_BASE = sim_utils.UrdfFileCfg(
    asset_path=OSRACER_URDF_PATH,
    usd_dir=f"{OSRACER_LAB_ASSETS_DATA_DIR}/Robots/OSRacer/blind",
    fix_base=False,
    merge_fixed_joints=True,
    root_link_name="base_link",
    joint_drive=None,
    rigid_props=_RIGID_PROPS,
    articulation_props=_ARTICULATION_PROPS,
)

OSRACER_CFG = ArticulationCfg(
    spawn=_OSRACER_SPAWN_BASE,
    init_state=OSRACER_INIT_STATE,
    actuators=OSRACER_ACTUATOR_CFG,
)

# Visual config uses a separate USD cache dir so the two never collide.
# The TiledCameraCfg is added at the scene level (not here) using the camera_joint
# offset: xyz=(0.12323, -0.017229, -0.053395), rpy=(-90°, 0°, -90°).
OSRACER_VISUAL_CFG = OSRACER_CFG.replace(
    spawn=OSRACER_CFG.spawn.replace(
        usd_dir=f"{OSRACER_LAB_ASSETS_DATA_DIR}/Robots/OSRacer/visual",
    )
)
