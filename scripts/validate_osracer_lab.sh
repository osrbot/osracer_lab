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
  runtime-contract
                  Check shared hardware/runtime parameters against osracer.
  sim2real-readiness
                  Summarize sim2real gates without failing on incomplete gates.
  sim2real-ready-strict
                  Fail unless all sim2real readiness gates pass.
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
    runtime-contract)
        python3 "$ROOT_DIR/scripts/check_runtime_contract.py" \
            --osracer-root "${OSRACER_ROOT:-$ROOT_DIR/../osracer}"
        ;;
    sim2real-readiness)
        python3 "$ROOT_DIR/scripts/sim2real_readiness.py" \
            --osracer-root "${OSRACER_ROOT:-$ROOT_DIR/../osracer}"
        ;;
    sim2real-ready-strict)
        python3 "$ROOT_DIR/scripts/sim2real_readiness.py" \
            --osracer-root "${OSRACER_ROOT:-$ROOT_DIR/../osracer}" \
            --strict
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
