#!/usr/bin/env bash
# Chapter 1 hands-on lab: stop anything the lab started. The lab changes no host settings, so this only
# removes leftover processes (a killed run can leave the nvidia-smi sampler behind). Safe to run twice.
set -euo pipefail
LAB="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$LAB/../../../../.." && pwd)"
. "$ROOT/scripts/handson/common.sh"

pkill -f 'nvidia-smi.*ch01_telemetry' 2>/dev/null || true
pkill -f 'ch01_ceilings\.py' 2>/dev/null || true
left="$(pgrep -fa 'ch01_(telemetry|ceilings)' | grep -v pgrep || true)"
[ -z "$left" ] && echo "teardown: no ch01 processes left" || { echo "teardown: still running: $left"; exit 1; }
