---
layout: home

hero:
  name: OSRacer Isaac Lab
  text: From simulation training to real-car deployment
  tagline: "An Isaac Lab workflow for the OSRacer Ackermann vehicle: train on an RTX server, validate offline with MuJoCo and replay, then deploy traceable policies to Jetson Orin Nano Super 8G."
  image:
    src: /osracer-mark.svg
    alt: OSRacer Isaac Lab
  actions:
    - theme: brand
      text: Start here
      link: /en/getting-started
    - theme: alt
      text: Training and export
      link: /en/training
    - theme: alt
      text: Real-car parameters
      link: /en/real-car

features:
  - title: High-throughput server training
    details: Isaac Lab training runs on the RTX 4080 SUPER host. Jetson is reserved for sensing, ROS 2 runtime, and inference.
  - title: Interface consistency checks
    details: Source snapshots, runtime checks, CSV replay, and MuJoCo smoke tests catch host/firmware mismatches early.
  - title: Real-car safety gates
    details: Before wheel radius, steering, camera calibration, extrinsics, and latency are measured, use only offline validation or conservative low-speed tests.
---

# Documentation Entry

## How To Read This Site

<div class="doc-path">
  <a href="/osracer_lab/en/getting-started"><strong>Just make it run:</strong> install the extension and run a smoke test.</a>
  <a href="/osracer_lab/en/training"><strong>Train a policy:</strong> start with drift, then visual, then export.</a>
  <a href="/osracer_lab/en/sim2real"><strong>Prepare the car:</strong> follow Sim2Real / Jetson, real-car parameters, and calibration.</a>
  <a href="/osracer_lab/en/deployment"><strong>Check interfaces:</strong> read the runtime interface, hardware parameters, and feat-demo audit.</a>
</div>

## Recommended Route

<div class="metric-grid">
  <div class="metric-card">
    <strong>Training host</strong>
    <div class="value">RTX 4080S</div>
    Isaac Lab batched environments and policy export.
  </div>
  <div class="metric-card">
    <strong>Car computer</strong>
    <div class="value">Jetson Orin</div>
    ROS 2, sensors, and bounded inference.
  </div>
  <div class="metric-card">
    <strong>Initial speed</strong>
    <div class="value">0.3 m/s</div>
    Conservative first-drive limit.
  </div>
  <div class="metric-card">
    <strong>Control</strong>
    <div class="value">Ackermann</div>
    Policy outputs speed and steering angle.
  </div>
</div>

1. Train on the RTX 4080 SUPER host; do not move Isaac Lab training to Jetson.
2. After export, use CSV replay and MuJoCo smoke tests to check action formatting.
3. Use Jetson Orin Nano Super 8G for sensors, ROS 2, inference, and the real-car loop.
4. Before extrinsics, camera calibration, wheel radius, and latency are measured, keep tests conservative and low speed.

## Task Environments

| Gym ID | Purpose | Beginner advice |
|---|---|---|
| `Isaac-OSRacerDriftRL-v0` | Non-visual drift/control training | Start here |
| `Isaac-OSRacerVisualRL-v0` | Camera-based visual policy training | Run after drift works |

## Runtime Summary

| Item | Current value |
|---|---|
| ROS runtime | JetPack 6.x / Ubuntu 22.04 / ROS 2 Humble |
| Serial | `/dev/osrbot_base`, `460800` |
| Firmware command | `v <speed_mps> <steering_deg>` |
| Default telemetry | `stream sync`, `s/m/r/b` |
| Sync frame | `s px py pz vx vy vz yaw qx qy qz qw ax ay az gx gy gz` |
| Firmware version | ROS startup queries `fw version` and logs `OSRCORE ProjectVer` |
| Initial real-car speed limit | `0.3 m/s` |

::: danger Do not skip real measurements
The repository already records many firmware and ROS parameters, but calibrated sim2real still requires vehicle mass, loaded wheel radius, steering angle, camera intrinsics, sensor extrinsics, and serial latency.
:::
