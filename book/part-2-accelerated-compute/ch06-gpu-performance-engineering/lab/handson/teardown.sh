#!/usr/bin/env bash
# Ch 6 hands-on teardown: stop the lab's benchmark processes and telemetry sampler. The lab changes nothing else
# (no clocks, power limits or persistence mode are touched).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
pkill -f "$HERE/protocol.py" 2>/dev/null || true
pkill -f "$HERE/bench.py" 2>/dev/null || true
pkill -f "nvidia-smi --query-gpu=timestamp,clocks.sm,clocks.mem,temperature.gpu,power.draw,utilization.gpu,clocks_event_reasons.active" 2>/dev/null || true
left="$(pgrep -fa "$HERE/(protocol|bench|naive|roofline).py" || true)"
[ -z "$left" ] || { echo "still running: $left"; exit 1; }
echo "teardown OK"
