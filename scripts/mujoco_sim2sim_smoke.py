#!/usr/bin/env python3
"""Generate and optionally compile a minimal OSRacer MuJoCo kinematic model.

This is a sim2sim contract smoke test, not a tuned contact dynamics model. It
keeps the MuJoCo side tied to the same chassis parameters used by IsaacLab and
Jetson deployment, then lets environments with `mujoco` installed compile and
step the MJCF.
"""

import argparse
import csv
import json
import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ASSETS_SRC = REPO_ROOT / "source" / "osracer_lab_assets"
if str(ASSETS_SRC) not in sys.path:
    sys.path.insert(0, str(ASSETS_SRC))

from osracer_lab_assets.hardware_params import hardware_summary


def parse_args():
    parser = argparse.ArgumentParser(description="Generate a minimal OSRacer MuJoCo kinematic MJCF.")
    parser.add_argument("--xml-out", required=True, help="Path to write the generated MJCF")
    parser.add_argument("--compile", action="store_true", help="Compile the generated MJCF with mujoco")
    parser.add_argument("--rollout-steps", type=int, default=0, help="Run N MuJoCo steps after compiling")
    parser.add_argument("--speed-mps", type=float, default=0.3, help="Rollout target speed")
    parser.add_argument("--steering-rad", type=float, default=0.0, help="Rollout target steering")
    parser.add_argument("--actions-csv", default=None, help="Replay speed_cmd/steering_cmd actions from CSV")
    parser.add_argument("--measured-overlay", default=None, help="Measured overlay JSON from scripts/export_measured_overlay.py")
    parser.add_argument("--steps-per-action", type=int, default=1, help="MuJoCo steps to apply each CSV action")
    parser.add_argument("--timestep", type=float, default=0.01)
    parser.add_argument("--mass-kg", type=float, default=3.0, help="Placeholder mass until measured")
    parser.add_argument("--wheel-width-m", type=float, default=0.025)
    return parser.parse_args()


def _geom_block(name, pos, size, rgba):
    return (
        f'      <geom name="{name}" type="box" pos="{pos}" size="{size}" '
        f'rgba="{rgba}" contype="1" conaffinity="1"/>\n'
    )


def _overlay_value(overlay, group, key):
    return overlay.get("measured_overlay", {}).get(group, {}).get(key)


def apply_measured_overlay(params, overlay_path):
    if not overlay_path:
        return params, {"enabled": False}
    with Path(overlay_path).open("r", encoding="utf-8") as f:
        overlay = json.load(f)
    params = json.loads(json.dumps(params))
    applied = {"enabled": True, "path": str(Path(overlay_path).resolve()), "fields": {}}

    chassis = params["chassis"]
    value = _overlay_value(overlay, "chassis", "front_track_m")
    if value is not None:
        chassis["rear_track_m"] = float(value)
        applied["fields"]["chassis.rear_track_m"] = "front_track_m"
    value = _overlay_value(overlay, "chassis", "tire_width_m")
    if value is not None:
        chassis["measured_tire_width_m"] = float(value)
        applied["fields"]["chassis.measured_tire_width_m"] = "tire_width_m"
    value = _overlay_value(overlay, "powertrain", "true_max_speed_mps")
    if value is not None:
        chassis["simulation_max_speed_mps"] = float(value)
        applied["fields"]["chassis.simulation_max_speed_mps"] = "true_max_speed_mps"
    value = _overlay_value(overlay, "steering", "true_max_steering_rad_left_right")
    if isinstance(value, dict):
        left = float(value["left_rad"])
        right = float(value["right_rad"])
        chassis["simulation_max_steering_rad"] = min(abs(left), abs(right))
        applied["fields"]["chassis.simulation_max_steering_rad"] = "true_max_steering_rad_left_right"
    elif isinstance(value, list) and len(value) >= 2:
        chassis["simulation_max_steering_rad"] = min(abs(float(value[0])), abs(float(value[1])))
        applied["fields"]["chassis.simulation_max_steering_rad"] = "true_max_steering_rad_left_right"

    mass = _overlay_value(overlay, "chassis", "full_vehicle_mass_kg_with_battery_jetson_sensors")
    if mass is not None:
        applied["mass_kg"] = float(mass)
    timing = overlay.get("measured_overlay", {}).get("timing", {})
    if timing:
        applied["timing"] = timing
    return params, applied


def build_mjcf(params, mass_kg, wheel_width_m, timestep, overlay_applied=None):
    chassis = params["chassis"]
    camera = params["camera_ar0234"]
    lidar_scan = params["lidar_planar_scan_cfg"]

    wheelbase = chassis["wheelbase_m"]
    rear_track = chassis["rear_track_m"]
    half_track = rear_track / 2.0
    front_x = wheelbase / 2.0
    rear_x = -wheelbase / 2.0
    steering_limit = chassis["simulation_max_steering_rad"]
    max_speed = chassis["simulation_max_speed_mps"]
    wheel_radius = chassis["wheel_radius_m"]
    wheel_width_m = float(chassis.get("measured_tire_width_m", wheel_width_m))
    overlay_applied = overlay_applied or {"enabled": False}

    body_length = wheelbase + 0.12
    body_width = rear_track + 0.08
    body_height = 0.08
    body_z = wheel_radius + body_height / 2.0

    return f"""<mujoco model="osracer_minimal">
  <compiler angle="radian" coordinate="local"/>
  <option timestep="{timestep:.6g}" integrator="RK4"/>

  <default>
    <joint damping="0.1"/>
    <geom contype="0" conaffinity="0"/>
  </default>

  <asset>
    <material name="body_mat" rgba="0.08 0.12 0.16 1"/>
    <material name="wheel_mat" rgba="0.02 0.02 0.02 1"/>
    <material name="sensor_mat" rgba="0.1 0.5 0.9 1"/>
  </asset>

  <worldbody>
    <geom name="ground" type="plane" size="10 10 0.05" rgba="0.4 0.4 0.4 1"/>
    <body name="base_link" pos="0 0 {body_z:.6g}">
      <joint name="base_x" type="slide" axis="1 0 0"/>
      <joint name="base_y" type="slide" axis="0 1 0"/>
      <joint name="base_yaw" type="hinge" axis="0 0 1"/>
      <inertial pos="0 0 0" mass="{mass_kg:.6g}" diaginertia="0.03 0.05 0.06"/>
{_geom_block("chassis", "0 0 0", f"{body_length / 2:.6g} {body_width / 2:.6g} {body_height / 2:.6g}", "0.08 0.12 0.16 1")}      <site name="camera_ar0234" pos="{front_x:.6g} 0 {body_height:.6g}" size="0.015" rgba="0.1 0.5 0.9 1"/>
      <site name="lidar_25m" pos="0 0 {body_height + 0.08:.6g}" size="0.02" rgba="0.9 0.4 0.1 1"/>
      <body name="front_left_wheel" pos="{front_x:.6g} {half_track:.6g} {-body_height / 2:.6g}" euler="1.57079632679 0 0">
        <geom name="front_left_wheel_geom" type="cylinder" size="{wheel_radius:.6g} {wheel_width_m / 2:.6g}" material="wheel_mat"/>
      </body>
      <body name="front_right_wheel" pos="{front_x:.6g} {-half_track:.6g} {-body_height / 2:.6g}" euler="1.57079632679 0 0">
        <geom name="front_right_wheel_geom" type="cylinder" size="{wheel_radius:.6g} {wheel_width_m / 2:.6g}" material="wheel_mat"/>
      </body>
      <body name="rear_left_wheel" pos="{rear_x:.6g} {half_track:.6g} {-body_height / 2:.6g}" euler="1.57079632679 0 0">
        <geom name="rear_left_wheel_geom" type="cylinder" size="{wheel_radius:.6g} {wheel_width_m / 2:.6g}" material="wheel_mat"/>
      </body>
      <body name="rear_right_wheel" pos="{rear_x:.6g} {-half_track:.6g} {-body_height / 2:.6g}" euler="1.57079632679 0 0">
        <geom name="rear_right_wheel_geom" type="cylinder" size="{wheel_radius:.6g} {wheel_width_m / 2:.6g}" material="wheel_mat"/>
      </body>
    </body>
  </worldbody>

  <actuator>
    <velocity name="base_x_velocity" joint="base_x" ctrlrange="{-max_speed:.6g} {max_speed:.6g}" kv="50"/>
    <velocity name="base_y_velocity" joint="base_y" ctrlrange="{-max_speed:.6g} {max_speed:.6g}" kv="50"/>
    <velocity name="base_yaw_rate" joint="base_yaw" ctrlrange="{-max_speed / wheelbase * 2.0:.6g} {max_speed / wheelbase * 2.0:.6g}" kv="20"/>
  </actuator>

  <!-- Contract metadata:
       action = [target_speed_mps, target_steering_rad]
       yaw_rate = speed / wheelbase * tan(steering)
       visual wheel_radius_m={wheel_radius}
       camera = {camera["sensor"]}, advertised_fov_deg={camera["advertised_fov_deg"]}
       lidar_horizontal_fov_deg={lidar_scan["horizontal_fov_deg"]}
       lidar_angular_resolution_deg={lidar_scan["angular_resolution_deg"]}
       lidar_scan_rate_hz={lidar_scan["scan_rate_hz"]}
       lidar_ray_count={lidar_scan["ray_count"]}
       lidar_max_range_m={lidar_scan["max_range_m"]}
       measured_overlay_enabled={overlay_applied.get("enabled", False)}
       measured_overlay_fields={json.dumps(overlay_applied.get("fields", {}), sort_keys=True)}
  -->
</mujoco>
"""


def _load_mujoco():
    try:
        import mujoco
    except ImportError as exc:
        raise RuntimeError("mujoco is not installed in this Python environment") from exc
    return mujoco


def compile_model(xml_path):
    mujoco = _load_mujoco()

    model = mujoco.MjModel.from_xml_path(str(xml_path))
    return model.nq, model.nv, model.nu


def clamp_action(params, speed_mps, steering_rad):
    chassis = params["chassis"]
    speed = max(0.0, min(speed_mps, chassis["simulation_max_speed_mps"]))
    steering = max(
        -chassis["simulation_max_steering_rad"],
        min(steering_rad, chassis["simulation_max_steering_rad"]),
    )
    return speed, steering


def step_ackermann(mujoco, model, data, params, speed_mps, steering_rad):
    speed, steering = clamp_action(params, speed_mps, steering_rad)
    yaw = data.qpos[2]
    yaw_rate = 0.0 if abs(steering) < 1e-9 else speed / params["chassis"]["wheelbase_m"] * math.tan(steering)
    data.ctrl[:] = [speed * math.cos(yaw), speed * math.sin(yaw), yaw_rate]
    mujoco.mj_step(model, data)
    return speed, steering


def rollout_metrics(data, start_xy, steps, speed_mps=None, steering_rad=None, rows=None):
    end_xy = data.qpos[:2].copy()
    distance = ((end_xy[0] - start_xy[0]) ** 2 + (end_xy[1] - start_xy[1]) ** 2) ** 0.5
    metrics = {
        "steps": steps,
        "time_s": data.time,
        "distance_m": distance,
        "final_x_m": end_xy[0],
        "final_y_m": end_xy[1],
    }
    if speed_mps is not None:
        metrics["speed_mps"] = speed_mps
    if steering_rad is not None:
        metrics["steering_rad"] = steering_rad
    if rows is not None:
        metrics["rows"] = rows
    return metrics


def run_rollout(xml_path, params, steps, speed_mps, steering_rad):
    mujoco = _load_mujoco()
    model = mujoco.MjModel.from_xml_path(str(xml_path))
    data = mujoco.MjData(model)

    speed, steering = clamp_action(params, speed_mps, steering_rad)
    start_xy = data.qpos[:2].copy()
    for _ in range(steps):
        step_ackermann(mujoco, model, data, params, speed, steering)
    return rollout_metrics(data, start_xy, steps, speed_mps=speed, steering_rad=steering)


def _read_float(row, names, row_number):
    for name in names:
        if name in row and row[name] != "":
            value = float(row[name])
            if not math.isfinite(value):
                raise ValueError(f"row {row_number}: non-finite {name}={row[name]!r}")
            return value
    raise ValueError(f"row {row_number}: missing one of {', '.join(names)}")


def read_actions_csv(path):
    actions = []
    with Path(path).open(newline="") as input_file:
        reader = csv.DictReader(input_file)
        if not reader.fieldnames:
            raise ValueError("actions CSV has no header")
        for row_number, row in enumerate(reader, start=2):
            speed = _read_float(row, ("speed_cmd", "target_speed_mps", "speed_mps", "speed"), row_number)
            steering = _read_float(
                row,
                ("steering_cmd", "target_steering_rad", "steering_rad", "steering"),
                row_number,
            )
            actions.append((speed, steering))
    if not actions:
        raise ValueError("actions CSV has no rows")
    return actions


def run_actions_csv_rollout(xml_path, params, actions_path, steps_per_action):
    mujoco = _load_mujoco()
    model = mujoco.MjModel.from_xml_path(str(xml_path))
    data = mujoco.MjData(model)
    actions = read_actions_csv(actions_path)

    start_xy = data.qpos[:2].copy()
    steps = 0
    for speed, steering in actions:
        for _ in range(steps_per_action):
            step_ackermann(mujoco, model, data, params, speed, steering)
            steps += 1
    metrics = rollout_metrics(data, start_xy, steps)
    return {"rows": len(actions), **metrics}


def main():
    args = parse_args()
    if args.timestep <= 0.0:
        raise ValueError("--timestep must be > 0")
    if args.mass_kg <= 0.0:
        raise ValueError("--mass-kg must be > 0")
    if args.wheel_width_m <= 0.0:
        raise ValueError("--wheel-width-m must be > 0")
    if args.rollout_steps < 0:
        raise ValueError("--rollout-steps must be >= 0")
    if args.steps_per_action <= 0:
        raise ValueError("--steps-per-action must be > 0")

    xml_path = Path(args.xml_out)
    xml_path.parent.mkdir(parents=True, exist_ok=True)
    params, overlay_applied = apply_measured_overlay(hardware_summary(), args.measured_overlay)
    mass_kg = float(overlay_applied.get("mass_kg", args.mass_kg))
    xml_path.write_text(build_mjcf(params, mass_kg, args.wheel_width_m, args.timestep, overlay_applied))
    print(f"wrote {xml_path}")

    if args.compile or args.rollout_steps or args.actions_csv:
        nq, nv, nu = compile_model(xml_path)
        print(f"compiled nq={nq} nv={nv} nu={nu}")
    if args.rollout_steps:
        metrics = run_rollout(xml_path, params, args.rollout_steps, args.speed_mps, args.steering_rad)
        print(
            "rollout "
            + " ".join(f"{key}={value:.6g}" if isinstance(value, float) else f"{key}={value}" for key, value in metrics.items())
        )
    if args.actions_csv:
        metrics = run_actions_csv_rollout(xml_path, params, args.actions_csv, args.steps_per_action)
        print(
            "actions_csv_rollout "
            + " ".join(f"{key}={value:.6g}" if isinstance(value, float) else f"{key}={value}" for key, value in metrics.items())
        )


if __name__ == "__main__":
    main()
