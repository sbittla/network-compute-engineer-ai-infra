#!/usr/bin/env bash
# Ch 6 hands-on: the benchmark protocol on a real GPU. Unattended; writes results/<run-id>/.
#   bash run.sh [run-id]          CH06_RUNS=8 (runs per arm), CH06_ITERS=50 (timed iterations per run)
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../../../.." && pwd)"
. "$ROOT/scripts/handson/common.sh"
. "$ROOT/scripts/handson/venv.sh"
need_gpu
need_cmd flock timeout nvidia-smi
OUT="$(run_dir "$HERE" "${1:-}")"
trap 'bash "$HERE/teardown.sh" >/dev/null 2>&1 || true' EXIT
PY="$HANDSON_PY"
log() { echo "[$(date +%H:%M:%S)] $*"; }

log "results -> $OUT"
env_manifest "$OUT/environment.json" \
  "nvidia-smi --query-gpu=name,uuid,driver_version,vbios_version,clocks.max.sm,clocks.max.memory,power.limit,pcie.link.gen.current,pcie.link.width.current,persistence_mode --format=csv,noheader" \
  "nvidia-smi --query-gpu=clocks.applications.graphics,clocks.sm,temperature.gpu,clocks_event_reasons.active --format=csv,noheader" \
  "$PY -c 'import torch; print(torch.__version__, torch.version.cuda, torch.backends.cudnn.version())'"
nvidia-smi -q -d PERFORMANCE,CLOCK,POWER -i 0 > "$OUT/gpu_state_before.txt" 2>&1 || true

log "step 1: naive timing vs the protocol's timer"
with_gpu_lock timeout 600 "$PY" "$HERE/naive.py" > "$OUT/step1_naive.json"

# Steps 2-5: one session holding the GPU lock (the protocol assumes a dedicated GPU).
log "steps 2-5: protocol session: ${CH06_RUNS:-8} interleaved runs per arm, fresh process each"
with_gpu_lock timeout 3600 "$PY" "$HERE/protocol.py" "$OUT" --runs "${CH06_RUNS:-8}" --iters "${CH06_ITERS:-50}" \
  --python "$PY" | tee "$OUT/protocol.log"

log "step 6: empirical roofline"
with_gpu_lock timeout 900 "$PY" "$HERE/roofline.py" > "$OUT/step6_roofline.json"
nvidia-smi -q -d PERFORMANCE,CLOCK,POWER -i 0 > "$OUT/gpu_state_after.txt" 2>&1 || true

log "analyze"
python3 "$HERE/analyze.py" "$OUT"
python3 "$HERE/check.py" "$OUT" || true
log "done: $OUT"
