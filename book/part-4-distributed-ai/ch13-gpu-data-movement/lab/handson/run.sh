#!/usr/bin/env bash
# Chapter 13 hands-on lab: moving data to the GPU, unattended. Usage: bash run.sh [run-id]
# Writes results/<run-id>/ (environment.json, raw outputs per step, summary.json, report.md).
set -euo pipefail
LAB="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$LAB/../../../../.." && pwd)"
. "$ROOT/scripts/handson/common.sh"

need_gpu
need_cmd flock nvidia-smi
. "$ROOT/scripts/handson/venv.sh"

OUT="$(run_dir "$LAB" "${1:-}")"
bash "$LAB/teardown.sh" >/dev/null 2>&1 || true
trap 'bash "$LAB/teardown.sh" >/dev/null 2>&1 || true' EXIT
log() { echo "[ch13 $(date +%T)] $*"; }
log "results -> $OUT"
env_manifest "$OUT/environment.json" "nvidia-smi --version | head -1" "nproc" "df -h /dev/shm | tail -1" \
  "test -d /usr/lib/wsl && echo wsl2 || echo native"

gpu_steps() {
  set -euo pipefail
  log "Step 1: pinned vs pageable copies of batch-sized buffers; the cost of pinning"
  mkdir -p "$OUT/step1-copies"
  "$HANDSON_PY" "$LAB/copies.py" > "$OUT/step1-copies/copies.json"
  log "Step 2: copy/compute overlap on two CUDA streams, with GPU timestamps"
  mkdir -p "$OUT/step2-overlap"
  "$HANDSON_PY" "$LAB/overlap.py" > "$OUT/step2-overlap/overlap.json" 2> "$OUT/step2-overlap/overlap.stderr.txt"
  log "Step 3: DataLoader sweep: workers x pin_memory x prefetch_factor"
  mkdir -p "$OUT/step3-dataloader"
  nvidia-smi --query-gpu=name,clocks.sm,clocks.max.sm,power.draw,temperature.gpu --format=csv > "$OUT/step3-dataloader/gpu-before.csv"
  "$HANDSON_PY" "$LAB/loader.py" > "$OUT/step3-dataloader/loader.json" 2> "$OUT/step3-dataloader/loader.stderr.txt"
}
export -f gpu_steps log; export OUT LAB HANDSON_PY
log "waiting for the GPU lock"
with_gpu_lock bash -c gpu_steps

log "summarizing"
"$HANDSON_PY" "$LAB/summarize.py" "$OUT"
"$HANDSON_PY" "$LAB/check.py" "$OUT" || { log "check.py FAILED on this run"; exit 1; }
log "done: $OUT"
