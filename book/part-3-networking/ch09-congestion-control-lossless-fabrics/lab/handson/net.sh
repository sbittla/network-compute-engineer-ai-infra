#!/usr/bin/env bash
# Chapter 9 hands-on lab: the one-switch fabric, in network namespaces.
#
#   ch09-h1 .. ch09-hN  senders      10.209.0.<i>/24     ch09-h<i>e  <-veth->  ch09-s<i>  (bridge port)
#   ch09-pr             latency probe 10.209.0.200/24    ch09-pr0    <-veth->  ch09-spr   (bridge port)
#   ch09-rx             receiver     10.209.0.100/24     ch09-rx0    <-veth->  ch09-srx   (bridge port: THE BOTTLENECK)
#   ch09-sw             the switch: bridge ch09-br joins every ch09-s* port
#
# The bottleneck is the egress queue of ch09-srx, the switch port that faces the receiver: a token bucket
# (tbf) drains it at 100 Mbit/s, and its child qdisc is the queue under test (drop-tail bfifo or RED).
# netem on the receiver's own port delays everything it sends (ACKs, ping replies) by 2 ms, so the base RTT
# is about 2 ms and the bandwidth-delay product about 25 KB.
#
#   bash net.sh up [N]              create the namespaces, veths and bridge (N senders, default 16)
#   bash net.sh queue <profile>     put a queue profile on the bottleneck droptail | red | asfound | dctcp
#   bash net.sh ecn <0|1>           net.ipv4.tcp_ecn in every sender namespace (1 = request ECN)
#   bash net.sh show                addresses, bridge ports, qdiscs with statistics
#   bash net.sh down                same as teardown.sh
#
# Touches nothing outside its own ch09-* namespaces: the veths are created inside them, and the host's
# interfaces, routes, sysctls and firewall are never changed.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../../../.." && pwd)"
. "$ROOT/scripts/handson/common.sh"
need_root
need_cmd ip tc ethtool

SW=ch09-sw RX=ch09-rx PR=ch09-pr
PORT_DEV=ch09-srx                    # the switch egress port under test
RATE=100mbit                         # bottleneck drain rate
BASE_DELAY=2ms                       # netem on the receiver's port: one-way delay of everything it sends
# Byte thresholds are the chapter's ORION template scaled by the BDP ratio 25 KB / 200 KB = 1/8 (README §2).
BUF=500000                           # physical buffer of the queue: ORION's 4 MB hot-queue share / 8 = 20 BDP
KMIN=18750 KMAX=187500 PMAX=0.2      # template: 150 KB / 8, 1,500 KB / 8, 20 %
KMIN_AF=187500 KMAX_AF=750000        # as found on orion-be-leaf-r3: 1,500 KB / 8, 6,000 KB / 8
AVPKT=1514

ns_exec() { local ns="$1"; shift; ip netns exec "$ns" "$@"; }
nooffload() {  # GSO/TSO/GRO off, so the queue holds real 1,514-byte frames and RED counts real packets
  ns_exec "$1" ethtool -K "$2" tso off gso off gro off >/dev/null 2>&1 || true
}
link_pair() {  # link_pair <ns> <dev-in-ns> <dev-in-switch> <ip>
  ip netns add "$1"
  ip link add "$2" netns "$1" type veth peer name "$3" netns "$SW"
  ip -n "$1" addr add "$4/24" dev "$2"
  ip -n "$1" link set lo up
  ip -n "$1" link set "$2" up
  ip -n "$SW" link set "$3" master ch09-br
  ip -n "$SW" link set "$3" up
  nooffload "$1" "$2"; nooffload "$SW" "$3"
}

case "${1:-}" in
  up)
    n="${2:-16}"
    ip netns list | grep -q "^$SW" && die "the fabric is already up (bash teardown.sh first)"
    ip netns add "$SW"
    ip -n "$SW" link set lo up
    ip -n "$SW" link add ch09-br type bridge stp_state 0
    ip -n "$SW" link set ch09-br up
    nooffload "$SW" ch09-br
    link_pair "$RX" ch09-rx0 "$PORT_DEV" 10.209.0.100
    link_pair "$PR" ch09-pr0 ch09-spr 10.209.0.200
    for i in $(seq 1 "$n"); do link_pair "ch09-h$i" "ch09-h${i}e" "ch09-s$i" "10.209.0.$i"; done
    # TCP Small Queues caps the bytes each socket may have queued below it at about 1 ms of its pacing rate.
    # On one host a sender's skb stays charged to its socket through the veth, the bridge and the switch's
    # queue, so TSQ would stop every flow at ~20 packets and a 500 KB queue would never fill. A real NIC frees
    # the skb when the frame leaves the host. Raising the pacing ratios to their maximum (1000 %) lifts the TSQ
    # cap well above the queue; these senders don't pace (cubic/dctcp, no fq), so nothing else changes.
    for i in $(seq 1 "$n"); do
      ns_exec "ch09-h$i" sysctl -qw net.ipv4.tcp_pacing_ca_ratio=1000 net.ipv4.tcp_pacing_ss_ratio=1000
    done
    # Base RTT: delay what the receiver sends (ACKs, echo replies); the data path keeps only the bottleneck.
    ns_exec "$RX" tc qdisc replace dev ch09-rx0 root netem delay "$BASE_DELAY" limit 100000
    # Learn every MAC on the bridge before the first measurement (one ping from each host to the receiver).
    for h in "$PR" $(seq -f "ch09-h%g" 1 "$n"); do ns_exec "$h" ping -c 1 -W 2 -q 10.209.0.100 >/dev/null || die "no path from $h"; done
    bash "$HERE/net.sh" queue droptail >/dev/null
    echo "fabric up: $n senders, probe, receiver, bridge ch09-br in $SW; bottleneck $PORT_DEV at $RATE"
    ;;
  queue)
    prof="${2:?profile: droptail|red|asfound|dctcp}"
    ns_exec "$SW" tc qdisc del dev "$PORT_DEV" root 2>/dev/null || true
    ns_exec "$SW" tc qdisc add dev "$PORT_DEV" root handle 1: tbf rate "$RATE" burst 3028 limit "$BUF"
    case "$prof" in
      droptail)  child=(bfifo limit "$BUF") ;;
      red)       child=(red limit "$BUF" min "$KMIN" max "$KMAX" avpkt "$AVPKT" burst 50 probability "$PMAX" bandwidth "$RATE" ecn) ;;
      asfound)   child=(red limit "$BUF" min "$KMIN_AF" max "$KMAX_AF" avpkt "$AVPKT" burst 250 probability "$PMAX" bandwidth "$RATE" ecn) ;;
      dctcp)     child=(red limit "$BUF" min "$KMIN" max $((KMIN + AVPKT)) avpkt "$AVPKT" burst 13 probability 1.0 bandwidth "$RATE" ecn) ;;
      *) die "unknown profile $prof" ;;
    esac
    ns_exec "$SW" tc qdisc add dev "$PORT_DEV" parent 1:1 handle 10: "${child[@]}"
    ns_exec "$SW" tc -d qdisc show dev "$PORT_DEV"
    ;;
  ecn)
    v="${2:?0 or 1}"
    for ns in $(ip netns list | awk '{print $1}' | grep -E '^ch09-h[0-9]+$'); do ns_exec "$ns" sysctl -qw net.ipv4.tcp_ecn="$v"; done
    ;;
  show)
    for ns in $(ip netns list | awk '{print $1}' | grep '^ch09-' | sort -V); do
      echo "== $ns"; ip -n "$ns" -br addr show | grep -v '^lo'
    done
    echo "== bridge ports"; ip -n "$SW" -br link show master ch09-br
    echo "== bottleneck $PORT_DEV"; ns_exec "$SW" tc -s -d qdisc show dev "$PORT_DEV"
    echo "== receiver port ch09-rx0"; ns_exec "$RX" tc -s qdisc show dev ch09-rx0
    echo "== offloads on $PORT_DEV"; ns_exec "$SW" ethtool -k "$PORT_DEV" | grep -E '^(tcp-segmentation|generic-segmentation|generic-receive)-offload'
    ;;
  down)
    bash "$HERE/teardown.sh"
    ;;
  *) echo "usage: $0 up [N] | queue <profile> | ecn <0|1> | show | down" >&2; exit 2 ;;
esac
