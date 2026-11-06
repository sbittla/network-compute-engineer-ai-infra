#!/usr/bin/env bash
# Ch 22 hands-on teardown: stop the hog, the trainer and the data server; delete the ch22-* namespaces (and with them
# the veth pair and the netem qdisc); remove /tmp/ch22-*. Leaves the machine as it was.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "$HERE/hog.sh" stop 2>/dev/null || true
pkill -f "$HERE/trainer.py" 2>/dev/null || true
bash "$HERE/netlab.sh" down 2>/dev/null || true
for ns in $(ip netns list 2>/dev/null | awk '{print $1}' | grep '^ch22-' || true); do ip netns del "$ns" || true; done
rm -rf /tmp/ch22-handson /tmp/ch22-hog.pids /tmp/ch22-dataserver.pid /tmp/ch22-dataserver.log
left_ns="$(ip netns list 2>/dev/null | grep '^ch22-' || true)"
left_p="$(pgrep -f "^ch22-hog|$HERE/(dataserver|trainer)\.py" || true)"
[ -z "$left_ns$left_p" ] || { echo "left behind: namespaces [$left_ns] pids [$left_p]"; exit 1; }
echo "teardown OK"
