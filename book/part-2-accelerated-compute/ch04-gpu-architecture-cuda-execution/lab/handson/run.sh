#!/usr/bin/env bash
# Ch 4 hands-on: profile a training step, find the hidden host sync, remove it, re-measure, try CUDA Graphs.
# Unattended; writes results/<run-id>/.   bash run.sh [run-id]
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../../../.." && pwd)"
. "$ROOT/scripts/handson/common.sh"
. "$ROOT/scripts/handson/venv.sh"
need_gpu
need_cmd flock timeout
OUT="$(run_dir "$HERE" "${1:-}")"
SCRATCH=/tmp/ch04-handson
mkdir -p "$SCRATCH"
trap 'bash "$HERE/teardown.sh" >/dev/null 2>&1 || true' EXIT
RUNS="${CH04_RUNS:-7}"          # runs per variant for the A/B (separate processes, interleaved)
PY="$HANDSON_PY"
STEP="$HERE/train_step.py"
HAVE_NSYS=0; command -v nsys >/dev/null && HAVE_NSYS=1
log() { echo "[$(date +%H:%M:%S)] $*"; }

log "results -> $OUT"
env_manifest "$OUT/environment.json" "nsys --version" \
  "nvidia-smi --query-gpu=name,driver_version,clocks.max.sm,pcie.link.gen.max,pcie.link.width.max --format=csv,noheader" \
  "$PY -c 'import torch; print(torch.__version__, torch.version.cuda)'"

# Step 1: the symptom. Time the baseline step, sampling nvidia-smi GPU-Util every 100 ms while it runs.
log "step 1: baseline step time and GPU-Util"
with_gpu_lock timeout 600 "$PY" "$HERE/with_util.py" "$OUT/step1_gpu_util.csv" -- \
  "$PY" "$STEP" --variant baseline --steps 150 > "$OUT/step1_baseline_time.json"

# Step 2: torch.profiler on each variant: runtime calls per step (and whether GPU activity is recorded at all).
log "step 2: torch.profiler"
for v in baseline fixed graphed; do
  with_gpu_lock timeout 600 "$PY" "$STEP" --variant "$v" --mode profile --trace "$SCRATCH/trace_$v.json" \
    > "$OUT/step2_profile_$v.json" 2> "$OUT/step2_profile_$v.txt"
  gzip -c "$SCRATCH/trace_$v.json" > "$OUT/step2_trace_$v.json.gz"
done

# Step 3 (and 5, 6): Nsight Systems timeline of two steps per variant, then the gap analysis.
nsys_capture() {
  local v="$1" rep="$SCRATCH/step_$1"
  with_gpu_lock timeout 900 nsys profile -t cuda,nvtx,osrt -s none --cuda-graph-trace=node --capture-range=cudaProfilerApi \
    --capture-range-end=stop -f true -o "$rep" "$PY" "$STEP" --variant "$v" --mode nsys --capture-steps 6 > "$OUT/nsys_${v}_profile.log" 2>&1
  cp "$rep.nsys-rep" "$OUT/nsys_${v}.nsys-rep"
  timeout 600 nsys export --type sqlite --force-overwrite true --output "$rep.sqlite" "$rep.nsys-rep" > "$SCRATCH/export_$v.log" 2>&1 || { cat "$SCRATCH/export_$v.log" >&2; return 1; }
  timeout 600 nsys stats --report cuda_api_sum,cuda_gpu_kern_sum,cuda_gpu_mem_time_sum,nvtx_sum "$rep.sqlite" \
    > "$OUT/nsys_${v}_stats.txt" 2>&1 || true
  python3 "$HERE/gaps.py" "$rep.sqlite" --json "$OUT/nsys_${v}_gaps.json" > "$OUT/nsys_${v}_gaps.txt"
}
if [ "$HAVE_NSYS" = 1 ]; then
  log "step 3: nsys timeline of the baseline"
  nsys_capture baseline
else
  log "step 3: nsys not installed (CH04_NSYS=0 or setup skipped): skipping the timeline steps"
  echo '{"nsys": "not installed"}' > "$OUT/nsys_skipped.json"
fi

# Step 4: which line synchronizes? torch.cuda.set_sync_debug_mode("warn") on one baseline step.
log "step 4: sync debug mode"
with_gpu_lock timeout 600 "$PY" "$STEP" --variant baseline --mode syncdebug > "$OUT/step4_syncdebug.txt" 2>&1

# Step 5: the fix, re-measured. Interleaved runs, a fresh process each (Chapter 6 protocol, light).
log "step 5: A/B/C timing, $RUNS interleaved runs per variant"
: > "$OUT/step5_runs.jsonl"
variants=(baseline fixed graphed)
for r in $(seq 1 "$RUNS"); do
  for k in 0 1 2; do
    v="${variants[$(( (k + r) % 3 ))]}"          # rotate the start so no variant always runs first
    with_gpu_lock timeout 600 "$PY" "$STEP" --variant "$v" | \
      python3 -c "import json,sys; d=json.load(sys.stdin); d['run']=$r; print(json.dumps(d))" >> "$OUT/step5_runs.jsonl"
  done
done
if [ "$HAVE_NSYS" = 1 ]; then
  log "step 5: nsys timeline of the fixed step"
  nsys_capture fixed
fi

# Step 6: CUDA Graphs. The baseline cannot be captured (its host syncs break capture); the fixed step can.
log "step 6: CUDA Graphs"
with_gpu_lock timeout 600 "$PY" "$STEP" --mode capture > "$OUT/step6_capture_baseline.json" 2> "$OUT/step6_capture_baseline.err" || true
if [ "$HAVE_NSYS" = 1 ]; then
  nsys_capture graphed
fi

# Step 6b: the same graph where the step is launch-bound. With micro-batches of 4 sequences instead of 8, the GPU
# work per launch halves and the CPU's ~950 launches per step become the bottleneck: the regime graphs are for.
LB_BATCH="${CH04_LB_BATCH:-4}"
log "step 6b: fixed vs graphed at --batch $LB_BATCH (launch-bound), 4 interleaved runs each"
: > "$OUT/step6b_launchbound_runs.jsonl"
for r in 1 2 3 4; do
  for v in $([ $((r % 2)) = 1 ] && echo "fixed graphed" || echo "graphed fixed"); do
    with_gpu_lock timeout 600 "$PY" "$STEP" --variant "$v" --batch "$LB_BATCH" |       python3 -c "import json,sys; d=json.load(sys.stdin); d['run']=$r; d['batch']=$LB_BATCH; print(json.dumps(d))" >> "$OUT/step6b_launchbound_runs.jsonl"
  done
done

log "summarize"
python3 "$HERE/summarize.py" "$OUT"
python3 "$HERE/check.py" "$OUT" || true
log "done: $OUT"
