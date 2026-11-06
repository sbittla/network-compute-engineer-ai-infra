#!/usr/bin/env bash
# Chapter 1 hands-on lab, unattended: bash run.sh [run-id]  ->  results/<run-id>/
set -euo pipefail
LAB="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$LAB/../../../../.." && pwd)"
. "$ROOT/scripts/handson/common.sh"
trap 'bash "$LAB/teardown.sh"' EXIT
export PYTHONDONTWRITEBYTECODE=1

need_gpu
. "$ROOT/scripts/handson/venv.sh"
RUN="$(run_dir "$LAB" "${1:-}")"
echo "results: $RUN"
env_manifest "$RUN/environment.json" "nvidia-smi --version | head -3" \
  "$HANDSON_PY -c 'import torch; print(torch.__version__, torch.version.cuda)'"
# The whole measurement holds the shared GPU lock: telemetry would be meaningless with another job on the card.
cd "$LAB"
with_gpu_lock "$HANDSON_PY" "$LAB/ch01_ceilings.py" --out "$RUN" ${CH01_QUICK:+--quick} 2>&1 | tee "$RUN/run.log"
"$HANDSON_PY" "$LAB/ch01_analyze.py" "$RUN" > /dev/null
cat "$RUN/report.md"
python3 "$LAB/check.py" "$RUN"
