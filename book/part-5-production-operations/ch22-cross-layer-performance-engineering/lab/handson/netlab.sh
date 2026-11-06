#!/usr/bin/env bash
# Ch 22 hands-on network: two namespaces joined by a veth pair, the data server in one, the trainer in the other.
#
#   ch22-train [ch22-t0 10.22.0.1/30] <---- veth ----> [ch22-d0 10.22.0.2/30] ch22-data (dataserver.py :8222)
#
#   bash netlab.sh up              create the namespaces, the veth pair and start the data server
#   bash netlab.sh delay <ms>      netem: add <ms> of delay to everything ch22-data sends (the responses)
#   bash netlab.sh nodelay         remove the netem qdisc
#   bash netlab.sh status          addresses, qdisc counters, a ping, the server's health
#   bash netlab.sh down            stop the server and delete both namespaces (and with them the veth pair)
# Touches nothing outside its own namespaces: no host interface, route or firewall rule is changed.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../../../.." && pwd)"
. "$ROOT/scripts/handson/common.sh"
need_root
need_cmd ip tc
NS_T=ch22-train NS_D=ch22-data
PIDFILE=/tmp/ch22-dataserver.pid

case "${1:-}" in
  up)
    ip netns add "$NS_T" 2>/dev/null || true
    ip netns add "$NS_D" 2>/dev/null || true
    if ! ip -n "$NS_T" link show ch22-t0 >/dev/null 2>&1; then
      ip link add ch22-t0 netns "$NS_T" type veth peer name ch22-d0 netns "$NS_D"
    fi
    ip -n "$NS_T" addr replace 10.22.0.1/30 dev ch22-t0
    ip -n "$NS_D" addr replace 10.22.0.2/30 dev ch22-d0
    for ns in "$NS_T" "$NS_D"; do ip -n "$ns" link set lo up; done
    # The data server sends a 64 KB reply per batch on keep-alive connections. With the default
    # tcp_slow_start_after_idle=1, a connection idle longer than its RTO restarts from a 10-segment cwnd,
    # and under the netem delay a 64 KB reply then needs extra round trips of slow start. Prefetching makes each
    # connection idle longer, so the fix would partly undo itself. Off in both arms: the A/B still changes
    # one thing, the number of fetches in flight.
    ip netns exec "$NS_D" sysctl -qw net.ipv4.tcp_slow_start_after_idle=0
    ip -n "$NS_T" link set ch22-t0 up
    ip -n "$NS_D" link set ch22-d0 up
    if ! { [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; }; then
      ip netns exec "$NS_D" python3 "$HERE/dataserver.py" --bind 10.22.0.2 --port 8222 \
        > /tmp/ch22-dataserver.log 2>&1 &
      echo $! > "$PIDFILE"
    fi
    for _ in $(seq 1 50); do
      ip netns exec "$NS_T" python3 -c "import urllib.request as u; u.urlopen('http://10.22.0.2:8222/health', timeout=1)" \
        2>/dev/null && { echo "netlab up"; exit 0; }
      sleep 0.2
    done
    die "data server did not come up (see /tmp/ch22-dataserver.log)"
    ;;
  delay)
    ms="${2:?delay in ms}"
    ip netns exec "$NS_D" tc qdisc replace dev ch22-d0 root netem delay "${ms}ms" limit 10000
    ip netns exec "$NS_D" tc qdisc show dev ch22-d0
    ;;
  nodelay)
    ip netns exec "$NS_D" tc qdisc del dev ch22-d0 root 2>/dev/null || true
    ;;
  status)
    ip -n "$NS_T" -br addr show ch22-t0
    ip -n "$NS_D" -br addr show ch22-d0
    ip netns exec "$NS_D" tc -s qdisc show dev ch22-d0
    ip netns exec "$NS_T" ping -c 5 -i 0.2 -q 10.22.0.2 | tail -2
    ip netns exec "$NS_T" ss -tin dst 10.22.0.2 2>/dev/null | head -6 || true
    ;;
  down)
    if [ -f "$PIDFILE" ]; then kill "$(cat "$PIDFILE")" 2>/dev/null || true; rm -f "$PIDFILE"; fi
    pkill -f "$HERE/dataserver.py" 2>/dev/null || true
    ip netns del "$NS_T" 2>/dev/null || true
    ip netns del "$NS_D" 2>/dev/null || true
    ;;
  *) echo "usage: $0 up|delay <ms>|nodelay|status|down" >&2; exit 2 ;;
esac
