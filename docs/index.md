---
layout: home

hero:
  name: OSRacer Isaac Lab
  text: 从仿真训练到实车部署
  tagline: 面向 OSRacer 阿克曼车的 Isaac Lab 工作流：在 RTX 服务器上训练策略，在 MuJoCo / replay 中做离线验证，再把可控、可追踪的策略部署到 Jetson Orin Nano Super 8G。
  image:
    src: /osracer-mark.svg
    alt: OSRacer Isaac Lab
  actions:
    - theme: brand
      text: 从快速开始看起
      link: /getting-started
    - theme: alt
      text: 训练与导出
      link: /training
    - theme: alt
      text: 实车参数填写
      link: /real-car

features:
  - title: 服务器高并发训练
    details: Isaac Lab 训练负载放在 RTX 4080 SUPER 上，Jetson 只负责实车推理和传感器闭环。
  - title: 接口一致性检查
    details: 用 source snapshot、runtime checks、CSV replay 和 MuJoCo smoke test 提前发现上下位机不一致。
  - title: 面向实车的安全闸门
    details: 未完成轮径、转向角、相机内参、外参和延迟测量前，只允许离线验证或低速保守测试。
---

# 文档入口

## 你应该怎么读

<div class="doc-path">
  <a href="/osracer_lab/getting-started"><strong>只想先跑起来：</strong>完成安装、安装扩展、跑 smoke test。</a>
  <a href="/osracer_lab/training"><strong>要训练策略：</strong>先跑 drift，再跑 visual，最后导出策略。</a>
  <a href="/osracer_lab/sim2real"><strong>要上实车：</strong>按 Sim2Real / Jetson、实车参数和标定流程走。</a>
  <a href="/osracer_lab/deployment"><strong>要查接口：</strong>看运行时接口约定、硬件参数和 feat-demo 参数核对。</a>
</div>

## 当前推荐路线

<div class="metric-grid">
  <div class="metric-card">
    <strong>训练平台</strong>
    <div class="value">RTX 4080S</div>
    Isaac Lab 批量环境和策略导出。
  </div>
  <div class="metric-card">
    <strong>实车平台</strong>
    <div class="value">Jetson Orin</div>
    ROS 2、传感器和低延迟推理。
  </div>
  <div class="metric-card">
    <strong>初始限速</strong>
    <div class="value">0.3 m/s</div>
    首车测试前先保守闭环。
  </div>
  <div class="metric-card">
    <strong>控制接口</strong>
    <div class="value">Ackermann</div>
    策略输出速度和转向角。
  </div>
</div>

1. 在 RTX 4080 SUPER 服务器上跑 Isaac Lab，不把训练负载放到 Jetson。
2. 导出策略后，先用 CSV replay 和 MuJoCo smoke test 检查动作输出格式。
3. Jetson Orin Nano Super 8G 只做传感器、ROS、推理和实车闭环。
4. 未完成外参、相机标定、轮径和延迟测量前，只做保守低速测试。

## 任务环境

| Gym ID | 用途 | 新手建议 |
|---|---|---|
| `Isaac-OSRacerDriftRL-v0` | 无视觉漂移/控制训练 | 先从这里开始 |
| `Isaac-OSRacerVisualRL-v0` | 带相机输入的视觉策略训练 | 跑通 drift 后再做 |

## 当前硬件接口摘要

| 项 | 当前值 |
|---|---|
| ROS 运行环境 | JetPack 6.x / Ubuntu 22.04 / ROS 2 Humble |
| 串口 | `/dev/osrbot_base`, `460800` |
| 固件命令 | `v <speed_mps> <steering_deg>` |
| 默认遥测 | `stream sync`, `s/m/r/b` |
| 同步帧 | `s px py pz vx vy vz yaw qx qy qz qw ax ay az gx gy gz` |
| 固件版本 | ROS 启动时查询 `fw version` 并打印 `OSRCORE ProjectVer` |
| 初始实车限速 | `0.3 m/s` |

## 重要提醒

::: danger 不要跳过实车测量
当前仓库已经记录了很多来自固件和 ROS 的参数，但真实 sim2real 还需要测量整车质量、负载轮径、转向角、相机内参、传感器外参和串口延迟。
:::
