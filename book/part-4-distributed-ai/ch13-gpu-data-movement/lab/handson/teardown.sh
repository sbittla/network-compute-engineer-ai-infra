#!/usr/bin/env bash
# Chapter 13 hands-on lab: stop anything the lab started (benchmarks, DataLoader workers, nvidia-smi
# samplers). The lab changes nothing on the host. Safe to run repeatedly.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../../../.." && pwd)"
. "$ROOT/scripts/handson/common.sh"

for s in copies.py overlap.py loader.py; do pkill -f "$HERE/$s" 2>/dev/null || true; done
left="$(pgrep -fa "$HERE/(copies|overlap|loader).py" || true)"
[ -z "$left" ] || { echo "teardown: still running:"; echo "$left"; exit 1; }
echo "ch13 teardown: clean"
