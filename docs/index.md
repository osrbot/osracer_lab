# OSRacer Isaac Lab

<div class="hero" markdown="1">
  <div markdown="1">
  <span class="hero-kicker">Isaac Lab / Jetson / Sim2Real</span>

  # 面向 OSRacer 阿克曼车的仿真训练与实车部署流程

  `osracer_lab` 用来在 RTX 服务器上训练 OSRacer 策略，并把策略、硬件参数、测量数据和 Jetson 部署流程连起来。它不是底层固件，也不是 ROS 上位机功能包，而是训练、验证、导出和 sim2real 的工作区。

  <div class="hero-actions" markdown="1">
  [从快速开始看起](getting-started.md)
  [训练与导出](training.md)
  [实车参数填写](real-car.md)
  </div>
  </div>
  <div class="hero-panel" markdown="1">
  **三层代码关系**

  | 层 | 仓库 | 用途 |
  |---|---|---|
  | 固件 | `osrbot/osrcore` | ESP32 底盘控制、IMU、编码器、串口协议 |
  | ROS | `osrbot/osracer` `feat-demo` | Jetson 上位机、传感器、推理、实车工具 |
  | 训练 | `osrbot/osracer_lab` | Isaac Lab 训练、导出、sim2sim、sim2real 验证 |
  </div>
</div>

## 你应该怎么读

<ol class="path-steps" markdown="1">
  <li><strong>只想先跑起来：</strong>看 <a href="getting-started/">快速开始</a>，完成安装、安装扩展、跑 smoke test。</li>
  <li><strong>要训练策略：</strong>看 <a href="training/">训练与导出</a>，先跑 drift，再跑 visual。</li>
  <li><strong>要上实车：</strong>看 <a href="real-car/">实车参数</a>、<a href="sim2real/">Sim2Real / Jetson</a>、<a href="calibration/">标定流程</a>。</li>
  <li><strong>要查协议：</strong>看 <a href="hardware_parameters/">硬件参数</a> 和 <a href="deployment/">部署合同</a>。</li>
</ol>

## 当前推荐路线

<div class="card-grid" markdown="1">
  <div class="info-card" markdown="1">
  ### 1. 服务器训练
  在 RTX 4080 SUPER 服务器上跑 Isaac Lab。不要把训练负载放到 Jetson 上。
  </div>
  <div class="info-card" markdown="1">
  ### 2. 离线验证
  导出策略后，先用 CSV replay 和 MuJoCo smoke test 检查动作合同。
  </div>
  <div class="info-card" markdown="1">
  ### 3. Jetson 推理
  Jetson Orin Nano Super 8G 只做传感器、ROS、推理和实车闭环。
  </div>
  <div class="info-card" markdown="1">
  ### 4. 低速首车
  未完成外参、相机标定、轮径和延迟测量前，只做保守低速测试。
  </div>
</div>

## 任务环境

| Gym ID | 用途 | 新手建议 |
|---|---|---|
| `Isaac-OSRacerDriftRL-v0` | 无视觉漂移/控制训练 | 先从这里开始 |
| `Isaac-OSRacerVisualRL-v0` | 带相机输入的视觉策略训练 | 跑通 drift 后再做 |

## 当前硬件合同摘要

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

!!! warning "不要跳过实车测量"
    当前仓库已经记录了很多来自固件和 ROS 的参数，但真实 sim2real 还需要测量整车质量、负载轮径、转向角、相机内参、传感器外参和串口延迟。
