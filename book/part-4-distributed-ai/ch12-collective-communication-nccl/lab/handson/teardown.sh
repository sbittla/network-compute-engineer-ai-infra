#!/usr/bin/env bash
# Chapter 12 hands-on lab: stop any lab process. The lab creates only processes (torchrun agents and
# ch12_collectives.py workers); it writes nothing outside results/.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../../../.." && pwd)"
. "$ROOT/scripts/handson/common.sh"
pkill -TERM -f "ch12_collectives\.py" 2>/dev/null || true
for _ in 1 2 3 4 5; do pgrep -f "ch12_collectives\.py" >/dev/null || break; sleep 1; done
pkill -KILL -f "ch12_collectives\.py" 2>/dev/null || true
if pgrep -f "ch12_collectives\.py" >/dev/null; then
  echo "teardown: a ch12_collectives.py process is still running" >&2; exit 1
fi
echo "teardown OK: no ch12_collectives.py processes"
