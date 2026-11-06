#!/usr/bin/env bash
# Ch 4 hands-on teardown: stop anything the lab started and remove its scratch files.
# The lab creates no namespaces, devices or services; it only runs processes and writes /tmp/ch04-handson.
# Nsight Systems stays installed (setup.sh installed it); remove it with:  CH04_PURGE_NSYS=1 bash teardown.sh
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../../../.." && pwd)"
. "$ROOT/scripts/handson/common.sh"
pkill -f "$HERE/train_step.py" 2>/dev/null || true
pkill -f "nvidia-smi --query-gpu=timestamp,utilization.gpu,clocks.sm,power.draw,temperature.gpu,clocks_event_reasons.active" 2>/dev/null || true
rm -rf /tmp/ch04-handson
if [ "${CH04_PURGE_NSYS:-0}" = "1" ]; then
  need_root
  apt-get remove -y -qq 'nsight-systems-2025.6.3' >/dev/null || true
  rm -rf /var/cache/ch04-handson
fi
left="$(pgrep -fa "$HERE/train_step.py" || true)"
[ -z "$left" ] || { echo "still running: $left"; exit 1; }
echo "teardown OK"
