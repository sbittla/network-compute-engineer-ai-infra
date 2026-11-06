#!/usr/bin/env bash
# Chapter 12 hands-on lab: run every measurement unattended and write results/<run-id>/.
#   bash run.sh [run-id]          (reference run: bash run.sh wsl2-rtx4060-laptop)
# CPU (gloo) sweeps need no lock; the NCCL steps take the shared GPU lock.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../../../.." && pwd)"
. "$ROOT/scripts/handson/common.sh"
. "$ROOT/scripts/handson/venv.sh"

RUN_ID="${1:-$(hostname)-$(date +%Y%m%d-%H%M%S)}"
[ -n "$RUN_ID" ] || die "empty run id"
rm -rf "${HERE:?}/results/$RUN_ID"
OUT="$(run_dir "$HERE" "$RUN_ID")"
RAW="$OUT/raw"
mkdir -p "$RAW"
trap 'bash "$HERE/teardown.sh" >/dev/null 2>&1 || true' EXIT

TR="$HANDSON_VENV/bin/torchrun"
[ -x "$TR" ] || die "torchrun missing: run setup.sh"
T0=$(date +%s)
cat /proc/loadavg > "$RAW/loadavg_before.txt"
: > "$RAW/exit_codes.tsv"

# sweep <name> <nproc> [worker options...]   (CPU, gloo)
sweep() {
  local name="$1" n="$2"; shift 2
  echo "[ch12] $(date +%T) $name: torchrun --nproc-per-node=$n ch12_collectives.py $*"
  local rc=0
  timeout 900 "$TR" --standalone --nproc-per-node="$n" "$HERE/ch12_collectives.py" \
    --out "$RAW/$name.jsonl" --tag "$name" "$@" > "$RAW/$name.log" 2>&1 || rc=$?
  printf '%s\t%s\n' "$name" "$rc" >> "$RAW/exit_codes.tsv"
}

echo "== Step 1: all_reduce, all_gather, reduce_scatter, broadcast; 4 B to 64 MiB; 2, 4, 8 ranks (gloo)"
sweep coll_n2 2 --ops all_reduce,all_gather,reduce_scatter,broadcast,pingpong
sweep coll_n4 4
sweep coll_n8 8
echo "== Step 2: repeat the 4-rank sweep as separate launches (run-to-run spread)"
sweep coll_n4_rep2 4 --ops all_reduce
sweep coll_n4_rep3 4 --ops all_reduce
echo "== Step 3: ring versus tree, hand-written from send/recv, against gloo's own all_reduce"
sweep algo_n4 4 --ops all_reduce,ring_allreduce,tree_allreduce --step-factor 4
sweep algo_n8 8 --ops all_reduce,ring_allreduce,tree_allreduce --step-factor 4

echo "== Step 4: NCCL on the one GPU"
if nvidia-smi -L >/dev/null 2>&1; then
  rc=0
  NCCL_DEBUG=WARN with_gpu_lock timeout 180 "$TR" --standalone --nproc-per-node=2 "$HERE/ch12_collectives.py" \
    --device cuda --same-gpu --ops all_reduce --max-bytes 1024 > "$RAW/nccl_2ranks_1gpu.log" 2>&1 || rc=$?
  printf 'nccl_2ranks_1gpu\t%s\n' "$rc" >> "$RAW/exit_codes.tsv"
  rc=0
  NCCL_DEBUG=INFO with_gpu_lock timeout 600 "$TR" --standalone --nproc-per-node=1 "$HERE/ch12_collectives.py" \
    --device cuda --out "$RAW/nccl_n1.jsonl" --tag nccl_n1 > "$RAW/nccl_n1.log" 2>&1 || rc=$?
  printf 'nccl_n1\t%s\n' "$rc" >> "$RAW/exit_codes.tsv"
  nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv > "$RAW/gpu_nvidia_smi.csv" 2>&1 || true
else
  echo "no GPU visible: step 4 skipped" | tee "$RAW/nccl.skipped"
fi
if command -v nvcc >/dev/null 2>&1; then
  echo "nvcc found: build nccl-tests by hand (README, optional step) to compare with the -g 1 floor" > "$RAW/nccl_tests.txt"
else
  echo "nccl-tests not built: no CUDA toolkit (nvcc) on this host; see README optional step" > "$RAW/nccl_tests.txt"
fi

cat /proc/loadavg > "$RAW/loadavg_after.txt"
echo "$(( $(date +%s) - T0 ))" > "$RAW/run_seconds.txt"
env_manifest "$OUT/environment.json" \
  "$HANDSON_PY -c 'import torch; print(torch.__version__, torch.version.cuda, torch.cuda.nccl.version())'" \
  "cat /proc/loadavg" "free -m | sed -n 2p"
"$HANDSON_PY" "$HERE/analyze.py" "$OUT"
echo "== Done in $(cat "$RAW/run_seconds.txt") s: $OUT"
"$HANDSON_PY" "$HERE/check.py" "$OUT"
