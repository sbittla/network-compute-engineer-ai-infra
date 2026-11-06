#!/usr/bin/env bash
# Chapter 14 hands-on lab: remove everything the lab created (scratch files and any stray processes).
# Results directories are kept.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../../../.." && pwd)"
. "$ROOT/scripts/handson/common.sh"

EXT4_DIR="${CH14_EXT4_DIR:-/var/tmp/ch14-handson}"
P9_DIR="${CH14_9P_DIR:-/mnt/c/Users/Public/ch14-handson}"

# Only processes this lab started: fio jobs on our files and our Python helpers.
pkill -f -- "--filename=$EXT4_DIR" 2>/dev/null || true
pkill -f -- "--filename=$P9_DIR" 2>/dev/null || true
pkill -f -- "ch14-storage-pipelines-checkpointing/lab/handson/ckpt_bench.py" 2>/dev/null || true

for d in "$EXT4_DIR" "$P9_DIR"; do
  case "$d" in
    */ch14-handson*) rm -rf -- "$d" ;;
    *) echo "refusing to remove $d (name must contain ch14-handson)" >&2 ;;
  esac
done
left=0
for d in "$EXT4_DIR" "$P9_DIR"; do [ -e "$d" ] && { echo "still present: $d" >&2; left=1; }; done
[ "$left" -eq 0 ] && echo "teardown complete: no ch14-handson scratch files left"
