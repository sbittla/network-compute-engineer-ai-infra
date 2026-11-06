#!/usr/bin/env bash
# Chapter 8 hands-on lab: remove everything the lab created (perftest processes on ch08rxe0, the rxe
# device, the veth pair). Safe to run repeatedly.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../../../.." && pwd)"
. "$ROOT/scripts/handson/common.sh"

need_root
DEV=ch08rxe0
NETDEV=ch08-v0

# Every perftest/pingpong process the lab starts names the device ch08rxe0 on its command line.
pkill -9 -f "(ib_[a-z_]+|ibv_rc_pingpong) .*-d ${DEV}( |$)" 2>/dev/null || true
for _ in 1 2 3 4 5 6 7 8 9 10; do
  pgrep -f "(ib_[a-z_]+|ibv_rc_pingpong) .*-d ${DEV}( |$)" >/dev/null || break
  sleep 0.5
done
# The rxe link must go before its netdev; a QP still held by a dying process can delay it briefly.
for _ in 1 2 3 4 5 6 7 8 9 10; do
  rdma link show "$DEV/1" >/dev/null 2>&1 || break
  rdma link delete "$DEV" 2>/dev/null || sleep 0.5
done
ip link show "$NETDEV" >/dev/null 2>&1 && ip link delete "$NETDEV"

left="$(pgrep -fa "(ib_[a-z_]+|ibv_rc_pingpong) .*-d ${DEV}( |$)" | grep -v pgrep || true)"
[ -z "$left" ] || { echo "teardown: processes still running:"; echo "$left"; exit 1; }
! rdma link show "$DEV/1" >/dev/null 2>&1 || die "teardown: rdma link $DEV still present"
! ip link show "$NETDEV" >/dev/null 2>&1 || die "teardown: $NETDEV still present"
echo "ch08 teardown: clean"
