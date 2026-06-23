# CHANGELOG

## [Unreleased]

### Changed
- **Independence**: inlined all WheeledLab MDP utilities into `osracer_lab_tasks/mdp/`
  — `RCCarRWDActionCfg`, `AckermannAction`, `RCCarRWDAction`, `increase_reward_weight_over_time`,
    `root_euler_xyz`, `BlindObsCfg`, `reset_root_state_along_track`, `reset_root_state`,
    `TraversabilityHashmapUtil`, terrain geometry generation.
  — `wheeledlab` and `wheeledlab_tasks` are **no longer runtime dependencies**.
- **Bug fix**: `root_link_name=None` with `merge_fixed_joints=True` lets the URDF importer
  merge `base_link` into the effective `base_footprint` articulation root.
- `osracer_lab_tasks/setup.py` dependency list cleaned (`scipy` added, `wheeledlab*` removed).
- `osracer_lab_tasks/common/__init__.py` now also exports `BlindObsCfg`.
- Added deployment notes for mapping trained policy actions to the OSRacer ROS 2
  `ackermann_cmd` bridge and firmware serial command format.

## [0.1.0]

- Initial IsaacLab adapter for OSRacer.
- Drift RL task (`Isaac-OSRacerDriftRL-v0`) with stadium track, domain randomisation, curriculum.
- Visual RL task (`Isaac-OSRacerVisualRL-v0`) with procedural traversability terrain + tiled camera.
- RSL-RL training script (`scripts/train_osracer_drift.py`).
