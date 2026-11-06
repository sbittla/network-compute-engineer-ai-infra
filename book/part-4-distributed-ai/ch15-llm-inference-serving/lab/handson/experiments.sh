#!/usr/bin/env bash
# Chapter 15 hands-on lab: every GPU step. run.sh calls this under the GPU lock: experiments.sh <run-dir>
# Steps (each writes raw files under <run-dir>/raw/):
#   1 concurrency sweep   2 prefix caching off/on   3 KV pressure and preemption
#   4 capacity vs --gpu-memory-utilization          5 --max-num-seqs under the same load
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../../../.." && pwd)"
. "$ROOT/scripts/handson/common.sh"
. "$HERE/lab.env"

RUN="$1"; RAW="$RUN/raw"; mkdir -p "$RAW" "$CH15_STATE"
PY="$CH15_VENV/bin/python"
URL="http://127.0.0.1:$CH15_PORT"
STEPS="${CH15_STEPS:-1 2 3 4 5}"          # run a subset with CH15_STEPS="1 2"
REPS="${CH15_REPS:-3}"
CONCURRENCY="${CH15_CONCURRENCY:-1 2 4 8 16 32}"
BASE_UTIL=0.80
UTILS="${CH15_UTILS:-0.45 0.55 0.65 0.80 0.90}"   # fresh starts once the compile cache is warm
PRESSURE_UTIL="${CH15_PRESSURE_UTIL:-0.55}"
MAX_LEN=4096
SERVER_PID=""

export HF_HUB_OFFLINE=1 VLLM_NO_USAGE_STATS=1 DO_NOT_TRACK=1
# FlashInfer's top-k/top-p sampler JIT-compiles with nvcc, which the pip wheels do not ship; use the PyTorch sampler
export VLLM_USE_FLASHINFER_SAMPLER=0
export TORCHINDUCTOR_COMPILE_THREADS=4   # torch.compile workers default to one per CPU; 24 of them crowd 7 GB of RAM

log() { echo "[$(date +%H:%M:%S)] $*"; }

# Host memory and GPU memory, sampled for the whole run (model loads are where host RAM is tight in WSL).
monitor() {
  echo -e "t_s\tmem_available_mib\tserver_rss_mib" > "$RAW/hostmem.tsv"
  local t0; t0=$(date +%s.%N)
  while true; do
    local avail rss=0 pid
    avail=$(awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo)
    pid=$(cat "$CH15_STATE/server.pid" 2>/dev/null || true)
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
      rss=$(ps -o rss= -s "$pid" 2>/dev/null | awk '{s+=$1} END {print int(s/1024)}')
    fi
    awk -v a="$(date +%s.%N)" -v b="$t0" -v m="$avail" -v r="${rss:-0}" \
      'BEGIN {printf "%.1f\t%s\t%s\n", a - b, m, r}' >> "$RAW/hostmem.tsv"
    sleep 0.5
  done
}

stop_server() {
  local pid; pid=$(cat "$CH15_STATE/server.pid" 2>/dev/null || true)
  if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
    kill -TERM -- "-$pid" 2>/dev/null || true
    for _ in $(seq 60); do kill -0 "$pid" 2>/dev/null || break; sleep 0.5; done
    kill -KILL -- "-$pid" 2>/dev/null || true
    pkill -KILL -s "$pid" 2>/dev/null || true
  fi
  pkill -KILL -f -- "--served-model-name $CH15_SERVED_NAME" 2>/dev/null || true
  rm -f "$CH15_STATE/server.pid"
  # wait for the card to give the memory back before the next start
  for _ in $(seq 60); do
    [ "$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1)" -lt 600 ] && break; sleep 1
  done
}

cleanup() {
  stop_server
  [ -n "${MON_PID:-}" ] && kill "$MON_PID" 2>/dev/null || true
  [ -n "${GPU_MON_PID:-}" ] && kill "$GPU_MON_PID" 2>/dev/null || true
}
trap cleanup EXIT

# start_server <name> <gpu-mem-util> <max-num-seqs> <prefix:on|off>; returns 1 if the engine refuses to start
start_server() {
  local name="$1" util="$2" mns="$3" prefix="$4" pflag
  [ "$prefix" = on ] && pflag="--enable-prefix-caching" || pflag="--no-enable-prefix-caching"
  echo "{\"name\": \"$name\", \"gpu_memory_utilization\": $util, \"max_num_seqs\": $mns, \"prefix_caching\": \"$prefix\", \"max_model_len\": $MAX_LEN}" \
    > "$RAW/server-$name.json"
  log "start server $name: util=$util max-num-seqs=$mns prefix=$prefix"
  local t0; t0=$(date +%s)
  setsid "$CH15_VENV/bin/vllm" serve "$CH15_MODEL" --revision "$CH15_MODEL_REVISION" \
    --served-model-name "$CH15_SERVED_NAME" --host 127.0.0.1 --port "$CH15_PORT" \
    --dtype bfloat16 --max-model-len "$MAX_LEN" --gpu-memory-utilization "$util" --max-num-seqs "$mns" \
    $pflag --seed 0 > "$RAW/server-$name.log" 2>&1 < /dev/null &
  echo $! > "$CH15_STATE/server.pid"
  for _ in $(seq 900); do
    if curl -sf "$URL/health" >/dev/null 2>&1; then
      echo "$(( $(date +%s) - t0 ))" > "$RAW/server-$name.startup_s"
      "$PY" "$HERE/metrics_sampler.py" --url "$URL" --snapshot "$RAW/metrics-$name-start.prom"
      log "server $name ready after $(cat "$RAW/server-$name.startup_s") s"
      return 0
    fi
    if ! kill -0 "$(cat "$CH15_STATE/server.pid")" 2>/dev/null; then
      log "server $name exited during start-up (see server-$name.log)"; echo "refused" > "$RAW/server-$name.startup_s"
      stop_server; return 1
    fi
    sleep 1
  done
  log "server $name did not become healthy in 900 s"; echo "timeout" > "$RAW/server-$name.startup_s"; stop_server; return 1
}

# load <label> <loadgen args...>: runs the load generator with /metrics sampled alongside
load() {
  local label="$1"; shift
  "$PY" "$HERE/metrics_sampler.py" --url "$URL" --snapshot "$RAW/metrics-$label-start.prom"
  "$PY" "$HERE/metrics_sampler.py" --url "$URL" --out "$RAW/metrics-$label.jsonl" --interval 0.25 --duration 900 &
  local sp=$!
  timeout 900 "$PY" "$HERE/loadgen.py" --url "$URL" --model "$CH15_SERVED_NAME" --label "$label" \
    --out "$RAW/load-$label.jsonl" "$@" | tee -a "$RAW/loadgen.log"
  sleep 0.5; kill "$sp" 2>/dev/null || true; wait "$sp" 2>/dev/null || true
  "$PY" "$HERE/metrics_sampler.py" --url "$URL" --snapshot "$RAW/metrics-$label-end.prom"
}

need_gpu
monitor & MON_PID=$!
nvidia-smi --query-gpu=timestamp,memory.used,memory.total,utilization.gpu,power.draw,clocks.sm --format=csv \
  -lms 1000 > "$RAW/nvidia-smi.csv" 2>&1 & GPU_MON_PID=$!
nvidia-smi -q > "$RAW/nvidia-smi-q.txt" 2>&1 || true

has() { case " $STEPS " in *" $1 "*) return 0;; *) return 1;; esac; }

# ---- Base server: steps 1, 2 (off), 3 (high util), 5 (reference) ----
start_server base "$BASE_UTIL" 64 off
load warmup --concurrency 4 --num-requests 8 --prompt-min 256 --prompt-max 1024 --output-tokens 32 --seed 1
if has 1; then
  for c in $CONCURRENCY; do
    n=$(( 4 * c > 16 ? 4 * c : 16 ))
    for r in $(seq "$REPS"); do
      load "sweep-c$c-r$r" --concurrency "$c" --num-requests "$n" --prompt-min 256 --prompt-max 1024 \
        --output-tokens 128 --seed $(( 1000 * c + r ))
    done
  done
fi
if has 2; then
  for c in 1 8; do
    load "prefix-off-c$c" --concurrency "$c" --num-requests $(( c == 1 ? 24 : 48 )) --shared-prefix 1536 --suffix 64 \
      --output-tokens 16 --seed $(( 500 + c ))
  done
fi
if has 5; then
  load "mns64-c32" --concurrency 32 --num-requests 96 --prompt-min 256 --prompt-max 1024 --output-tokens 128 --seed 77
fi
if has 3; then
  load "pressure-u$BASE_UTIL" --concurrency 32 --num-requests 64 --prompt-min 1024 --prompt-max 1024 \
    --output-tokens 512 --seed 99
fi
stop_server

# ---- Step 2: the same shared-prefix workload with prefix caching on ----
if has 2 && start_server prefix-on "$BASE_UTIL" 64 on; then
  for c in 1 8; do
    load "prefix-on-c$c" --concurrency "$c" --num-requests $(( c == 1 ? 24 : 48 )) --shared-prefix 1536 --suffix 64 \
      --output-tokens 16 --seed $(( 500 + c ))
  done
  stop_server
fi

# ---- Step 5: --max-num-seqs caps the running batch under the same 32-way load ----
if has 5; then
  for m in 4 16; do
    if start_server "mns$m" "$BASE_UTIL" "$m" off; then
      load "mns$m-c32" --concurrency 32 --num-requests 96 --prompt-min 256 --prompt-max 1024 --output-tokens 128 --seed 77
      stop_server
    fi
  done
fi

# ---- Step 4 (and 3 at low util): KV capacity against --gpu-memory-utilization ----
if has 4 || has 3; then
  for u in $UTILS; do
    if ! has 4 && [ "$u" != "$PRESSURE_UTIL" ]; then continue; fi
    if start_server "util$u" "$u" 64 off; then
      if has 3 && [ "$u" = "$PRESSURE_UTIL" ]; then
        load "pressure-u$u" --concurrency 32 --num-requests 64 --prompt-min 1024 --prompt-max 1024 \
          --output-tokens 512 --seed 99
      fi
      stop_server
    fi
  done
fi
log "experiments done"
