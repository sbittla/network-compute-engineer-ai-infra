#!/usr/bin/env bash
# Chapter 3 hands-on lab: host diagnostics on this machine, unattended. Usage: bash run.sh [run-id]
# Writes results/<run-id>/ (environment.json, raw outputs per step, summary.json, report.md).
set -euo pipefail
LAB="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$LAB/../../../../.." && pwd)"
CH="$(cd "$LAB/../.." && pwd)"
. "$ROOT/scripts/handson/common.sh"

need_root
need_cmd vmstat mpstat iostat taskset setpriv prlimit flock lspci numactl dmesg python3
. "$ROOT/scripts/handson/venv.sh"

OUT="$(run_dir "$LAB" "${1:-}")"
bash "$LAB/teardown.sh" >/dev/null 2>&1 || true
trap 'bash "$LAB/teardown.sh" >/dev/null 2>&1 || true' EXIT
log() { echo "[ch03 $(date +%T)] $*"; }
log "results -> $OUT"

env_manifest "$OUT/environment.json" "vmstat -V | head -1" "mpstat -V 2>&1 | head -1" "lspci --version" \
  "numactl --show | head -1" "uname -r" "ulimit -l" "cat /proc/sys/kernel/dmesg_restrict" "nproc"   "test -d /usr/lib/wsl && echo wsl2 || echo native"

NCPU="$(nproc)"
HOT=$(( NCPU / 2 + 2 ))            # the CPU we load in Steps 2 and 3 (not CPU 0, which takes most interrupts)
[ "$HOT" -lt "$NCPU" ] || HOT=$(( NCPU - 1 ))

# ---------------------------------------------------------------- Step 1: the chapter's collector, root and non-root
log "Step 1: read-only collector (Section 3.10), as root and as nobody"
S="$OUT/step1-collector"; mkdir -p "$S"
COL="$CH/solutions/lab/host_collector.py"; ANA="$CH/solutions/lab/host_analyzer.py"
[ -f "$COL" ] || { COL="$CH/lab/starter/host_collector.py"; ANA="$CH/lab/starter/host_analyzer.py"; }
echo "$COL" > "$S/collector_path.txt"
"$HANDSON_PY" "$COL" --out-dir "$S/root" --note "ch03 hands-on: idle host, root" > "$S/collector-root.log" 2>&1
NR="$(mktemp -d /tmp/ch03-nonroot.XXXXXX)"
cp "$COL" "$NR/"; chown -R 65534:65534 "$NR"; chmod 755 "$NR"
setpriv --reuid=65534 --regid=65534 --clear-groups /usr/bin/python3 "$NR/host_collector.py" \
  --out-dir "$NR/out" --note "ch03 hands-on: idle host, non-root (nobody)" > "$S/collector-nonroot.log" 2>&1
mkdir -p "$S/nonroot"; cp "$NR"/out/* "$S/nonroot/"; rm -rf "$NR"
"$HANDSON_PY" "$ANA" "$S"/root/*.json --baseline "$CH/lab/data/orion_hx8_baseline.yaml" \
  --out "$S/triage-vs-orion-hx8.md" > "$S/analyzer.log" 2>&1

# ---------------------------------------------------------------- Step 2: averages hide the saturated core
log "Step 2: one busy thread pinned to CPU $HOT; vmstat and mpstat"
S="$OUT/step2-percpu"; mkdir -p "$S"
taskset -c "$HOT" timeout 20 python3 "$LAB/spin.py" ch03-spin 15 &
sleep 1
SPIN="$(pgrep -n -f 'spin.py ch03-spin')"
{ echo "\$ taskset -cp $SPIN"; taskset -cp "$SPIN"; echo "\$ ps -L -o pid,tid,psr,pcpu,comm -p $SPIN"; ps -L -o pid,tid,psr,pcpu,comm -p "$SPIN"; } > "$S/affinity.txt"
echo "$HOT" > "$S/hot_cpu.txt"
LC_ALL=C vmstat 1 6 > "$S/vmstat.txt"
LC_ALL=C mpstat -P ALL 1 5 > "$S/mpstat.txt"
kill "$SPIN" 2>/dev/null || true; wait 2>/dev/null || true

# ---------------------------------------------------------------- Step 3: CPU placement and throughput
log "Step 3: pinned workers (taskset semantics): alone, same CPU, SMT siblings, separate cores, unpinned"
S="$OUT/step3-pinning"; mkdir -p "$S"
lscpu -e=CPU,CORE,SOCKET,NODE,ONLINE > "$S/lscpu-e.txt"
with_gpu_lock python3 "$LAB/cpu_bench.py" --cpu "$HOT" --seconds 3 --reps 3 > "$S/bench.json"

# ---------------------------------------------------------------- Step 4: page cache
log "Step 4: page cache: cold, warm and O_DIRECT reads of a 1 GiB file"
S="$OUT/step4-pagecache"; mkdir -p "$S"
LC_ALL=C free -m > "$S/free-before.txt"
python3 "$LAB/pagecache.py" /var/tmp/ch03-pagecache.bin 1024 > "$S/pagecache.json"
LC_ALL=C free -m > "$S/free-after.txt"
rm -f /var/tmp/ch03-pagecache.bin

# ---------------------------------------------------------------- Step 5: locked memory and pinned copies
log "Step 5a: ulimit -l and mlock as root and as nobody"
S="$OUT/step5-pinned"; mkdir -p "$S"
# The limit root inherits differs between WSL boots and distributions (64 MiB from a login shell, ~1 GB
# from WSL's init). Give the unprivileged probes the common distribution default so the result is reproducible.
NOBODY_MEMLOCK=$((64 * 1024 * 1024))
{ echo "root:   ulimit -l = $(ulimit -l)"; echo "nobody: ulimit -l = $(prlimit --memlock=$NOBODY_MEMLOCK setpriv --reuid=65534 --regid=65534 --clear-groups bash -c 'ulimit -l')"; } > "$S/ulimit.txt"
NR="$(mktemp -d /tmp/ch03-nonroot.XXXXXX)"; cp "$LAB/mlock_probe.py" "$NR/"; chmod 755 "$NR"; chmod 644 "$NR/mlock_probe.py"
{
  python3 "$LAB/mlock_probe.py" 128
  prlimit --memlock=$NOBODY_MEMLOCK setpriv --reuid=65534 --regid=65534 --clear-groups python3 "$NR/mlock_probe.py" 16
  prlimit --memlock=$NOBODY_MEMLOCK setpriv --reuid=65534 --regid=65534 --clear-groups python3 "$NR/mlock_probe.py" 128
} > "$S/mlock.jsonl"
rm -rf "$NR"
if nvidia-smi -L >/dev/null 2>&1; then
  log "Step 5b: pinned vs pageable copies to the GPU (GPU lock held)"
  with_gpu_lock "$HANDSON_PY" "$LAB/pinned_copy.py" --mib 256 --reps 10 > "$S/pinned_copy.json"
else
  log "Step 5b skipped: no GPU"; echo '{"skipped": "no NVIDIA GPU visible"}' > "$S/pinned_copy.json"
fi

# ---------------------------------------------------------------- Step 6: kernel log and /proc signals, idle and saturated
log "Step 6: dmesg and /proc; then $((2 * NCPU)) niced CPU hogs for 12 s (GPU lock held so GPU benchmarks are not disturbed)"
S="$OUT/step6-signals"; mkdir -p "$S"
dmesg -T > "$S/dmesg.txt" 2>&1 || echo "dmesg failed: $?" > "$S/dmesg.txt"
dmesg --level=emerg,alert,crit,err > "$S/dmesg-err.txt" 2>&1 || true
dmesg --level=warn > "$S/dmesg-warn.txt" 2>&1 || true
cat /proc/interrupts > "$S/interrupts.txt"; cat /proc/meminfo > "$S/meminfo.txt"
grep -E '^(oom_kill|pgmajfault|pswpin|pswpout) ' /proc/vmstat > "$S/vmstat-counters.txt"
overload() {
  set -euo pipefail
  for f in cpu io memory; do echo "$f: $(tr '\n' ' ' < /proc/pressure/$f)"; done > "$S/psi-before.txt"
  cat /proc/loadavg > "$S/loadavg-before.txt"
  pids=()
  for _ in $(seq 1 $((2 * NCPU))); do timeout 14 nice -n 19 bash -c 'while :; do :; done' ch03-hog & pids+=($!); done
  sleep 2
  LC_ALL=C vmstat 1 6 > "$S/vmstat-overload.txt"
  sleep 3
  for f in cpu io memory; do echo "$f: $(tr '\n' ' ' < /proc/pressure/$f)"; done > "$S/psi-during.txt"
  cat /proc/loadavg > "$S/loadavg-during.txt"
  kill "${pids[@]}" 2>/dev/null || true; wait 2>/dev/null || true
}
export -f overload; export S NCPU
with_gpu_lock bash -c overload

# ---------------------------------------------------------------- summary
log "summarizing"
"$HANDSON_PY" "$LAB/summarize.py" "$OUT"
"$HANDSON_PY" "$LAB/check.py" "$OUT" || { log "check.py FAILED on this run"; exit 1; }
log "done: $OUT"
