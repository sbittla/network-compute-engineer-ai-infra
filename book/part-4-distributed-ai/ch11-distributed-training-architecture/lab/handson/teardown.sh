#!/usr/bin/env bash
# Chapter 11 hands-on lab: stop any lab process and remove the lab's scratch files.
# The lab creates only processes (torchrun agents and ch11_ddp.py workers) and /tmp/ch11-handson-*.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../../../.." && pwd)"
. "$ROOT/scripts/handson/common.sh"
pkill -TERM -f "ch11_ddp\.py" 2>/dev/null || true
for _ in 1 2 3 4 5; do pgrep -f "ch11_ddp\.py" >/dev/null || break; sleep 1; done
pkill -KILL -f "ch11_ddp\.py" 2>/dev/null || true
rm -rf /tmp/ch11-handson-*
if pgrep -f "ch11_ddp\.py" >/dev/null || compgen -G "/tmp/ch11-handson-*" >/dev/null; then
  echo "teardown: something is left behind" >&2; exit 1
fi
echo "teardown OK: no ch11_ddp.py processes, no /tmp/ch11-handson-* files"
