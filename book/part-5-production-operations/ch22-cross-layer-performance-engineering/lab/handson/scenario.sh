#!/usr/bin/env bash
# Ch 22 hands-on: run the trainer once under a scenario's conditions. Used by run.sh and by you.
#
#   bash scenario.sh <scenario> <arm> <out.json> [extra trainer args]
#     scenario: healthy | loader | cpu | sync | network
#     arm:      bad (the bottleneck present) | fixed (the remedy applied)
#   The environment for the cpu and network scenarios (the hog, the netem delay) is set up by the caller:
#   run.sh does it, and the README shows the commands. The trainer always runs in the ch22-train namespace,
#   pinned with taskset, holding the GPU lock (run.sh takes it once for the whole run).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../../../.." && pwd)"
. "$ROOT/scripts/handson/common.sh"
# sudo resets PATH (secure_path); WSL2 keeps nvidia-smi in /usr/lib/wsl/lib.
[ -d /usr/lib/wsl/lib ] && export PATH="$PATH:/usr/lib/wsl/lib"
. "$ROOT/scripts/handson/venv.sh"
sc="${1:?scenario}" arm="${2:?arm}" out="${3:?output json}"; shift 3
CAL=/tmp/ch22-handson/calibration.env
[ -f "$CAL" ] && . "$CAL"
ROUNDS="${CH22_ROUNDS:-8}"
CPUS_A="${CH22_CPUS_A:-8-11}"     # where the job normally runs (and where the noisy neighbour lands)
CPUS_B="${CH22_CPUS_B:-12-15}"    # a disjoint set of CPUs for the remedy
cpus="$CPUS_A"
args=(--decode-rounds "$ROUNDS" --workers 4 --inflight 1)
case "$sc:$arm" in
  healthy:*)      ;;
  loader:bad)     args=(--decode-rounds "$ROUNDS" --workers 0 --inflight 1) ;;
  loader:fixed)   ;;
  cpu:bad)        ;;                              # same job; the hog shares its CPUs
  cpu:fixed)      cpus="$CPUS_B" ;;               # re-pin the job away from the hog
  sync:bad)       args+=(--inject-sync) ;;
  sync:fixed)     ;;
  network:bad)    ;;                              # same job; netem delays the data server's replies
  network:fixed)  args=(--decode-rounds "$ROUNDS" --workers 4 --inflight 4) ;;
  *) die "unknown scenario/arm: $sc $arm" ;;
esac
mkdir -p "$(dirname "$out")" /tmp/ch22-handson
lock=(with_gpu_lock); [ -n "${CH22_GPU_LOCK_HELD:-}" ] && lock=()   # run.sh already holds it
"${lock[@]}" timeout 900 taskset -c "$cpus" ip netns exec ch22-train "$HANDSON_PY" "$HERE/trainer.py" "${args[@]}" \
  --label "$sc:$arm" --util-file "/tmp/ch22-handson/util-$$.txt" "$@" > "$out" 2> "${out%.json}.stderr"
