#!/usr/bin/env bash
# Chapter 9 hands-on lab: remove everything the lab created (processes in the ch09-* namespaces, the
# namespaces themselves and their veth pairs). Safe to run repeatedly.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../../../.." && pwd)"
. "$ROOT/scripts/handson/common.sh"

need_root
for ns in $(ip netns list | awk '{print $1}' | grep '^ch09-' || true); do
  pids="$(ip netns pids "$ns" 2>/dev/null || true)"
  [ -z "$pids" ] || kill -9 $pids 2>/dev/null || true
done
sleep 0.3
# Deleting a namespace deletes the veth ends inside it, and with them their peers.
for ns in $(ip netns list | awk '{print $1}' | grep '^ch09-' || true); do ip netns del "$ns"; done

left="$(ip netns list | grep '^ch09-' || true)"
[ -z "$left" ] || die "teardown: namespaces still present: $left"
[ "$(ip -o link show | grep -c ' ch09-' || true)" = 0 ] || die "teardown: ch09-* links left in the initial namespace"
echo "ch09 teardown: clean"
