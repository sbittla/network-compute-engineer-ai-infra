#!/usr/bin/env bash
# Ch 22 hands-on: a competing CPU-bound job, pinned with taskset (the "noisy neighbour").
#   bash hog.sh start <cpu-list> <processes>     e.g. bash hog.sh start 0-3 8
#   bash hog.sh stop
# Each process is a Python busy loop named "ch22-hog" (visible in ps/top), pinned to <cpu-list>.
set -euo pipefail
PIDFILE=/tmp/ch22-hog.pids
case "${1:-}" in
  start)
    cpus="${2:?cpu list}" n="${3:-8}"
    : > "$PIDFILE"
    for _ in $(seq 1 "$n"); do
      taskset -c "$cpus" bash -c 'exec -a ch22-hog python3 -c "while True: pass"' </dev/null >/dev/null 2>&1 &
      echo $! >> "$PIDFILE"
    done
    sleep 0.5
    echo "started $n ch22-hog processes on CPUs $cpus: $(tr '\n' ' ' < "$PIDFILE")"
    ;;
  stop)
    if [ -f "$PIDFILE" ]; then xargs -r kill < "$PIDFILE" 2>/dev/null || true; rm -f "$PIDFILE"; fi
    pkill -f '^ch22-hog' 2>/dev/null || true
    ;;
  *) echo "usage: $0 start <cpu-list> <n> | stop" >&2; exit 2 ;;
esac
