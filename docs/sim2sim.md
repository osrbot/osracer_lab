# Sim2Sim

Sim2Sim 的目的不是替代 Isaac Lab 训练，而是用第二个简单仿真器检查动作接口和参数一致性。

## 当前路径

| 阶段 | 工具 |
|---|---|
| Isaac Lab 训练 | `scripts/train_osracer_drift.py` |
| 策略导出 | `scripts/export_osracer_policy.py` |
| 策略 CSV replay | `scripts/run_sim2real_replay_pipeline.py` |
| MuJoCo smoke | `scripts/mujoco_sim2sim_smoke.py` |

## MuJoCo smoke

```bash
cd ~/osracer_ws/osracer_lab
python3 scripts/mujoco_sim2sim_smoke.py \
  --xml-out /tmp/osracer_mujoco_smoke.xml
```

带实测 overlay：

```bash
python3 scripts/mujoco_sim2sim_smoke.py \
  --xml-out /tmp/osracer_overlay_smoke.xml \
  --measured-overlay /tmp/osracer_measured_overlay.json
```

## 要检查什么

- action 是否仍是 `[target_speed_mps, target_steering_rad]`
- 最大速度是否被正确夹紧
- 最大转向是否被正确夹紧
- 轮距、轴距、轮径是否来自同一份参数来源
- policy replay 输出是否有 NaN 或超过实车边界

## 不要误解

MuJoCo smoke 不是高保真实车仿真。它是接口一致性检查器，用来尽早发现“策略输出和实车桥接不一致”这类问题。
