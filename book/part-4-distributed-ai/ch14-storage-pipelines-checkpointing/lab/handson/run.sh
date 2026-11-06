#!/usr/bin/env bash
# Chapter 14 hands-on lab: run every step unattended and write results/<run-id>/.
#   sudo bash run.sh [run-id]
# Environment: CH14_EXT4_DIR (default /var/tmp/ch14-handson), CH14_9P_DIR (default /mnt/c/Users/Public/ch14-handson),
#              CH14_REPS (default 5).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../../../.." && pwd)"
. "$ROOT/scripts/handson/common.sh"
# sudo resets PATH to secure_path, which drops WSL2's nvidia-smi directory
[ -d /usr/lib/wsl/lib ] && case ":$PATH:" in *:/usr/lib/wsl/lib:*) ;; *) PATH="$PATH:/usr/lib/wsl/lib" ;; esac

need_root
need_cmd fio python3 findmnt
need_gpu
. "$ROOT/scripts/handson/venv.sh"

OUT="$(run_dir "$HERE" "${1:-}")"
REPS="${CH14_REPS:-5}"
trap 'bash "$HERE/teardown.sh"' EXIT
bash "$HERE/teardown.sh" >/dev/null   # start clean
start=$(date +%s)
echo "results: $OUT"

env_manifest "$OUT/environment.json" "fio --version" "$HANDSON_PY -c 'import torch; print(torch.__version__)'" \
  "findmnt -no FSTYPE,SOURCE --target /var/tmp" "findmnt -no FSTYPE,SOURCE --target /mnt/c" \
  "lsblk -dno NAME,TYPE,SIZE,ROTA,MODEL" \
  "nvidia-smi --query-gpu=pcie.link.gen.max,pcie.link.width.max --format=csv,noheader"
mkdir -p "$OUT/raw"
cat /proc/meminfo > "$OUT/raw/meminfo-start.txt"

echo "== Steps 1-3: fio (about 9 minutes)"
timeout 3600 python3 "$HERE/fio_sweep.py" --out "$OUT" --reps "$REPS" 2>&1 | tee "$OUT/raw/fio_sweep.log"

echo "== Step 4: checkpoints on the GPU (waits for the shared GPU lock)"
with_gpu_lock timeout 1800 "$HANDSON_PY" "$HERE/ckpt_bench.py" --out "$OUT" --reps "$REPS" 2>&1 \
  | grep -v -e 'TypedStorage is deprecated' -e 'tensor.storage().size()' | tee "$OUT/raw/ckpt_bench.log"

cat /proc/meminfo > "$OUT/raw/meminfo-end.txt"
echo "== Step 5: summary, Young/Daly and report"
python3 "$HERE/summarize.py" "$OUT"
echo "elapsed: $(( $(date +%s) - start )) s" | tee "$OUT/raw/elapsed.txt"
python3 "$HERE/check.py" "$OUT"
