#!/usr/bin/env python3
"""Generate and optionally compile a minimal OSRacer MuJoCo model.

This is a sim2sim contract smoke test, not a tuned dynamics model. It keeps the
MuJoCo side tied to the same chassis parameters used by IsaacLab and Jetson
deployment, then lets environments with `mujoco` installed compile the MJCF.
"""

import argparse
from pathlib import Path

from osracer_lab_assets.hardware_params import hardware_summary


def parse_args():
    parser = argparse.ArgumentParser(description="Generate a minimal OSRacer MuJoCo MJCF.")
    parser.add_argument("--xml-out", required=True, help="Path to write the generated MJCF")
    parser.add_argument("--compile", action="store_true", help="Compile the generated MJCF with mujoco")
    parser.add_argument("--timestep", type=float, default=0.01)
    parser.add_argument("--mass-kg", type=float, default=3.0, help="Placeholder mass until measured")
    parser.add_argument("--wheel-width-m", type=float, default=0.025)
    return parser.parse_args()


def _geom_block(name, pos, size, rgba):
    return (
        f'      <geom name="{name}" type="box" pos="{pos}" size="{size}" '
        f'rgba="{rgba}" contype="1" conaffinity="1"/>\n'
    )


def build_mjcf(params, mass_kg, wheel_width_m, timestep):
    chassis = params["chassis"]
    camera = params["camera_ar0234"]
    lidar = params["lidar_25m"]

    wheelbase = chassis["wheelbase_m"]
    rear_track = chassis["rear_track_m"]
    wheel_radius = chassis["wheel_radius_m"]
    half_track = rear_track / 2.0
    front_x = wheelbase / 2.0
    rear_x = -wheelbase / 2.0
    steering_limit = chassis["simulation_max_steering_rad"]
    max_speed = chassis["simulation_max_speed_mps"]

    body_length = wheelbase + 0.12
    body_width = rear_track + 0.08
    body_height = 0.08
    body_z = wheel_radius + body_height / 2.0

    return f"""<mujoco model="osracer_minimal">
  <compiler angle="radian" coordinate="local"/>
  <option timestep="{timestep:.6g}" integrator="RK4"/>

  <default>
    <joint damping="0.02"/>
    <geom friction="1.2 0.02 0.001" density="300"/>
  </default>

  <asset>
    <material name="body_mat" rgba="0.08 0.12 0.16 1"/>
    <material name="wheel_mat" rgba="0.02 0.02 0.02 1"/>
    <material name="sensor_mat" rgba="0.1 0.5 0.9 1"/>
  </asset>

  <worldbody>
    <geom name="ground" type="plane" size="10 10 0.05" rgba="0.4 0.4 0.4 1"/>
    <body name="base_link" pos="0 0 {body_z:.6g}">
      <freejoint name="base_free"/>
      <inertial pos="0 0 0" mass="{mass_kg:.6g}" diaginertia="0.03 0.05 0.06"/>
{_geom_block("chassis", "0 0 0", f"{body_length / 2:.6g} {body_width / 2:.6g} {body_height / 2:.6g}", "0.08 0.12 0.16 1")}      <site name="camera_ar0234" pos="{front_x:.6g} 0 {body_height:.6g}" size="0.015" rgba="0.1 0.5 0.9 1"/>
      <site name="lidar_25m" pos="0 0 {body_height + 0.08:.6g}" size="0.02" rgba="0.9 0.4 0.1 1"/>
      <body name="front_left_steer" pos="{front_x:.6g} {half_track:.6g} {-body_height / 2:.6g}">
        <joint name="front_left_steer_joint" type="hinge" axis="0 0 1" range="{-steering_limit:.6g} {steering_limit:.6g}" limited="true"/>
        <body name="front_left_wheel" euler="1.57079632679 0 0">
          <joint name="front_left_wheel_joint" type="hinge" axis="0 0 1"/>
          <geom name="front_left_wheel_geom" type="cylinder" size="{wheel_radius:.6g} {wheel_width_m / 2:.6g}" material="wheel_mat"/>
        </body>
      </body>
      <body name="front_right_steer" pos="{front_x:.6g} {-half_track:.6g} {-body_height / 2:.6g}">
        <joint name="front_right_steer_joint" type="hinge" axis="0 0 1" range="{-steering_limit:.6g} {steering_limit:.6g}" limited="true"/>
        <body name="front_right_wheel" euler="1.57079632679 0 0">
          <joint name="front_right_wheel_joint" type="hinge" axis="0 0 1"/>
          <geom name="front_right_wheel_geom" type="cylinder" size="{wheel_radius:.6g} {wheel_width_m / 2:.6g}" material="wheel_mat"/>
        </body>
      </body>
      <body name="rear_left_wheel" pos="{rear_x:.6g} {half_track:.6g} {-body_height / 2:.6g}" euler="1.57079632679 0 0">
        <joint name="rear_left_wheel_joint" type="hinge" axis="0 0 1"/>
        <geom name="rear_left_wheel_geom" type="cylinder" size="{wheel_radius:.6g} {wheel_width_m / 2:.6g}" material="wheel_mat"/>
      </body>
      <body name="rear_right_wheel" pos="{rear_x:.6g} {-half_track:.6g} {-body_height / 2:.6g}" euler="1.57079632679 0 0">
        <joint name="rear_right_wheel_joint" type="hinge" axis="0 0 1"/>
        <geom name="rear_right_wheel_geom" type="cylinder" size="{wheel_radius:.6g} {wheel_width_m / 2:.6g}" material="wheel_mat"/>
      </body>
    </body>
  </worldbody>

  <actuator>
    <position name="front_left_steering" joint="front_left_steer_joint" ctrlrange="{-steering_limit:.6g} {steering_limit:.6g}" kp="3"/>
    <position name="front_right_steering" joint="front_right_steer_joint" ctrlrange="{-steering_limit:.6g} {steering_limit:.6g}" kp="3"/>
    <velocity name="rear_left_wheel_speed" joint="rear_left_wheel_joint" ctrlrange="0 {max_speed / wheel_radius:.6g}" kv="1"/>
    <velocity name="rear_right_wheel_speed" joint="rear_right_wheel_joint" ctrlrange="0 {max_speed / wheel_radius:.6g}" kv="1"/>
  </actuator>

  <!-- Contract metadata:
       action = [target_speed_mps, target_steering_rad]
       camera = {camera["sensor"]}, advertised_fov_deg={camera["advertised_fov_deg"]}
       lidar_horizontal_fov_deg={lidar["horizontal_fov_deg"]}
  -->
</mujoco>
"""


def compile_model(xml_path):
    try:
        import mujoco
    except ImportError as exc:
        raise RuntimeError("mujoco is not installed in this Python environment") from exc

    model = mujoco.MjModel.from_xml_path(str(xml_path))
    return model.nq, model.nv, model.nu


def main():
    args = parse_args()
    if args.timestep <= 0.0:
        raise ValueError("--timestep must be > 0")
    if args.mass_kg <= 0.0:
        raise ValueError("--mass-kg must be > 0")
    if args.wheel_width_m <= 0.0:
        raise ValueError("--wheel-width-m must be > 0")

    xml_path = Path(args.xml_out)
    xml_path.parent.mkdir(parents=True, exist_ok=True)
    xml_path.write_text(build_mjcf(hardware_summary(), args.mass_kg, args.wheel_width_m, args.timestep))
    print(f"wrote {xml_path}")

    if args.compile:
        nq, nv, nu = compile_model(xml_path)
        print(f"compiled nq={nq} nv={nv} nu={nu}")


if __name__ == "__main__":
    main()
