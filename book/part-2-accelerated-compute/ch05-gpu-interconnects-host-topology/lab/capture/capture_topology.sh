#!/usr/bin/env bash
# Chapter 5 lab — L2 capture script. Collects the same files, in the same section format, as the
# lab's data/hosts/<host>/ directories, so your parsers run unchanged on a real host.
#
# Usage (on a GPU host you are authorized to inspect; root needed for full lspci -vvv):
#   sudo bash capture_topology.sh /tmp/topo-$(hostname)
#
# Notes:
#   * The lab's files are simplified/reformatted reconstructions (e.g. gdr_prereqs.txt sections, abridged
#     lstopo). Real output contains more bridges, NVSwitch functions and fields; expect to adapt parsers.
#   * ibdev2netdev is an NVIDIA networking (OFED/DOCA) utility; the sysfs fallback is used if absent.
#   * lldpcli requires lldpd running on the host with LLDP enabled on the backend NICs.
set -euo pipefail
out="${1:-./topo-$(hostname)}"
mkdir -p "$out"

# Every optional tool is guarded so that `set -e` does not abort the capture when one is missing.
nvidia-smi topo -m                                        > "$out/nvidia-smi_topo_m.txt" || echo "# nvidia-smi topo unavailable" > "$out/nvidia-smi_topo_m.txt"
lstopo-no-graphics --no-caches                            > "$out/lstopo.txt"            || echo "# lstopo unavailable (install hwloc)" > "$out/lstopo.txt"
nvidia-smi --query-gpu=index,uuid,pci.bus_id --format=csv > "$out/gpu_inventory.csv"     || echo "# nvidia-smi unavailable" > "$out/gpu_inventory.csv"
lspci -D -vmm -d 15b3:                                    > "$out/lspci_vmm.txt"         || echo "# lspci unavailable" > "$out/lspci_vmm.txt"

if command -v ibdev2netdev >/dev/null 2>&1; then
  ibdev2netdev > "$out/ibdev2netdev.txt"
else
  for d in /sys/class/infiniband/*; do
    hca=$(basename "$d")
    for n in "$d"/device/net/*; do echo "$hca port 1 ==> $(basename "$n") (sysfs)"; done
  done > "$out/ibdev2netdev.txt"
fi

lldpcli show neighbors -f keyvalue > "$out/lldp.txt" 2>/dev/null || echo "# lldpcli unavailable" > "$out/lldp.txt"

{
  echo "### uname -r";                     uname -r
  echo "### cat /proc/cmdline";            cat /proc/cmdline
  echo "### lsmod | grep -E 'nvidia_peermem|nv_peer_mem'"
  lsmod | grep -E 'nvidia_peermem|nv_peer_mem' || true
  echo "### nvidia-smi --query-gpu=driver_version --format=csv,noheader -i 0"
  nvidia-smi --query-gpu=driver_version --format=csv,noheader -i 0 || echo "# unavailable"
  echo "### ofed_info -s";                 (ofed_info -s 2>/dev/null || echo "ofed_info unavailable")
  echo "### lspci -vvv | grep ACSCtl  (downstream switch port directly above each GPU and NIC)"
  # For each GPU (vendor 10de, class 0302) and NIC (vendor 15b3), find its parent bridge and print its ACSCtl.
  # Output format matches the lab data: "<port BDF> (above <device>) ACSCtl:<TAB>SrcValid... ReqRedir..."
  # (parse_gdr reads the first token as the port BDF and looks for "ReqRedir+"; the annotation is ignored).
  for dev in $(lspci -D -d 10de::0302 2>/dev/null | awk '{print $1}') $(lspci -D -d 15b3: 2>/dev/null | awk '{print $1}'); do
    parent=$(basename "$(dirname "$(readlink -f /sys/bus/pci/devices/$dev)")")
    acs=$(lspci -vvv -s "$parent" 2>/dev/null | grep -m1 'ACSCtl:' | sed 's/^[[:space:]]*//')
    echo "$parent (above $dev) ${acs:-ACSCtl: <no ACS capability>}"
  done
} > "$out/gdr_prereqs.txt"

echo "captured to $out"
