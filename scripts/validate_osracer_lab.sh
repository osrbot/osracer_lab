#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ISAACLAB_SH="${ISAACLAB_SH:-$HOME/rlgpu_ws/IsaacLab/isaaclab.sh}"
TRAIN_SCRIPT="$ROOT_DIR/scripts/train_osracer_drift.py"

usage() {
    cat <<'EOF'
Usage: scripts/validate_osracer_lab.sh [target]

Targets:
  static          Compile OSRacer Python sources.
  drift-smoke     Run a short drift training check.
  visual-smoke    Run a short camera/visual training check.
  visual-perf     Run the RTX 4080 SUPER visual throughput probe.
  export-smoke    Export the verified drift checkpoint to TorchScript.
  source-authority
                  Check source-of-truth repos: osrcore firmware and osracer feat-demo.
  runtime-contract
                  Check shared hardware/runtime parameters against osracer.
  sim-sensor-contract
                  Check Isaac/MuJoCo sensor configs against hardware_params.py.
  real-measurements
                  Validate real-car measurement JSON values and sources.
  measurement-seed
                  Create docs/real_car_measurements.json from template plus known repo facts.
  measurement-pack
                  Create a field measurement pack for manual sim2real values.
  import-sensor-preflight
                  Import Jetson sensor_summary.json evidence into measurement JSON.
  import-serial-latency
                  Import serial_latency_probe.py JSON into measurement JSON.
  import-measurement-session
                  Import jetson_measurement_session.sh manifest into measurement JSON.
  sim2real-readiness
                  Summarize sim2real gates without failing on incomplete gates.
  sim2real-ready-strict
                  Fail unless all sim2real readiness gates pass.
  calibration-plan
                  Plan repo updates from measured parameters without writing files.
  measured-overlay
                  Export measured parameter overlay JSON without mutating source files.
  sensor-extrinsics-check
                  Compare measured sensor extrinsics against URDF/static TF.
  sensor-extrinsics-write
                  Write measured sensor extrinsics into URDF/static TF/hardware params.
  drift-baseline  Run the verified long drift baseline.
  all-smoke       Run static + drift-smoke + visual-smoke.

Environment overrides:
  ISAACLAB_SH=/path/to/isaaclab.sh
  SMOKE_ITERS=5
  DRIFT_SMOKE_ENVS=128
  VISUAL_SMOKE_ENVS=64
  VISUAL_PERF_ENVS=512
  VISUAL_PERF_ITERS=10
  EXPORT_CHECKPOINT=logs/rsl_rl/osracer_drift/2026-06-23_17-05-26/model_1999.pt
  EXPORT_OUTPUT_DIR=/tmp/osracer_policy_export_smoke
  OSRACER_ROOT=../osracer
  OSRCORE_ROOT=/path/to/osrcore
  MEASUREMENTS_FILE=docs/real_car_measurements.json
  MEASUREMENT_SEED_OUTPUT=docs/real_car_measurements.json
  SENSOR_SUMMARY_FILE=/path/to/sensor_summary.json
  SERIAL_LATENCY_FILE=/path/to/serial_latency.json
  MEASUREMENT_SESSION_FILE=/path/to/measurement_session.json
  MEASUREMENT_PACK_OUTPUT=/tmp/osracer_real_measurement_pack
  MEASURED_OVERLAY_OUTPUT=/tmp/osracer_measured_overlay.json
  DRIFT_BASELINE_ENVS=2048
  DRIFT_BASELINE_ITERS=2000
EOF
}

run_static() {
    cd "$ROOT_DIR"
    mapfile -t python_files < <(
        find scripts source -type f -name '*.py' ! -path '*/__pycache__/*' | sort
    )
    python3 -m py_compile "${python_files[@]}"
}

run_train() {
    "$ISAACLAB_SH" -p "$TRAIN_SCRIPT" "$@"
}

target="${1:-all-smoke}"

case "$target" in
    -h|--help|help)
        usage
        ;;
    static)
        run_static
        ;;
    drift-smoke)
        run_train --headless \
            --num_envs "${DRIFT_SMOKE_ENVS:-128}" \
            --max_iterations "${SMOKE_ITERS:-5}"
        ;;
    visual-smoke)
        run_train --task Isaac-OSRacerVisualRL-v0 --headless \
            --num_envs "${VISUAL_SMOKE_ENVS:-64}" \
            --max_iterations "${SMOKE_ITERS:-5}"
        ;;
    visual-perf)
        run_train --task Isaac-OSRacerVisualRL-v0 --headless \
            --num_envs "${VISUAL_PERF_ENVS:-512}" \
            --max_iterations "${VISUAL_PERF_ITERS:-10}"
        ;;
    export-smoke)
        "$ISAACLAB_SH" -p "$ROOT_DIR/scripts/export_osracer_policy.py" --headless \
            --checkpoint "${EXPORT_CHECKPOINT:-logs/rsl_rl/osracer_drift/2026-06-23_17-05-26/model_1999.pt}" \
            --output_dir "${EXPORT_OUTPUT_DIR:-/tmp/osracer_policy_export_smoke}" \
            --format jit
        ;;
    source-authority)
        args=(--osracer-root "${OSRACER_ROOT:-$ROOT_DIR/../osracer}")
        if [[ -n "${OSRCORE_ROOT:-}" ]]; then
            args+=(--osrcore-root "$OSRCORE_ROOT")
        fi
        python3 "$ROOT_DIR/scripts/check_source_authority.py" "${args[@]}"
        ;;
    runtime-contract)
        python3 "$ROOT_DIR/scripts/check_runtime_contract.py" \
            --osracer-root "${OSRACER_ROOT:-$ROOT_DIR/../osracer}"
        ;;
    sim-sensor-contract)
        python3 "$ROOT_DIR/scripts/check_sim_sensor_contract.py"
        ;;
    real-measurements)
        if [[ -z "${MEASUREMENTS_FILE:-}" ]]; then
            echo "MEASUREMENTS_FILE is required" >&2
            exit 2
        fi
        python3 "$ROOT_DIR/scripts/validate_real_measurements.py" "$MEASUREMENTS_FILE"
        ;;
    measurement-seed)
        python3 "$ROOT_DIR/scripts/collect_real_measurement_seed.py" \
            --osracer-root "${OSRACER_ROOT:-$ROOT_DIR/../osracer}" \
            --output "${MEASUREMENT_SEED_OUTPUT:-$ROOT_DIR/docs/real_car_measurements.json}"
        ;;
    measurement-pack)
        args=(--output-dir "${MEASUREMENT_PACK_OUTPUT:-/tmp/osracer_real_measurement_pack}" --overwrite)
        if [[ -n "${MEASUREMENTS_FILE:-}" ]]; then
            args+=(--measurements "$MEASUREMENTS_FILE")
        fi
        python3 "$ROOT_DIR/scripts/create_measurement_pack.py" "${args[@]}"
        ;;
    import-sensor-preflight)
        if [[ -z "${MEASUREMENTS_FILE:-}" || -z "${SENSOR_SUMMARY_FILE:-}" ]]; then
            echo "MEASUREMENTS_FILE and SENSOR_SUMMARY_FILE are required" >&2
            exit 2
        fi
        python3 "$ROOT_DIR/scripts/import_sensor_preflight_measurements.py" \
            --measurements "$MEASUREMENTS_FILE" \
            --sensor-summary "$SENSOR_SUMMARY_FILE" \
            --write
        ;;
    import-serial-latency)
        if [[ -z "${MEASUREMENTS_FILE:-}" || -z "${SERIAL_LATENCY_FILE:-}" ]]; then
            echo "MEASUREMENTS_FILE and SERIAL_LATENCY_FILE are required" >&2
            exit 2
        fi
        python3 "$ROOT_DIR/scripts/import_serial_latency_measurement.py" \
            --measurements "$MEASUREMENTS_FILE" \
            --serial-report "$SERIAL_LATENCY_FILE" \
            --write
        ;;
    import-measurement-session)
        if [[ -z "${MEASUREMENTS_FILE:-}" || -z "${MEASUREMENT_SESSION_FILE:-}" ]]; then
            echo "MEASUREMENTS_FILE and MEASUREMENT_SESSION_FILE are required" >&2
            exit 2
        fi
        python3 "$ROOT_DIR/scripts/import_measurement_session.py" \
            --measurements "$MEASUREMENTS_FILE" \
            --session "$MEASUREMENT_SESSION_FILE" \
            --write
        ;;
    sim2real-readiness)
        args=(--osracer-root "${OSRACER_ROOT:-$ROOT_DIR/../osracer}")
        if [[ -n "${MEASUREMENTS_FILE:-}" ]]; then
            args+=(--measurements "$MEASUREMENTS_FILE")
        fi
        python3 "$ROOT_DIR/scripts/sim2real_readiness.py" "${args[@]}"
        ;;
    sim2real-ready-strict)
        args=(--osracer-root "${OSRACER_ROOT:-$ROOT_DIR/../osracer}" --strict)
        if [[ -n "${MEASUREMENTS_FILE:-}" ]]; then
            args+=(--measurements "$MEASUREMENTS_FILE")
        fi
        python3 "$ROOT_DIR/scripts/sim2real_readiness.py" "${args[@]}"
        ;;
    calibration-plan)
        if [[ -z "${MEASUREMENTS_FILE:-}" ]]; then
            echo "MEASUREMENTS_FILE is required" >&2
            exit 2
        fi
        python3 "$ROOT_DIR/scripts/plan_calibration_updates.py" \
            --measurements "$MEASUREMENTS_FILE"
        ;;
    measured-overlay)
        if [[ -z "${MEASUREMENTS_FILE:-}" ]]; then
            echo "MEASUREMENTS_FILE is required" >&2
            exit 2
        fi
        python3 "$ROOT_DIR/scripts/export_measured_overlay.py" \
            --measurements "$MEASUREMENTS_FILE" \
            --output "${MEASURED_OVERLAY_OUTPUT:-/tmp/osracer_measured_overlay.json}"
        ;;
    sensor-extrinsics-check)
        if [[ -z "${MEASUREMENTS_FILE:-}" ]]; then
            echo "MEASUREMENTS_FILE is required" >&2
            exit 2
        fi
        python3 "$ROOT_DIR/scripts/apply_sensor_extrinsics.py" \
            --measurements "$MEASUREMENTS_FILE" \
            --osracer-root "${OSRACER_ROOT:-$ROOT_DIR/../osracer}"
        ;;
    sensor-extrinsics-write)
        if [[ -z "${MEASUREMENTS_FILE:-}" ]]; then
            echo "MEASUREMENTS_FILE is required" >&2
            exit 2
        fi
        python3 "$ROOT_DIR/scripts/apply_sensor_extrinsics.py" \
            --measurements "$MEASUREMENTS_FILE" \
            --osracer-root "${OSRACER_ROOT:-$ROOT_DIR/../osracer}" \
            --write
        ;;
    drift-baseline)
        run_train --headless \
            --num_envs "${DRIFT_BASELINE_ENVS:-2048}" \
            --max_iterations "${DRIFT_BASELINE_ITERS:-2000}"
        ;;
    all-smoke)
        "$0" static
        "$0" drift-smoke
        "$0" visual-smoke
        ;;
    *)
        usage >&2
        exit 2
        ;;
esac
