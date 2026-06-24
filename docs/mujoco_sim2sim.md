# MuJoCo Sim2Sim 验证

`osracer_lab` 仍以 Isaac Lab 作为高并发训练仿真器。MuJoCo 在这里作为第二仿真器，用来尽早发现动作接口、几何参数和动力学假设中的明显错误。

## 当前范围

当前 MuJoCo 支持是运动学 smoke test，不是高保真实车仿真：

- 生成一个最小 OSRacer MuJoCo XML。
- 保持动作接口为 `[target_speed_mps, target_steering_rad]`。
- 可读取 measured overlay，覆盖部分实测参数。
- 可从 CSV replay 中读取策略输出，检查速度和转向是否合理。

## 基本命令

生成 XML：

```bash
python3 scripts/mujoco_sim2sim_smoke.py --xml-out /tmp/osracer_minimal.xml
```

带 measured overlay：

```bash
python3 scripts/mujoco_sim2sim_smoke.py \
  --xml-out /tmp/osracer_overlay.xml \
  --measured-overlay /tmp/osracer_measured_overlay.json
```

如果本机装了 MuJoCo Python 包，可加 `--compile` 做 XML 编译检查：

```bash
python3 scripts/mujoco_sim2sim_smoke.py --xml-out /tmp/osracer_minimal.xml --compile
```

## Replay 流程

策略 replay CSV 需要包含：

| 列 | 含义 |
|---|---|
| `speed_cmd` | 策略输出速度 |
| `steering_cmd` | 策略输出转向 |

这些列来自 `osracer feat-demo` 中的 `tools/policy_replay_csv.py`。

执行 replay pipeline：

```bash
python3 scripts/run_sim2real_replay_pipeline.py \
  --policy-replay-csv /tmp/policy_replay.csv \
  --output-dir /tmp/osracer_sim2real_replay
```

输出通常包括：

```text
/tmp/osracer_sim2real_replay/policy_replay.csv
/tmp/osracer_sim2real_replay/mujoco_replay.xml
```

## 重点检查

- 策略输出是否超出仿真动作范围。
- 转向符号是否和 ROS bridge / 固件一致。
- 速度单位是否始终是 `m/s`。
- 转向单位是否在策略侧为弧度，固件侧为角度。
- overlay 后的轮径、轴距、轮距是否和实测值一致。

## 下一步

1. 用真实 observation replay 驱动 MuJoCo。
2. 加入更真实的轮胎和转向响应模型。
3. 把 MuJoCo 检查接入 sim2real readiness gate。
4. 与实车低速日志做对比，确认误差范围。
