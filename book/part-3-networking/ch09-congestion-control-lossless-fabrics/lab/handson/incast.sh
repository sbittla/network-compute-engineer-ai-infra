#!/usr/bin/env bash
# Chapter 9 hands-on lab: one synchronized N:1 incast through the bottleneck, with all its evidence.
#
#   bash incast.sh <out-dir> <N> <seconds> [cc]
#
# Senders ch09-h1..h<N> each run one iperf3 TCP flow (congestion control <cc>, default cubic) to its own
# iperf3 server on the receiver (10.209.0.100, ports 5201..), all started at the same moment. During the
# run the switch-side queue is sampled every 20 ms (qsample.py) and the probe namespace pings the receiver
# every 20 ms through the same queue. Its echo requests carry ECT(0) (ping -Q 2), so a RED queue marks them
# instead of dropping them.
# Writes into <out-dir>: client_h<i>.json (iperf3 -J), qdisc_{before,after}.{txt,json} (tc -s),
# queue.csv (qsample.py), ping.txt, window.txt (start and end of the clients, epoch seconds), rx_netstat_{before,after}.txt (/proc/net/netstat and snmp of the
# receiver namespace), commands.txt.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../../../.." && pwd)"
. "$ROOT/scripts/handson/common.sh"
need_root
need_cmd iperf3 ip tc ping ss python3

out="${1:?out dir}" n="${2:?N senders}" secs="${3:?seconds}" cc="${4:-cubic}"
mkdir -p "$out"
SW=ch09-sw RX=ch09-rx PR=ch09-pr DEV=ch09-srx RXIP=10.209.0.100
cmds="$out/commands.txt"
netstat_rx() { ip netns exec "$RX" sh -c 'cat /proc/net/netstat /proc/net/snmp'; }

# Servers: one per sender, each serving exactly one test (-1), bound to the receiver's address.
for i in $(seq 1 "$n"); do
  ip netns exec "$RX" timeout $((secs + 30)) iperf3 -s -1 -B "$RXIP" -p $((5200 + i)) >/dev/null 2>&1 &
done
for _ in $(seq 1 100); do
  [ "$(ip netns exec "$RX" ss -Hltn | grep -c "$RXIP:52")" -ge "$n" ] && break
  sleep 0.05
done
echo "\$ ip netns exec $RX iperf3 -s -1 -B $RXIP -p 520<i>   (i = 1..$n)" >> "$cmds"

ip netns exec "$SW" tc -s -d qdisc show dev "$DEV" > "$out/qdisc_before.txt"
ip netns exec "$SW" tc -s -j qdisc show dev "$DEV" > "$out/qdisc_before.json"
netstat_rx > "$out/rx_netstat_before.txt"

ip netns exec "$SW" python3 "$HERE/qsample.py" "$DEV" "$((secs + 1))" "$out/queue.csv" 0.02 &
qs=$!
ip netns exec "$PR" ping -D -n -i 0.02 -Q 2 -w "$((secs + 1))" "$RXIP" > "$out/ping.txt" 2>&1 &
pp=$!
sleep 0.3
echo "\$ ip netns exec $SW python3 qsample.py $DEV $((secs + 1)) queue.csv 0.02" >> "$cmds"
echo "\$ ip netns exec $PR ping -D -n -i 0.02 -Q 2 -w $((secs + 1)) $RXIP" >> "$cmds"

pids=()
date +%s.%N > "$out/window.txt"           # wall-clock window of the incast: aggregate goodput = bytes / window
for i in $(seq 1 "$n"); do
  ip netns exec "ch09-h$i" timeout $((secs + 30)) iperf3 -c "$RXIP" -p $((5200 + i)) -t "$secs" -C "$cc" -J \
    > "$out/client_h$i.json" 2>&1 &
  pids+=($!)
done
echo "\$ ip netns exec ch09-h<i> iperf3 -c $RXIP -p 520<i> -t $secs -C $cc -J   (i = 1..$n, started together)" >> "$cmds"
rc=0
for p in "${pids[@]}"; do wait "$p" || rc=$?; done
date +%s.%N >> "$out/window.txt"
wait "$qs" || true
wait "$pp" || true

ip netns exec "$SW" tc -s -d qdisc show dev "$DEV" > "$out/qdisc_after.txt"
ip netns exec "$SW" tc -s -j qdisc show dev "$DEV" > "$out/qdisc_after.json"
netstat_rx > "$out/rx_netstat_after.txt"
# Any server left (a client that never connected) must not leak into the next run.
pkill -f "iperf3 -s -1 -B $RXIP" 2>/dev/null || true
echo "$rc" > "$out/clients.rc"
exit 0
