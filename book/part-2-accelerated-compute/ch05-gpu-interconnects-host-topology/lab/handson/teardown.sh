#!/usr/bin/env bash
# Chapter 5 hands-on lab: stop anything the lab started. The lab changes nothing on the host; it only runs
# copy benchmarks and nvidia-smi samplers, all under timeout. Safe to run repeatedly.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../../../.." && pwd)"
. "$ROOT/scripts/handson/common.sh"

pkill -f "$HERE/bw.py" 2>/dev/null || true
left="$(pgrep -fa "$HERE/bw.py" || true)"
[ -z "$left" ] || { echo "teardown: still running:"; echo "$left"; exit 1; }
echo "ch05 teardown: clean"
