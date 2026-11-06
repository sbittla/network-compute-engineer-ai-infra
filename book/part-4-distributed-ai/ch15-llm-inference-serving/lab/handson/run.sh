#!/usr/bin/env bash
# Chapter 15 hands-on lab: serve an LLM with vLLM and measure it. Unattended.
#   bash run.sh [run-id]        -> results/<run-id>/ (default: <hostname>-<timestamp>)
# Holds the shared GPU lock for as long as any vLLM server runs; teardown runs on exit, even after a failure.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../../../.." && pwd)"
. "$ROOT/scripts/handson/common.sh"
. "$HERE/lab.env"

need_gpu
[ -x "$CH15_VENV/bin/vllm" ] || die "vLLM venv missing: run setup.sh first"
trap 'bash "$HERE/teardown.sh" >/dev/null 2>&1 || true' EXIT

RUN="$(run_dir "$HERE" "${1:-}")"
mkdir -p "$RUN/raw"; echo "results -> $RUN"
env_manifest "$RUN/environment.json" \
  "$CH15_VENV/bin/python -c 'import vllm; print(vllm.__version__)'" \
  "$CH15_VENV/bin/python -c 'import torch; print(torch.__version__, torch.version.cuda)'" \
  "nvidia-smi --query-gpu=name,driver_version,memory.total,clocks.max.sm,power.limit --format=csv,noheader" \
  "echo $CH15_MODEL@$CH15_MODEL_REVISION"

t0=$(date +%s)
with_gpu_lock bash "$HERE/experiments.sh" "$RUN" 2>&1 | tee "$RUN/raw/run.log"
echo "$(( $(date +%s) - t0 ))" > "$RUN/raw/elapsed_s"

python3 "$HERE/analyze.py" "$RUN"
python3 "$HERE/check.py" "$RUN"
