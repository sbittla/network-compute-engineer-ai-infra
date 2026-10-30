#!/usr/bin/env python3
"""Generate the Chapter 8 lab datasets (deterministic, seeded).

Produces, under ``lab/data/``:

* ``baseline.yaml``            -- the site's RDMA readiness baseline for ORION backend NICs
* ``inventory/orion-nNN.txt``  -- per-node command captures (ibv_devinfo, rdma link, show_gids,
                                  ethtool, ip, dcb, lsmod, site RDMA env file) for nodes n01..n08
* ``perftest/bw_*.txt``        -- ib_write_bw -a --report_gbits style output, one file per pair/rail
* ``perftest/lat_*.txt``       -- ib_write_lat -a style output, one file per pair/rail
* ``perftest/pcie_link.csv``   -- PCIe link status (LnkSta) per NIC, from an lspci capture

All values are [ILLUSTRATIVE] and modelled on ORION-256 (docs/REFERENCE_CLUSTER.md). Output formats
mimic the real tools closely but are abridged; real output varies by tool and driver version.

Usage:
    python tools/generate_data.py            # writes into ../data relative to this file
    python tools/generate_data.py --seed 8   # same structure, different noise (do not commit)
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

SEED = 8
NODE_IDS = range(1, 9)          # ORION subset: rack-01 and rack-02, nodes orion-n01..n08
RAILS = 8
NETDEVS = [f"ens{r + 1}np0" for r in range(RAILS)]
IFINDEX0 = 4
FW_OK = "28.39.1002"
FW_OLD = "28.36.2024"
DRV_VER = "24.04-0.6.6"
BOARD = "MT_0000000838"
PCI_BUS = ["1a", "1b", "3a", "3b", "9a", "9b", "ba", "bb"]  # NICs sit beside GPUs on PCIe switches

# Planted faults (documented only in solutions/lab/PLANTED_FAULTS.md)
FAULT_MTU = (6, 3)          # node 6, rail 3: netdev MTU 1500
FAULT_FW = (2, 5)           # node 2, rail 5: old firmware after RMA swap
FAULT_DOWN = (3, 6)         # node 3, rail 6: port down / polling
FAULT_PFC = (4, 1)          # node 4, rail 1: PFC on priority 4 instead of 3
FAULT_GID_NODE = 5          # node 5: NCCL_IB_GID_INDEX=2 (RoCE v1 GID)
FAULT_PEERMEM_NODE = 6      # node 6: nvidia_peermem not loaded
FAULT_SWAP = (7, 2, 3)      # node 7: rails 2 and 3 have swapped IP addresses
BW_SLOW = (5, 6, 5)         # pair n05-n06 on rail 5 underperforms ...
PCIE_DOWN = (5, 5)          # ... because orion-n05 mlx5_5 trained at PCIe x8
LAT_TAIL = (7, 8, 2)        # pair n07-n08 on rail 2 has a heavy latency tail


def mac(node: int, rail: int) -> list[int]:
    return [0xB8, 0x3F, 0xD2, 0x47, node, 0x20 + rail]


def mac_str(node: int, rail: int) -> str:
    return ":".join(f"{b:02x}" for b in mac(node, rail))


def eui64_groups(node: int, rail: int) -> list[str]:
    m = mac(node, rail)
    e = [m[0] ^ 0x02, m[1], m[2], 0xFF, 0xFE, m[3], m[4], m[5]]
    return [f"{e[i]:02x}{e[i + 1]:02x}" for i in range(0, 8, 2)]


def node_guid(node: int, rail: int) -> str:
    m = mac(node, rail)
    g = [m[0], m[1], m[2], 0x03, 0x00, m[3], m[4], m[5]]
    return ":".join(f"{g[i]:02x}{g[i + 1]:02x}" for i in range(0, 8, 2))


def host_ip(node: int, rail: int) -> str:
    return f"10.100.{rail}.{2 * node + 1}"


def assigned_ip(node: int, rail: int) -> str:
    n, a, b = FAULT_SWAP
    if node == n and rail == a:
        return host_ip(node, b)
    if node == n and rail == b:
        return host_ip(node, a)
    return host_ip(node, rail)


def ipv4_gid(ip: str) -> str:
    o = [int(x) for x in ip.split(".")]
    return f"0000:0000:0000:0000:0000:ffff:{o[0]:02x}{o[1]:02x}:{o[2]:02x}{o[3]:02x}"


def netdev_mtu(node: int, rail: int) -> int:
    return 1500 if (node, rail) == FAULT_MTU else 9000


def is_down(node: int, rail: int) -> bool:
    return (node, rail) == FAULT_DOWN


# --------------------------------------------------------------------------- inventory sections

def sec_ibv_devinfo(node: int) -> str:
    out = []
    for r in range(RAILS):
        fw = FW_OLD if (node, r) == FAULT_FW else FW_OK
        state = "PORT_DOWN (1)" if is_down(node, r) else "PORT_ACTIVE (4)"
        amtu = "1024 (3)" if netdev_mtu(node, r) == 1500 else "4096 (5)"
        out.append(
            f"hca_id:\tmlx5_{r}\n"
            f"\ttransport:\t\t\tInfiniBand (0)\n"
            f"\tfw_ver:\t\t\t\t{fw}\n"
            f"\tnode_guid:\t\t\t{node_guid(node, r)}\n"
            f"\tsys_image_guid:\t\t\t{node_guid(node, r)}\n"
            f"\tvendor_id:\t\t\t0x02c9\n"
            f"\tvendor_part_id:\t\t\t4129\n"
            f"\thw_ver:\t\t\t\t0x0\n"
            f"\tboard_id:\t\t\t{BOARD}\n"
            f"\tphys_port_cnt:\t\t\t1\n"
            f"\t\tport:\t1\n"
            f"\t\t\tstate:\t\t\t{state}\n"
            f"\t\t\tmax_mtu:\t\t4096 (5)\n"
            f"\t\t\tactive_mtu:\t\t{amtu}\n"
            f"\t\t\tsm_lid:\t\t\t0\n"
            f"\t\t\tport_lid:\t\t0\n"
            f"\t\t\tport_lmc:\t\t0x00\n"
            f"\t\t\tlink_layer:\t\tEthernet\n"
        )
    return "\n".join(out)


def sec_rdma_link(node: int) -> str:
    lines = []
    for r in range(RAILS):
        if is_down(node, r):
            lines.append(f"link mlx5_{r}/1 state DOWN physical_state POLLING netdev {NETDEVS[r]}")
        else:
            lines.append(f"link mlx5_{r}/1 state ACTIVE physical_state LINK_UP netdev {NETDEVS[r]}")
    return "\n".join(lines) + "\n"


def sec_show_gids(node: int) -> str:
    lines = ["DEV\tPORT\tINDEX\tGID\t\t\t\t\tIPv4  \t\tVER\tDEV",
             "---\t----\t-----\t---\t\t\t\t\t------------  \t---\t---"]
    count = 0
    for r in range(RAILS):
        ll = "fe80:0000:0000:0000:" + ":".join(eui64_groups(node, r))
        ip = assigned_ip(node, r)
        g4 = ipv4_gid(ip)
        nd = NETDEVS[r]
        lines.append(f"mlx5_{r}\t1\t0\t{ll}\t\t\tv1\t{nd}")
        lines.append(f"mlx5_{r}\t1\t1\t{ll}\t\t\tv2\t{nd}")
        lines.append(f"mlx5_{r}\t1\t2\t{g4}\t{ip}  \tv1\t{nd}")
        lines.append(f"mlx5_{r}\t1\t3\t{g4}\t{ip}  \tv2\t{nd}")
        count += 4
    lines.append(f"n_gids_found={count}")
    return "\n".join(lines) + "\n"


def sec_ethtool_i(node: int, r: int) -> str:
    fw = FW_OLD if (node, r) == FAULT_FW else FW_OK
    return (
        "driver: mlx5_core\n"
        f"version: {DRV_VER}\n"
        f"firmware-version: {fw} ({BOARD})\n"
        "expansion-rom-version: \n"
        f"bus-info: 0000:{PCI_BUS[r]}:00.0\n"
        "supports-statistics: yes\n"
        "supports-test: yes\n"
        "supports-eeprom-access: no\n"
        "supports-register-dump: no\n"
        "supports-priv-flags: yes\n"
    )


def sec_ethtool(node: int, r: int) -> str:
    if is_down(node, r):
        return (f"Settings for {NETDEVS[r]}:\n\tSpeed: Unknown!\n\tDuplex: Unknown! (255)\n"
                "\tAuto-negotiation: on\n\tPort: Direct Attach Copper\n\tLink detected: no\n")
    return (f"Settings for {NETDEVS[r]}:\n\tSpeed: 400000Mb/s\n\tDuplex: Full\n"
            "\tAuto-negotiation: on\n\tPort: Direct Attach Copper\n\tLink detected: yes\n")


def sec_ip_link(node: int) -> str:
    lines = [f"1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN mode DEFAULT group default qlen 1000\\    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00"]
    for r in range(RAILS):
        idx = IFINDEX0 + r
        if is_down(node, r):
            flags, st = "<NO-CARRIER,BROADCAST,MULTICAST,UP>", "DOWN"
        else:
            flags, st = "<BROADCAST,MULTICAST,UP,LOWER_UP>", "UP"
        lines.append(f"{idx}: {NETDEVS[r]}: {flags} mtu {netdev_mtu(node, r)} qdisc mq state {st} mode DEFAULT "
                     f"group default qlen 1000\\    link/ether {mac_str(node, r)} brd ff:ff:ff:ff:ff:ff")
    return "\n".join(lines) + "\n"


def sec_ip_addr(node: int) -> str:
    lines = ["1: lo    inet 127.0.0.1/8 scope host lo\\       valid_lft forever preferred_lft forever"]
    for r in range(RAILS):
        idx = IFINDEX0 + r
        lines.append(f"{idx}: {NETDEVS[r]}    inet {assigned_ip(node, r)}/31 scope global {NETDEVS[r]}"
                     f"\\       valid_lft forever preferred_lft forever")
    return "\n".join(lines) + "\n"


def sec_dcb_pfc(node: int, r: int) -> str:
    on = {4} if (node, r) == FAULT_PFC else {3}
    prios = " ".join(f"{p}:{'on' if p in on else 'off'}" for p in range(8))
    return f"prio-pfc {prios}\n"


def sec_dcb_app(node: int, r: int) -> str:
    return "dscp-prio 26:3 48:6\n"


def sec_lsmod(node: int) -> str:
    lines = []
    if node != FAULT_PEERMEM_NODE:
        lines.append("nvidia_peermem         16384  0")
    lines += ["mlx5_ib               479232  0",
              "ib_uverbs             184320  2 nvidia_peermem,mlx5_ib" if node != FAULT_PEERMEM_NODE
              else "ib_uverbs             184320  1 mlx5_ib",
              "ib_core               434176  6 rdma_cm,ib_ipoib,iw_cm,ib_umad,ib_uverbs,mlx5_ib",
              "mlx5_core            2367488  1 mlx5_ib"]
    return "\n".join(lines) + "\n"


def sec_env(node: int) -> str:
    gid = 2 if node == FAULT_GID_NODE else 3
    return ("# Managed by fleet config. RDMA settings for training jobs on backend rails.\n"
            "NCCL_IB_HCA=mlx5_0,mlx5_1,mlx5_2,mlx5_3,mlx5_4,mlx5_5,mlx5_6,mlx5_7\n"
            f"NCCL_IB_GID_INDEX={gid}\n"
            "NCCL_IB_TC=106\n")


def build_inventory(node: int) -> str:
    host = f"orion-n{node:02d}"
    parts = [f"### host: {host}", f"### collected: 2026-10-12T09:{14 + node:02d}:03Z",
             "### cmd: ibv_devinfo", sec_ibv_devinfo(node),
             "### cmd: rdma link show", sec_rdma_link(node),
             "### cmd: show_gids", sec_show_gids(node)]
    for r in range(RAILS):
        parts += [f"### cmd: ethtool -i {NETDEVS[r]}", sec_ethtool_i(node, r)]
        parts += [f"### cmd: ethtool {NETDEVS[r]}", sec_ethtool(node, r)]
    parts += ["### cmd: ip -o link show", sec_ip_link(node),
              "### cmd: ip -o -4 addr show", sec_ip_addr(node)]
    for r in range(RAILS):
        parts += [f"### cmd: dcb pfc show dev {NETDEVS[r]} prio-pfc", sec_dcb_pfc(node, r)]
        parts += [f"### cmd: dcb app show dev {NETDEVS[r]} dscp-prio", sec_dcb_app(node, r)]
    parts += ["### cmd: lsmod | grep -E 'peermem|mlx5|ib_core|ib_uverbs'", sec_lsmod(node),
              "### cmd: cat /etc/halcyon/rdma.env", sec_env(node)]
    return "\n".join(p.rstrip("\n") for p in parts) + "\n"


BASELINE = """\
# RDMA deployment-readiness baseline for ORION-256 backend (RoCEv2) NICs.  [ILLUSTRATIVE]
# Owned by the Fabric team; versions must be re-verified against the vendor compatibility matrix.
cluster: ORION-256
subset: [orion-n01, orion-n02, orion-n03, orion-n04, orion-n05, orion-n06, orion-n07, orion-n08]
expected:
  link_layer: Ethernet
  port_state: PORT_ACTIVE
  speed_mbps: 400000
  firmware: "28.39.1002"
  driver: mlx5_core
  driver_version: "24.04-0.6.6"
  netdev_mtu: 9000
  rdma_active_mtu: 4096
  roce_version: v2
  gid_index_variable: NCCL_IB_GID_INDEX
  pfc_enabled_priorities: [3]
  dscp_to_priority: {26: 3, 48: 6}
  peer_memory_module: nvidia_peermem
  address_plan: "10.100.{rail}.{host}/31"   # host = 2*node + 1 (node = NN in orion-nNN)
rails:            # RDMA device -> (rail, netdev)
  mlx5_0: {rail: 0, netdev: ens1np0}
  mlx5_1: {rail: 1, netdev: ens2np0}
  mlx5_2: {rail: 2, netdev: ens3np0}
  mlx5_3: {rail: 3, netdev: ens4np0}
  mlx5_4: {rail: 4, netdev: ens5np0}
  mlx5_5: {rail: 5, netdev: ens6np0}
  mlx5_6: {rail: 6, netdev: ens7np0}
  mlx5_7: {rail: 7, netdev: ens8np0}
"""

# --------------------------------------------------------------------------- perftest

BW_SIZES = [2 ** k for k in range(1, 24)]          # 2 B .. 8 MiB
LAT_SIZES = [2 ** k for k in range(1, 17)]         # 2 B .. 64 KiB
PAIRS = [(1, 2), (3, 4), (5, 6), (7, 8)]


def gen_bw(rng: np.random.Generator, a: int, b: int, rail: int) -> str:
    peak = 392.0                      # Gb/s payload ceiling at 4096 B RoCE MTU [MODELED in manuscript]
    rmax = 11.5e6 * rng.uniform(0.97, 1.03)   # messages/s for one QP with tx-depth 128
    if (a, b, rail) == BW_SLOW:
        peak = 205.0                  # PCIe Gen5 x8 ceiling after protocol overhead
    hdr = (" #bytes     #iterations    BW peak[Gb/sec]    BW average[Gb/sec]   MsgRate[Mpps]")
    sep = "-" * 87
    lines = [sep,
             "                    RDMA_Write BW Test",
             " Dual-port       : OFF\t\tDevice         : mlx5_%d" % rail,
             " Number of qps   : 1\t\tTransport type : IB",
             " Connection type : RC\t\tUsing SRQ      : OFF",
             " TX depth        : 128",
             " CQ Moderation   : 100",
             " Mtu             : 4096[B]",
             " Link type       : Ethernet",
             " GID index       : 3",
             " Max inline data : 0[B]",
             " rdma_cm QPs\t : OFF",
             " Data ex. method : Ethernet",
             sep,
             f" local address: LID 0000 QPN 0x{0x100 + 16 * rail + a:04x} PSN 0x{rng.integers(0, 0xFFFFFF):06x} RKey 0x{rng.integers(0, 0xFFFFFF):06x} VAddr 0x{rng.integers(0x7f0000000000, 0x7fffffffffff):012x}",
             f" GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:100:{rail:02d}:{2 * a + 1:02d}",
             f" remote address: LID 0000 QPN 0x{0x100 + 16 * rail + b:04x} PSN 0x{rng.integers(0, 0xFFFFFF):06x} RKey 0x{rng.integers(0, 0xFFFFFF):06x} VAddr 0x{rng.integers(0x7f0000000000, 0x7fffffffffff):012x}",
             f" GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:100:{rail:02d}:{2 * b + 1:02d}",
             sep, hdr]
    for s in BW_SIZES:
        bits = s * 8
        rate = 1.0 / (1.0 / rmax + bits / (peak * 1e9))   # msgs/s
        avg = bits * rate / 1e9 * rng.uniform(0.985, 1.0)
        pk = avg * rng.uniform(1.0, 1.012)
        lines.append(f" {s:<10d} {5000:<14d} {pk:<18.2f} {avg:<18.2f} {avg * 1e9 / bits / 1e6:.6f}")
    lines.append(sep)
    return "\n".join(lines) + "\n"


def gen_lat(rng: np.random.Generator, a: int, b: int, rail: int) -> str:
    base = 1.85 + rng.uniform(-0.08, 0.08)   # one-way half-RTT at 2 B through one leaf, us
    tail = (a, b, rail) == LAT_TAIL
    sep = "-" * 87
    hdr = (" #bytes #iterations    t_min[usec]    t_max[usec]  t_typical[usec]    t_avg[usec]    "
           "t_stdev[usec]   99% percentile[usec]   99.9% percentile[usec] ")
    lines = [sep, "                    RDMA_Write Latency Test",
             " Dual-port       : OFF\t\tDevice         : mlx5_%d" % rail,
             " Number of qps   : 1\t\tTransport type : IB",
             " Connection type : RC\t\tUsing SRQ      : OFF",
             " Mtu             : 4096[B]", " Link type       : Ethernet", " GID index       : 3",
             " Max inline data : 220[B]", sep, hdr]
    for s in LAT_SIZES:
        ser = s * 8 / 392e9 * 1e6
        extra = 0.0 if s <= 220 else 0.12            # beyond inline size, NIC DMA-reads payload
        typ = base + ser + extra + rng.uniform(0, 0.03)
        tmin = typ - rng.uniform(0.03, 0.08)
        avg = typ + rng.uniform(0.01, 0.05)
        p99 = typ + rng.uniform(0.15, 0.35)
        p999 = typ + rng.uniform(0.8, 2.2)
        tmax = p999 + rng.uniform(2.0, 6.0)
        sd = rng.uniform(0.05, 0.12)
        if tail:
            p99 = typ + rng.uniform(5.5, 7.5)
            p999 = typ + rng.uniform(22.0, 30.0)
            tmax = p999 + rng.uniform(40.0, 70.0)
            avg = typ + rng.uniform(0.25, 0.4)
            sd = rng.uniform(1.4, 2.2)
        lines.append(f" {s:<7d} {1000:<10d}     {tmin:<14.2f} {tmax:<12.2f} {typ:<18.2f} {avg:<16.2f} "
                     f"{sd:<15.2f} {p99:<22.2f} {p999:.2f}")
    lines.append(sep)
    return "\n".join(lines) + "\n"


def gen_pcie(rng: np.random.Generator) -> str:
    rows = ["host,device,bdf,lnkcap,lnksta"]
    for n in NODE_IDS:
        for r in range(RAILS):
            sta = "Speed 32GT/s, Width x16"
            if (n, r) == PCIE_DOWN:
                sta = "Speed 32GT/s, Width x8 (downgraded)"
            rows.append(f"orion-n{n:02d},mlx5_{r},0000:{PCI_BUS[r]}:00.0,\"Speed 32GT/s, Width x16\",\"{sta}\"")
    return "\n".join(rows) + "\n"


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument("--out", type=Path, default=Path(__file__).resolve().parent.parent / "data")
    args = p.parse_args()
    rng = np.random.default_rng(args.seed)
    out: Path = args.out
    (out / "inventory").mkdir(parents=True, exist_ok=True)
    (out / "perftest").mkdir(parents=True, exist_ok=True)
    (out / "baseline.yaml").write_text(BASELINE, encoding="utf-8", newline="\n")
    for n in NODE_IDS:
        (out / "inventory" / f"orion-n{n:02d}.txt").write_text(build_inventory(n), encoding="utf-8", newline="\n")
    for rail in range(RAILS):
        for a, b in PAIRS:
            tag = f"n{a:02d}-n{b:02d}_rail{rail}"
            (out / "perftest" / f"bw_{tag}.txt").write_text(gen_bw(rng, a, b, rail), encoding="utf-8", newline="\n")
            (out / "perftest" / f"lat_{tag}.txt").write_text(gen_lat(rng, a, b, rail), encoding="utf-8", newline="\n")
    (out / "perftest" / "pcie_link.csv").write_text(gen_pcie(rng), encoding="utf-8", newline="\n")
    print(f"wrote dataset to {out}")


if __name__ == "__main__":
    main()
