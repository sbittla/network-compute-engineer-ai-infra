#!/usr/bin/env bash
# Chapter 21 hands-on lab: stop anything the lab started and, if an opt-in power-cap sweep was interrupted,
# restore the power limit it recorded. Safe to run twice.
set -euo pipefail
LAB="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$LAB/../../../../.." && pwd)"
. "$ROOT/scripts/handson/common.sh"

pkill -f 'ch21_perfwatt\.py' 2>/dev/null || true
pkill -f 'nvidia-smi.*ch21_telemetry' 2>/dev/null || true
for m in "$LAB"/results/.ch21_power_limit_changed; do
  [ -f "$m" ] || continue
  w="$(cat "$m")"
  echo "teardown: restoring the GPU power limit to $w W (interrupted cap sweep)"
  nvidia-smi -pl "$w" && rm -f "$m"
done
left="$(pgrep -fa 'ch21_(telemetry|perfwatt)' | grep -v pgrep || true)"
[ -z "$left" ] && echo "teardown: no ch21 processes left" || { echo "teardown: still running: $left"; exit 1; }
