# OSRacer Isaac / Jetson 当前实现状态

日期：2026-06-24

本文记录 `osracer_lab`、`osracer feat-demo` 和 `osrcore` 当前已经实现和验证的内容。它不是推送授权；每次推送前仍必须重新检查本地 git 状态。

## 当前仓库状态

| 仓库 | 分支 | 状态 |
|---|---|---|
| `osracer_lab` | `main` | 公开仓库，已接入 VitePress 文档站 |
| `osrcore` | `main` | 参数快照基于 `729a6c2` |
| `osracer` | `feat-demo` | 参数快照基于 `a901398` |

## `osracer_lab` 已实现

- 策略导出：`scripts/export_osracer_policy.py`
- 硬件参数源：`source/osracer_lab_assets/osracer_lab_assets/hardware_params.py`
- 硬件参数 JSON 导出：`scripts/export_hardware_params.py`
- AR0234 相机配置辅助函数：`ar0234_pinhole_camera_cfg()`
- 25m 雷达平面扫描配置：`lidar_25m_planar_scan_cfg()`
- 仿真传感器接口一致性检查：`scripts/check_sim_sensor_contract.py`
- MuJoCo 运动学 sim2sim smoke：`scripts/mujoco_sim2sim_smoke.py`
- observation replay 到 MuJoCo：`scripts/run_sim2real_replay_pipeline.py`
- `osrcore` 和 `osracer feat-demo` 来源检查：`scripts/check_source_authority.py`
- 来源快照：`docs/source_authority_snapshot.json`
- 来源快照生成与校验：
  - `scripts/create_source_authority_snapshot.py`
  - `scripts/verify_source_authority_snapshot.py`
- 运行时接口一致性检查：`scripts/check_runtime_contract.py`
- sim2real readiness 汇总：`scripts/sim2real_readiness.py`
- 实车测量模板和校验：
  - `docs/real_car_measurements.template.json`
  - `scripts/validate_real_measurements.py`
  - `scripts/measurement_gap_report.py`
  - `scripts/check_measurement_consistency.py`
- 实车测量包和导入工具：
  - `scripts/create_measurement_pack.py`
  - `scripts/import_sensor_preflight_measurements.py`
  - `scripts/import_serial_latency_measurement.py`
  - `scripts/import_camera_info_calibration.py`
  - `scripts/import_measurement_session.py`
- 标定与 review pack：
  - `scripts/apply_sensor_extrinsics.py`
  - `scripts/plan_calibration_updates.py`
  - `scripts/export_measured_overlay.py`
  - `scripts/check_camera_calibration_overlay.py`
  - `scripts/create_calibration_review_pack.py`
  - `scripts/verify_calibration_review_pack.py`
- Jetson 部署包生成：`scripts/package_jetson_deployment.py`
- VitePress 文档站：
  - `package.json`
  - `docs/.vitepress/config.mts`
  - `docs/index.md`
  - `docs/en/index.md`

## `osracer feat-demo` 已实现

这些功能在 ROS 上位机仓库中维护，`osracer_lab` 只做接口和参数核对：

- TorchScript 推理节点和 `/ackermann_cmd` launch 路径
- 实车 observation 记录器
- CSV 策略 replay：`tools/policy_replay_csv.py`
- replay summary gate：`tools/policy_replay_summary.py`
- Jetson 预检查：`tools/jetson_preflight.sh`
- Jetson 环境报告：`tools/jetson_environment_report.py`
- Jetson measurement session：`tools/jetson_measurement_session.sh`
- 实车 readiness 检查：`tools/real_car_readiness_check.sh`
- Jetson runtime monitor 和 summary
- 部署包校验：`tools/verify_jetson_deployment.py`
- TensorRT 构建和性能 profiling 辅助工具
- 首车 runbook、go/no-go gate 和 evidence pack

## 已验证命令

`osracer_lab` 侧常用验证：

```bash
scripts/validate_osracer_lab.sh source-authority
scripts/validate_osracer_lab.sh source-authority-snapshot
scripts/validate_osracer_lab.sh runtime-contract
scripts/validate_osracer_lab.sh measurement-gap
scripts/validate_osracer_lab.sh measurement-consistency
scripts/validate_osracer_lab.sh sim2real-readiness
scripts/validate_osracer_lab.sh calibration-plan
scripts/validate_osracer_lab.sh measured-overlay
scripts/validate_osracer_lab.sh camera-calibration-overlay
python3 scripts/export_hardware_params.py --output /tmp/osracer_hardware_params.json
python3 scripts/mujoco_sim2sim_smoke.py --xml-out /tmp/osracer_overlay_smoke.xml
```

VitePress 文档验证：

```bash
npm ci
npm run docs:build
```

## 当前 readiness 结果

`scripts/validate_osracer_lab.sh sim2real-readiness` 当前预期仍会失败：

```text
sim2real_readiness: fail
[PASS] runtime_contract
[FAIL] strict_extrinsics
[FAIL] measured_sensor_extrinsics_applied
[FAIL] required_real_measurements
```

这是正常状态。当前代码适合离线 replay 和保守首车准备，还不能视为完成标定的闭环 sim2real。

## 标定闭环前阻塞项

1. 统一 `base_link -> camera_link`、`base_link -> laser`、`base_link -> imu_link` 的来源。
2. 从 `docs/real_car_measurements.template.json` 复制并填写 `docs/real_car_measurements.json`。
3. 通过 `scripts/validate_osracer_lab.sh real-measurements`。
4. 在实际 Orin Nano Super 8GB 上确认 ROS 2、`ackermann_msgs`、Torch / ONNX / TensorRT 运行时。
5. 采集实车被动 observation。
6. 用导出的策略 replay 实车 observation。
7. 用同一 observation 跑 MuJoCo action replay。
8. 先架空低速闭环，再落地低速测试。

## 推送前提醒

```bash
git status --short --branch
git diff --check
rg -n "<team-sensitive-patterns>" .
npm run docs:build
```

没有用户明确确认，不要推送任何仓库。
