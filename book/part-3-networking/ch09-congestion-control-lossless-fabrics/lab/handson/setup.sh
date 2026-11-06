#!/usr/bin/env bash
# Chapter 9 hands-on lab: install iperf3 and ethtool (idempotent, pinned) and check that the kernel has
# what the lab needs: network namespaces, veth, a bridge, and the tbf, red and netem qdiscs. Prints the versions.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../../../.." && pwd)"
. "$ROOT/scripts/handson/common.sh"

need_root
# Ubuntu 24.04 (noble) versions; on another distribution the lab accepts that distribution's packages.
PKGS=("iperf3=3.16-1build2" "ethtool" "iproute2" "iputils-ping" "kmod")
missing=()
for p in "${PKGS[@]}"; do dpkg -s "${p%%=*}" >/dev/null 2>&1 || missing+=("$p"); done
if [ "${#missing[@]}" -gt 0 ]; then
  apt-get -o DPkg::Lock::Timeout=600 update -qq
  if ! DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Lock::Timeout=600 install -y -qq "${missing[@]}" >/dev/null; then
    echo "pinned versions not available here; installing the distribution's packages instead" >&2
    DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Lock::Timeout=600 install -y -qq "${missing[@]%%=*}" >/dev/null
  fi
fi
# iperf3's Debian package may ask to start a system daemon; the lab never uses one.
if systemctl list-unit-files iperf3.service 2>/dev/null | grep -c '^iperf3' >/dev/null; then
  systemctl disable --now iperf3 >/dev/null 2>&1 || true
fi
need_cmd iperf3 ethtool ip tc ping nstat python3

# Kernel features, tested for real in a throwaway namespace (a config file can lie; a module can be missing).
kcheck() {
  local ns=ch09-probe ok=1
  ip netns del "$ns" 2>/dev/null || true
  ip netns add "$ns"
  ip -n "$ns" link add ch09-pa type veth peer name ch09-pb || ok=0
  if [ "$ok" = 1 ]; then
    ip -n "$ns" link set ch09-pa up
    QD=("tbf rate 100mbit burst 16kb latency 100ms:tbf:CONFIG_NET_SCH_TBF, module sch_tbf"
        "red limit 1000000 min 30000 max 90000 avpkt 1500 burst 30 probability 0.1 bandwidth 100mbit ecn:red:CONFIG_NET_SCH_RED, module sch_red"
        "netem delay 1ms:netem:CONFIG_NET_SCH_NETEM, module sch_netem"
        "bfifo limit 1000000:bfifo:CONFIG_NET_SCHED")
    for q in "${QD[@]}"; do
      IFS=: read -r spec name cfg <<< "$q"
      tc -n "$ns" qdisc replace dev ch09-pa root $spec 2>/dev/null || { echo "missing qdisc: $name ($cfg)"; ok=0; }
    done
    ip -n "$ns" link add ch09-pbr type bridge 2>/dev/null || { echo "missing: bridge (CONFIG_BRIDGE, module bridge)"; ok=0; }
  else
    echo "missing: veth (CONFIG_VETH)"
  fi
  ip netns del "$ns"
  [ "$ok" = 1 ]
}
modprobe -q sch_tbf 2>/dev/null || true
modprobe -q sch_red 2>/dev/null || true
modprobe -q sch_netem 2>/dev/null || true
modprobe -q bridge 2>/dev/null || true
if ! kcheck; then
  die "this kernel lacks a qdisc the lab needs (above). On stock Ubuntu and stock WSL2 kernels they are modules that
load on demand. A custom kernel built with 'make bzImage' only and no 'make modules modules_install' has none:
build and install its modules, or rebuild with CONFIG_NET_SCH_TBF=y, CONFIG_NET_SCH_RED=y, CONFIG_NET_SCH_NETEM=y
and CONFIG_BRIDGE=y (README section 3, 'Kernel')."
fi
# DCTCP is optional: the lab runs the DCTCP configuration only when the kernel offers it.
modprobe -q tcp_dctcp 2>/dev/null || true
if grep -qw dctcp /proc/sys/net/ipv4/tcp_available_congestion_control; then dctcp=available; else dctcp="not available (the dctcp configuration is skipped)"; fi

echo "kernel:    $(uname -r)"
echo "iperf3:    $(iperf3 --version | head -1)"
echo "ethtool:   $(ethtool --version)"
echo "iproute2:  $(ip -V)"
echo "kernel ok: veth, bridge, qdiscs tbf, red (with ecn), netem, bfifo"
echo "tcp cc:    $(cat /proc/sys/net/ipv4/tcp_available_congestion_control); dctcp $dctcp"
echo "setup complete"
