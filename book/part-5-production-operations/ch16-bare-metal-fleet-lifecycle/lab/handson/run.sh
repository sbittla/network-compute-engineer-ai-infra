#!/usr/bin/env bash
# Chapter 16 hands-on lab: run the node acceptance suite against this machine and write results/<run-id>/.
#   sudo bash run.sh [run-id]
# Environment: CH16_STRESS_S (GPU stress seconds, default 120), CH16_FIO_REPS (default 3),
#              CH16_POLICY (default acceptance_policy_laptop.json next to this script).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../../../.." && pwd)"
. "$ROOT/scripts/handson/common.sh"
# sudo resets PATH to secure_path, which drops WSL2's nvidia-smi directory
[ -d /usr/lib/wsl/lib ] && case ":$PATH:" in *:/usr/lib/wsl/lib:*) ;; *) PATH="$PATH:/usr/lib/wsl/lib" ;; esac

need_root
need_cmd fio ethtool lsblk python3
need_gpu
. "$ROOT/scripts/handson/venv.sh"

OUT="$(run_dir "$HERE" "${1:-}")"
trap 'bash "$HERE/teardown.sh"' EXIT
start=$(date +%s)
echo "results: $OUT"
env_manifest "$OUT/environment.json" "fio --version" "ethtool --version" \
  "$HANDSON_PY -c 'import torch; print(torch.__version__)'" \
  "nvidia-smi --query-gpu=name,driver_version,vbios_version,pcie.link.gen.max,pcie.link.width.max --format=csv,noheader" \
  "command -v dcgmi || echo absent"
mkdir -p "$OUT/raw"

echo "== Stages 1-3 and 5-7: inventory, kernel log, host memory, NICs, disks (read-only fio)"
timeout 900 python3 "$HERE/collect_host.py" --out "$OUT" --fio-reps "${CH16_FIO_REPS:-3}" 2>&1 | tee "$OUT/raw/collect_host.log"

echo "== Stage 4: GPU memory, numerics, stress and telemetry (waits for the shared GPU lock)"
with_gpu_lock timeout 1200 "$HANDSON_PY" "$HERE/gpu_stress.py" --out "$OUT" --seconds "${CH16_STRESS_S:-120}" 2>&1 \
  | tee "$OUT/raw/gpu_stress.log"

echo "== Verdict"
python3 "$HERE/evaluate.py" "$OUT" --policy "${CH16_POLICY:-$HERE/acceptance_policy_laptop.json}" | tee "$OUT/raw/evaluate.log"
echo "elapsed: $(( $(date +%s) - start )) s" | tee "$OUT/raw/elapsed.txt"
python3 "$HERE/check.py" "$OUT"
