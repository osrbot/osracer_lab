# 训练与导出

建议先训练 drift 任务，再进入 visual 任务。

## Drift 训练

小规模验证：

```bash
cd ~/osracer_ws/osracer_lab
~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/train_osracer_drift.py \
  --headless --num_envs 64 --max_iterations 2
```

RTX 4080 SUPER 推荐基线：

```bash
cd ~/osracer_ws/osracer_lab
~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/train_osracer_drift.py \
  --headless --num_envs 2048 --max_iterations 2000
```

当前经验：

| `num_envs` | 结论 |
|---:|---|
| 1024 | 稳定，但 GPU 利用不足 |
| 2048 | 推荐 drift 基线 |
| 4096 | 可运行，但吞吐波动更大 |
| 8192 | 初始化和 PhysX/CPU 同步成本明显，不默认推荐 |

## Visual 训练

视觉任务需要相机渲染，先确认 headless camera 检查通过。

保守基线：

```bash
cd ~/osracer_ws/osracer_lab
~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/train_osracer_drift.py \
  --task Isaac-OSRacerVisualRL-v0 \
  --headless --num_envs 256
```

更高吞吐探测：

```bash
cd ~/osracer_ws/osracer_lab
~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/train_osracer_drift.py \
  --task Isaac-OSRacerVisualRL-v0 \
  --headless --num_envs 512
```

## 继续训练

```bash
cd ~/osracer_ws/osracer_lab
~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/train_osracer_drift.py \
  --resume logs/rsl_rl/osracer_drift/model_1000.pt
```

## 导出策略

部署候选策略应从不含仿真真值的 task 导出。TorchScript：

```bash
cd ~/osracer_ws/osracer_lab
~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/export_osracer_policy.py \
  --headless \
  --task Isaac-OSRacerVisualRL-v0 \
  --checkpoint logs/rsl_rl/osracer_visual/<run>/model_1999.pt
```

ONNX：

```bash
cd ~/osracer_ws/osracer_lab
~/rlgpu_ws/IsaacLab/isaaclab.sh -p scripts/export_osracer_policy.py \
  --headless --format onnx \
  --task Isaac-OSRacerVisualRL-v0 \
  --checkpoint logs/rsl_rl/osracer_visual/<run>/model_1999.pt
```

如果只是导出 drift 仿真研究 artifact，必须显式加 `--allow-sim-only-observations`。该导出不能直接用于实车闭环。

## 导出后不要直接上车

导出后至少跑：

```bash
scripts/validate_osracer_lab.sh policy-observation-contract --task Isaac-OSRacerVisualRL-v0
scripts/validate_osracer_lab.sh runtime-contract
scripts/validate_osracer_lab.sh measurement-gap
```

如果 `measurement-gap` 还有缺项，策略只能进入离线 replay 或低速保守测试，不能当作完成 sim2real。
