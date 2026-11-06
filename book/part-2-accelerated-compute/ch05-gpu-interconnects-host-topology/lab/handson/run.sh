#!/usr/bin/env bash
# Chapter 5 hands-on lab: host topology from the inside, unattended. Usage: bash run.sh [run-id]
# Writes results/<run-id>/ (environment.json, raw outputs per step, summary.json, report.md).
set -euo pipefail
LAB="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$LAB/../../../../.." && pwd)"
. "$ROOT/scripts/handson/common.sh"

need_root
need_gpu
need_cmd lspci numactl lstopo-no-graphics taskset flock
. "$ROOT/scripts/handson/venv.sh"

OUT="$(run_dir "$LAB" "${1:-}")"
bash "$LAB/teardown.sh" >/dev/null 2>&1 || true
trap 'bash "$LAB/teardown.sh" >/dev/null 2>&1 || true' EXIT
log() { echo "[ch05 $(date +%T)] $*"; }
log "results -> $OUT"
env_manifest "$OUT/environment.json" "lspci --version" "lstopo-no-graphics --version" "numactl --show | head -1" \
  "nvidia-smi --version | head -1" "uname -r" "nproc" "test -d /usr/lib/wsl && echo wsl2 || echo native"

LINKQ="timestamp,pcie.link.gen.current,pcie.link.gen.gpucurrent,pcie.link.gen.max,pcie.link.gen.gpumax,pcie.link.gen.hostmax,pcie.link.width.current,pcie.link.width.max,utilization.gpu,clocks.sm,power.draw"

# ---------------------------------------------------------------- Step 1: what the host shows (read-only)
log "Step 1: topology discovery: nvidia-smi, lspci, hwloc, NUMA, sysfs"
S="$OUT/step1-discovery"; mkdir -p "$S"
nvidia-smi -L > "$S/nvidia-smi-L.txt"
nvidia-smi topo -m > "$S/topo-m.txt" 2>&1 || true
nvidia-smi -q > "$S/nvidia-smi-q.txt"
nvidia-smi --query-gpu=index,name,pci.bus_id,pcie.link.gen.max,pcie.link.gen.hostmax,pcie.link.width.max --format=csv > "$S/gpu-pci.csv"
lspci -D -nn > "$S/lspci-D-nn.txt" 2>&1 || true
lspci -tv > "$S/lspci-tv.txt" 2>&1 || true
lspci -vvv > "$S/lspci-vvv.txt" 2>&1 || true
lstopo-no-graphics --of console > "$S/lstopo.txt" 2>&1 || true
numactl --hardware > "$S/numactl-hardware.txt" 2>&1 || true
ls /sys/devices/system/node/ | grep -E '^node[0-9]+$' > "$S/numa-nodes.txt" || true
for d in /sys/bus/pci/devices/*; do
  [ -e "$d" ] || continue
  echo "$(basename "$d") class=$(cat "$d/class") vendor=$(cat "$d/vendor") device=$(cat "$d/device") numa_node=$(cat "$d/numa_node" 2>/dev/null || echo none) cur_speed=$(cat "$d/current_link_speed" 2>/dev/null | tr ' ' '_' || echo none) cur_width=$(cat "$d/current_link_width" 2>/dev/null || echo none) max_speed=$(cat "$d/max_link_speed" 2>/dev/null | tr ' ' '_' || echo none) max_width=$(cat "$d/max_link_width" 2>/dev/null || echo none)"
done > "$S/sysfs-pci.txt"
BUS="$(nvidia-smi --query-gpu=pci.bus_id --format=csv,noheader | head -1 | tr 'A-F' 'a-f' | sed 's/^0000\(....:\)/\1/')"
{ echo "nvidia-smi bus id (lower case): $BUS"; ls -d "/sys/bus/pci/devices/$BUS" 2>&1 || true; } > "$S/gpu-sysfs-lookup.txt"
for n in /sys/class/net/*; do
  echo "$(basename "$n") device=$(readlink -f "$n/device" 2>/dev/null || echo none) driver=$(basename "$(readlink -f "$n/device/driver" 2>/dev/null)" 2>/dev/null || echo none)"
done > "$S/net-devices.txt"
{ ls /sys/class/infiniband 2>&1 || true; } > "$S/infiniband.txt"

gpu_steps() {
  set -euo pipefail
  # ------------------------------------------------------------ Step 2: link state at idle
  log "Step 2: PCIe link state at idle (5 s at 250 ms)"
  local S="$OUT/step2-link-idle"; mkdir -p "$S"
  timeout 5 nvidia-smi --query-gpu="$LINKQ" --format=csv -lms 250 > "$S/link-idle.csv" 2>&1 || true
  # ------------------------------------------------------------ Step 3: bandwidth against the link's rate
  log "Step 3: H2D/D2H bandwidth sweep, pinned and pageable; then both directions at once"
  S="$OUT/step3-bandwidth"; mkdir -p "$S"
  "$HANDSON_PY" "$LAB/bw.py" sweep > "$S/sweep.json"
  "$HANDSON_PY" "$LAB/bw.py" bidir > "$S/bidir.json"
  # ------------------------------------------------------------ Step 4: what changes under load
  log "Step 4: link state and PCIe counters under sustained copies; copy bandwidth while a GEMM runs"
  S="$OUT/step4-under-load"; mkdir -p "$S"
  timeout 12 nvidia-smi --query-gpu="$LINKQ" --format=csv -lms 250 > "$S/link-load.csv" 2>&1 &
  local q=$!
  timeout 12 nvidia-smi dmon -s t -d 1 > "$S/dmon-pcie.txt" 2>&1 &
  local m=$!
  sleep 1
  "$HANDSON_PY" "$LAB/bw.py" hold --seconds 8 > "$S/hold.json"
  wait "$q" "$m" 2>/dev/null || true
  "$HANDSON_PY" "$LAB/bw.py" contend > "$S/contend.json"
  # ------------------------------------------------------------ Step 5: does the CPU the copy runs on matter here?
  log "Step 5: the same copy with the process bound to CPU 0 / node 0, then to the last CPU"
  S="$OUT/step5-affinity"; mkdir -p "$S"
  numactl --cpunodebind=0 --membind=0 taskset -c 0 "$HANDSON_PY" "$LAB/bw.py" point > "$S/cpu-first.json"
  taskset -c "$(( $(nproc) - 1 ))" "$HANDSON_PY" "$LAB/bw.py" point > "$S/cpu-last.json"
}
export -f gpu_steps log; export OUT LAB HANDSON_PY LINKQ
log "waiting for the GPU lock"
with_gpu_lock bash -c gpu_steps

log "summarizing"
"$HANDSON_PY" "$LAB/summarize.py" "$OUT"
"$HANDSON_PY" "$LAB/check.py" "$OUT" || { log "check.py FAILED on this run"; exit 1; }
log "done: $OUT"
