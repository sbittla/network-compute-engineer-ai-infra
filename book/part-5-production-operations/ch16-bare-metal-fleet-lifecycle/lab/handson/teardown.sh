#!/usr/bin/env bash
# Chapter 16 hands-on lab: stop anything the suite started. It creates no files outside results/,
# no interfaces and no devices; every device test is read-only. Results directories are kept.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../../../.." && pwd)"
. "$ROOT/scripts/handson/common.sh"

pkill -f -- "--name=ch16-" 2>/dev/null || true                                   # fio jobs
pkill -f -- "ch16-bare-metal-fleet-lifecycle/lab/handson/gpu_stress.py" 2>/dev/null || true
pkill -f -- "ch16-bare-metal-fleet-lifecycle/lab/handson/collect_host.py" 2>/dev/null || true
# nvidia-smi samplers are children of gpu_stress.py and die with it; check none is left.
if pgrep -f -- "--name=ch16-|ch16-bare-metal-fleet-lifecycle/lab/handson/(gpu_stress|collect_host).py" >/dev/null; then
  echo "processes still running:" >&2; pgrep -af -- "--name=ch16-|ch16-bare-metal-fleet-lifecycle/lab/handson/(gpu_stress|collect_host).py" >&2; exit 1
fi
echo "teardown complete: no ch16 processes left"
