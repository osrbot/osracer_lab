# Troubleshooting

## OSRacer Tasks Are Missing

Check editable installs:

```bash
cd ~/rlgpu_ws/IsaacLab
./isaaclab.sh -p -m pip install -e ~/osracer_ws/osracer_lab/source/osracer_lab_assets
./isaaclab.sh -p -m pip install -e ~/osracer_ws/osracer_lab/source/osracer_lab_tasks
./isaaclab.sh -p -m pip install -e ~/osracer_ws/osracer_lab/source/osracer_lab_rl
./isaaclab.sh -p scripts/environments/list_envs.py | grep OSRacer
```

## Visual Task Crashes

Check first:

- Isaac Sim version.
- NVIDIA driver and Vulkan.
- Whether drift task works.
- Whether `--num_envs` is too high for the GPU.

On the current development host, Isaac Sim 5.1 headless camera tasks were verified with NVIDIA driver `580.159.03`.

## ROS Has No Odom / IMU

Check:

- `/dev/osrbot_base` exists.
- Serial baud is `460800`.
- Firmware stream mode is `stream sync`.
- `osracer_bringup chassis_ackermann.launch.py` is running.

## Firmware Version Log Is Missing

The ROS bridge queries:

```text
fw version
```

Expected log contains `OSRCORE ProjectVer`. If it is missing, verify firmware version support and serial startup mode.

## `sim2real-readiness` Fails

This is expected before measurements are complete.

Common failing gates:

- required real measurements
- strict extrinsics
- measured sensor extrinsics applied
- camera calibration overlay

Run:

```bash
scripts/validate_osracer_lab.sh measurement-gap
scripts/validate_osracer_lab.sh sim2real-readiness
```
