#!/usr/bin/env bash
# Chapter 15 hands-on lab: stop anything the lab started. Safe to run at any time; leaves the venv and model cache.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../../../.." && pwd)"
. "$ROOT/scripts/handson/common.sh"
. "$HERE/lab.env"

pid=$(cat "$CH15_STATE/server.pid" 2>/dev/null || true)
if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
  kill -TERM -- "-$pid" 2>/dev/null || true
  for _ in $(seq 40); do kill -0 "$pid" 2>/dev/null || break; sleep 0.5; done
  kill -KILL -- "-$pid" 2>/dev/null || true
  pkill -KILL -s "$pid" 2>/dev/null || true   # the engine-core child stays in the server's session
fi
# Anything else carrying the lab's served-model name, the lab's helpers, or listening on the lab's port
pkill -KILL -f -- "--served-model-name $CH15_SERVED_NAME" 2>/dev/null || true
pkill -KILL -f -- "ch15-llm-inference-serving/lab/handson/(loadgen|metrics_sampler).py" 2>/dev/null || true
rm -rf "$CH15_STATE"
left=$(pgrep -f -- "--served-model-name $CH15_SERVED_NAME" || true)
[ -z "$left" ] || die "processes still running: $left"
if command -v ss >/dev/null && ss -ltn "sport = :$CH15_PORT" | grep -q LISTEN; then die "port $CH15_PORT still in use"; fi
echo "teardown OK: no ch15 server, port $CH15_PORT free (venv $CH15_VENV and the model cache are kept; remove them by hand)"
