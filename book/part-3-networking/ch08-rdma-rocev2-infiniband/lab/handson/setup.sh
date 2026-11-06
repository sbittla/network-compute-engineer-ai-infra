#!/usr/bin/env bash
# Chapter 8 hands-on lab: install the RDMA user-space tools (idempotent, pinned) and check that the
# kernel has Soft-RoCE (rdma_rxe). Prints the versions.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../../../.." && pwd)"
. "$ROOT/scripts/handson/common.sh"

need_root
# Ubuntu 24.04 (noble) versions; on another distribution the lab accepts that distribution's packages.
PKGS=("rdma-core=50.0-2ubuntu0.2" "ibverbs-utils=50.0-2ubuntu0.2" "ibverbs-providers=50.0-2ubuntu0.2"
      "perftest=24.01.0+0.38-1build2" "iproute2" "util-linux" "bc")
missing=()
for p in "${PKGS[@]}"; do dpkg -s "${p%%=*}" >/dev/null 2>&1 || missing+=("$p"); done
if [ "${#missing[@]}" -gt 0 ]; then
  apt-get -o DPkg::Lock::Timeout=600 update -qq
  if ! DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Lock::Timeout=600 install -y -qq "${missing[@]}" >/dev/null; then
    echo "pinned versions not available here; installing the distribution's packages instead" >&2
    DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Lock::Timeout=600 install -y -qq "${missing[@]%%=*}" >/dev/null
  fi
fi
need_cmd rdma ibv_devinfo ibv_devices ibv_rc_pingpong ib_write_bw ib_write_lat ib_read_lat ib_send_lat ip setpriv ss bc python3

# Soft-RoCE: built in (custom WSL2 kernel, docs/HANDS_ON_LABS.md section 6) or a module (stock Ubuntu kernels).
kconfig() { zcat /proc/config.gz 2>/dev/null || cat "/boot/config-$(uname -r)" 2>/dev/null || true; }
if [ -d /sys/module/rdma_rxe ]; then
  rxe="module loaded"
elif [ "$(kconfig | grep -c '^CONFIG_RDMA_RXE=y')" -gt 0 ]; then
  rxe="built into the kernel (CONFIG_RDMA_RXE=y)"
elif modprobe rdma_rxe 2>/dev/null; then
  rxe="module rdma_rxe loaded"
else
  die "this kernel has no Soft-RoCE (CONFIG_RDMA_RXE). On WSL2 build the kernel in docs/HANDS_ON_LABS.md section 6; on Ubuntu install linux-modules-extra-\$(uname -r)"
fi
# The veth driver carries the rxe device (built in on WSL2; a module elsewhere).
ip link add ch08-probe0 type veth peer name ch08-probe1 2>/dev/null || die "cannot create a veth pair (CONFIG_VETH)"
ip link delete ch08-probe0

echo "kernel:    $(uname -r)"
echo "rdma_rxe:  $rxe"
echo "rdma-core: $(dpkg-query -W -f='${Version}' rdma-core)"
echo "perftest:  $(dpkg-query -W -f='${Version}' perftest)"
echo "iproute2:  $(ip -V)"
echo "memlock:   $(ulimit -l) KiB in this shell (root also holds CAP_IPC_LOCK, which bypasses it)"
echo "setup complete"
