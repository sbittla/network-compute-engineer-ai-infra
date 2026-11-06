#!/usr/bin/env bash
# Chapter 11 hands-on lab: run every experiment unattended and write results/<run-id>/.
#   bash run.sh [run-id]          (reference run: bash run.sh wsl2-rtx4060-laptop)
# CPU experiments use gloo and need no lock; the one GPU step takes the shared GPU lock.
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
WORK="/tmp/ch11-handson-$$"
mkdir -p "$WORK"
trap 'bash "$HERE/teardown.sh" >/dev/null 2>&1 || true' EXIT

TR="$HANDSON_VENV/bin/torchrun"
[ -x "$TR" ] || die "torchrun missing: run setup.sh"
STEPS=25          # timed experiments: 25 steps, the first 5 are warm-up
T0=$(date +%s)
cat /proc/loadavg > "$RAW/loadavg_before.txt"
: > "$RAW/exit_codes.tsv"

# launch <name> <nproc> [torchrun options...] -- [worker options...]
launch() {
  local name="$1" n="$2"; shift 2
  local topts=()
  while [ "$1" != "--" ]; do topts+=("$1"); shift; done
  shift
  echo "[ch11] $(date +%T) $name: torchrun --nproc-per-node=$n ${topts[*]} ch11_ddp.py $*"
  local rc=0
  timeout 900 "$TR" --standalone --nproc-per-node="$n" "${topts[@]}" "$HERE/ch11_ddp.py" \
    --event-log "$RAW/$name.jsonl" --fault-log "$RAW/$name.faults.jsonl" "$@" > "$RAW/$name.log" 2>&1 || rc=$?
  printf '%s\t%s\n' "$name" "$rc" >> "$RAW/exit_codes.tsv"
  return 0
}

echo "== Step 1: data-parallel scaling on CPU (gloo), 1/2/4/8 ranks, 1 thread per rank"
for n in 1 2 4 8; do
  launch "weak_n$n" "$n" -- --steps $STEPS --micro-batch 32
  launch "weak_nocomm_n$n" "$n" -- --steps $STEPS --micro-batch 32 --no-comm
  launch "strong_n$n" "$n" -- --steps $STEPS --micro-batch $((64 / n))
done

echo "== Step 2: gradient bucket size (bucket_cap_mb), 4 ranks"
for b in 1 5 25 100; do
  launch "bucket_$b" 4 -- --steps $STEPS --micro-batch 32 --bucket-cap-mb "$b"
done

echo "== Step 3: gradient accumulation with no_sync, 4 ranks"
for k in 1 2 4 8; do
  launch "accum_$k" 4 -- --steps 15 --warmup 3 --micro-batch 32 --accum "$k"
done

echo "== Step 4: the same job on the GPU (1 rank, NCCL), reference only"
if nvidia-smi -L >/dev/null 2>&1; then
  rc=0
  with_gpu_lock timeout 600 "$TR" --standalone --nproc-per-node=1 "$HERE/ch11_ddp.py" --device cuda \
    --steps 40 --warmup 10 --micro-batch 32 --event-log "$RAW/gpu_n1.jsonl" --fault-log "$RAW/gpu_n1.faults.jsonl" \
    > "$RAW/gpu_n1.log" 2>&1 || rc=$?
  printf 'gpu_n1\t%s\n' "$rc" >> "$RAW/exit_codes.tsv"
  nvidia-smi --query-gpu=name,driver_version,memory.total,clocks.max.sm --format=csv > "$RAW/gpu_nvidia_smi.csv" 2>&1 || true
else
  echo "no GPU visible: step 4 skipped" | tee "$RAW/gpu_n1.skipped"
fi

echo "== Step 5: kill a rank, hang a rank (process-group timeout), elastic restart from checkpoint"
launch fault_kill_norestart 4 --max-restarts=0 -- --steps 40 --micro-batch 32 --ckpt-dir "$WORK/kill0" \
  --ckpt-every 10 --fault kill --fault-rank 2 --fault-steps 23 --pg-timeout 30
launch fault_kill 4 --max-restarts=1 -- --steps 40 --micro-batch 32 --ckpt-dir "$WORK/kill" \
  --ckpt-every 10 --fault kill --fault-rank 2 --fault-steps 23 --pg-timeout 30
for to in 10 20; do
  launch "fault_hang_t$to" 4 --max-restarts=1 -- --steps 40 --micro-batch 32 --ckpt-dir "$WORK/hang$to" \
    --ckpt-every 10 --fault hang --fault-rank 2 --fault-steps 23 --pg-timeout "$to"
done

echo "== Step 6: lost work against checkpoint interval (6 kills at the same steps, K = 2..32)"
FSTEPS=$("$HANDSON_PY" -c "import random; print(','.join(map(str, sorted(random.Random(11).sample(range(2, 193), 6)))))")
echo "$FSTEPS" > "$RAW/ckpt_fault_steps.txt"
launch ckpt_base 4 -- --steps 192 --micro-batch 32
for K in 2 4 8 16 32; do
  launch "ckpt_K$K" 4 --max-restarts=6 -- --steps 192 --micro-batch 32 --ckpt-dir "$WORK/K$K" \
    --ckpt-every "$K" --fault kill --fault-rank 2 --fault-steps "$FSTEPS" --pg-timeout 30
done

cat /proc/loadavg > "$RAW/loadavg_after.txt"
echo "$(( $(date +%s) - T0 ))" > "$RAW/run_seconds.txt"
env_manifest "$OUT/environment.json" \
  "$HANDSON_PY -c 'import torch; print(torch.__version__, torch.version.cuda, torch.cuda.nccl.version())'" \
  "$TR --help | head -1" "cat /proc/loadavg" "free -m | sed -n 2p"
"$HANDSON_PY" "$HERE/analyze.py" "$OUT"
echo "== Done in $(cat "$RAW/run_seconds.txt") s: $OUT"
"$HANDSON_PY" "$HERE/check.py" "$OUT"
