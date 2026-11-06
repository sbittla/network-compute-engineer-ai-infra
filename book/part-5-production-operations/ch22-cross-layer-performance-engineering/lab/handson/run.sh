#!/usr/bin/env bash
# Ch 22 hands-on: inject four bottlenecks one at a time into a training loop; for each, collect evidence,
# diagnose it with pre-written rules, apply the fix and validate it with an interleaved A/B test.
# Unattended; writes results/<run-id>/.   bash run.sh [run-id]     (CH22_RUNS=5 runs per arm)
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../../../.." && pwd)"
. "$ROOT/scripts/handson/common.sh"
# sudo resets PATH (secure_path); WSL2 keeps nvidia-smi in /usr/lib/wsl/lib.
[ -d /usr/lib/wsl/lib ] && export PATH="$PATH:/usr/lib/wsl/lib"
. "$ROOT/scripts/handson/venv.sh"
need_root
need_gpu
need_cmd ip tc taskset flock timeout ping
# The whole measured part runs under one GPU lock: one GPU job at a time on the shared card, no other GPU
# job between the A/B arms, and the CPU hog of scenario 2 runs only while this lab holds the card.
if [ -z "${CH22_GPU_LOCK_HELD:-}" ]; then
  echo "[$(date +%H:%M:%S)] waiting for the GPU lock ($HANDSON_GPU_LOCK)"
  export CH22_GPU_LOCK_HELD=1
  with_gpu_lock bash "$HERE/run.sh" "$@"
  exit $?
fi
RUNS="${CH22_RUNS:-5}"
export CH22_CPUS_A="${CH22_CPUS_A:-8-11}" CH22_CPUS_B="${CH22_CPUS_B:-12-15}"
SCR=/tmp/ch22-handson
trap 'bash "$HERE/teardown.sh" >/dev/null 2>&1 || true' EXIT
bash "$HERE/teardown.sh" >/dev/null 2>&1 || true      # start clean
mkdir -p "$SCR"
log() { echo "[$(date +%H:%M:%S)] $*"; }
PY="$HANDSON_PY"

# Fail before measuring anything if this kernel has no netem (scenario 4 needs it).
bash "$HERE/netlab.sh" up >/dev/null
bash "$HERE/netlab.sh" delay 1 >/dev/null 2>&1 || die "tc netem is unavailable (CONFIG_NET_SCH_NETEM, module sch_netem): run setup.sh"
bash "$HERE/netlab.sh" nodelay
OUT="$(run_dir "$HERE" "${1:-}")"
log "results -> $OUT"
env_manifest "$OUT/environment.json" "ip -V" "tc -V" "taskset --version" "uname -r" \
  "$PY -c 'import torch, numpy; print(torch.__version__, torch.version.cuda, numpy.__version__)'" \
  "lscpu | grep -E '^(Thread|Core|Socket|NUMA node\\(s\\))'"

log "network: namespaces ch22-train / ch22-data, veth ch22-t0 <-> ch22-d0, data server"
bash "$HERE/netlab.sh" up
bash "$HERE/netlab.sh" status > "$OUT/net_healthy_status.txt" 2>&1

# ---- calibration: size the CPU work and the delay from this machine's GPU step time
log "calibrate: GPU-only step time and decode cost per round"
timeout 600 taskset -c "$CH22_CPUS_A" ip netns exec ch22-train "$PY" "$HERE/trainer.py" --no-data \
  --label calibrate > "$OUT/calibration_gpu_only.json"
taskset -c "$CH22_CPUS_A" "$PY" - "$HERE" "$OUT/calibration_gpu_only.json" "$OUT/calibration.json" "$SCR/calibration.env" <<'PY'
import json, os, random, statistics, sys, time
here, gpu_json, out_json, env_file = sys.argv[1:5]
sys.path.insert(0, here)
os.sched_setaffinity(0, {sorted(os.sched_getaffinity(0))[0]})
import numpy as np
from trainer import decode
raw = random.Random(1).randbytes(65536)   # the data server's reply size
def t(rounds):
    xs = []
    for _ in range(7):
        t0 = time.perf_counter(); decode(raw, 4096, 1024, rounds); xs.append((time.perf_counter() - t0) * 1e3)
    return statistics.median(xs)
base, eight = t(0), t(8)
per_round = (eight - base) / 8
g = json.load(open(gpu_json))["step_ms"]
rounds = max(1, round((2.0 * g - base) / per_round))
delay = max(20, round(6.0 * g))
cal = {"gpu_only_step_ms": g, "decode_base_ms": base, "decode_ms_per_round": per_round, "decode_rounds": rounds,
       "decode_ms_expected": base + rounds * per_round, "netem_delay_ms": delay, "workers": 4,
       "rule": "decode ~ 2 x GPU step on one CPU (4 workers keep up with 2x headroom); netem delay ~ 6 x GPU step"}
json.dump(cal, open(out_json, "w"), indent=2)
open(env_file, "w").write(f"CH22_ROUNDS={rounds}\nCH22_DELAY_MS={delay}\n")
print(json.dumps(cal))
PY
. "$SCR/calibration.env"
export CH22_ROUNDS CH22_DELAY_MS

sc() { bash "$HERE/scenario.sh" "$@"; }
ab() {   # ab <scenario>: RUNS interleaved bad/fixed runs, the order alternating each round
  local s="$1" f="$OUT/ab_$1.jsonl"; : > "$f"
  for r in $(seq 1 "$RUNS"); do
    if [ $((r % 2)) -eq 1 ]; then order="bad fixed"; else order="fixed bad"; fi
    for arm in $order; do
      sc "$s" "$arm" "$SCR/ab.json"
      python3 -c "import json,sys; d=json.load(open('$SCR/ab.json')); d['run']=$r; d['arm']='$arm'; print(json.dumps(d))" >> "$f"
    done
  done
  log "  A/B $s: $(python3 -c "
import json,statistics as st
rows=[json.loads(l) for l in open('$f')]
for a in ('bad','fixed'): print(a, round(st.mean(r['step_ms'] for r in rows if r['arm']==a),2), end='  ')
")"
}
evidence() {   # evidence <scenario>: one profiled run of the bad arm, then the rule-based diagnosis
  sc "$1" bad "$OUT/evidence_$1.json" --profile ${2:-}
  python3 "$HERE/diagnose.py" "$OUT/evidence_$1.json" "$OUT/evidence_healthy.json" > "$OUT/diagnosis_$1.json"
  log "  evidence $1 -> $(python3 -c "import json; print(json.load(open('$OUT/diagnosis_$1.json'))['verdict'])")"
}

# ---- healthy reference
log "healthy: one profiled evidence run + $RUNS runs"
sc healthy fixed "$OUT/evidence_healthy.json" --profile
: > "$OUT/healthy_runs.jsonl"
for r in $(seq 1 "$RUNS"); do sc healthy fixed "$SCR/h.json"; cat "$SCR/h.json" >> "$OUT/healthy_runs.jsonl"; done

# ---- 1. dataloader stall: decode moved into the training process (num_workers=0)
log "scenario 1: dataloader stall"
evidence loader
ab loader

# ---- 2. CPU contention: a competing job pinned to the same CPUs with taskset
log "scenario 2: CPU contention (ch22-hog x 8 on CPUs $CH22_CPUS_A)"
bash "$HERE/hog.sh" start "$CH22_CPUS_A" 8 > "$OUT/cpu_hog_start.txt"
( sleep 12; { echo "# ps while the evidence run is going: PSR = the CPU each process last ran on";
  ps -eo pid,psr,pcpu,stat,comm,args --sort=-pcpu | grep -E 'ch22-hog|trainer.py|PID' | grep -v grep | cut -c1-160 | head -20
  for p in $(cat /tmp/ch22-hog.pids); do echo "hog $p affinity: $(taskset -cp "$p" 2>/dev/null | sed 's/.*: //')"; done
  } > "$OUT/cpu_ps_snapshot.txt" 2>&1 ) &
snap=$!
evidence cpu
wait "$snap" || true
ab cpu
bash "$HERE/hog.sh" stop

# ---- 3. hidden host sync: a per-layer .item() debug statistic
log "scenario 3: hidden host sync"
evidence sync --sync-debug
ab sync

# ---- 4. network delay on the data fetch: netem on the data server's veth
log "scenario 4: network delay (netem ${CH22_DELAY_MS} ms on ch22-d0)"
bash "$HERE/netlab.sh" delay "$CH22_DELAY_MS" > "$OUT/net_delay_qdisc.txt"
bash "$HERE/netlab.sh" status > "$OUT/net_delay_status_before.txt" 2>&1
evidence network
ab network
bash "$HERE/netlab.sh" status > "$OUT/net_delay_status_after.txt" 2>&1
bash "$HERE/netlab.sh" nodelay

log "summarize"
python3 "$HERE/summarize.py" "$OUT"
python3 "$HERE/check.py" "$OUT" || true
log "done: $OUT"
