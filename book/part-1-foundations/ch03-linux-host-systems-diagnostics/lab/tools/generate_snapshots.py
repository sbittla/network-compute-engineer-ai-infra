#!/usr/bin/env python3
"""Generate the synthetic ORION host-diagnostic snapshots used by the Chapter 3 lab.

Each snapshot has exactly the JSON schema written by ``host_collector.py`` (``hostdiag/1``):
one section per command, holding the command's argv, status, return code, stdout, stderr and
elapsed time. The stdout text imitates the real tools (lscpu, numactl, free, vmstat, iostat,
mpstat, ip, ethtool, lspci, /proc/interrupts, dmesg, numastat, taskset, nvidia-smi) closely
enough that a parser written against these files will work on real hosts with minor tuning.

All values are [ILLUSTRATIVE] and modelled on the HX8 node in docs/REFERENCE_CLUSTER.md.
INSTRUCTOR MATERIAL: this generator encodes the planted faults (listed in solutions/exercises-key.md)
and is stripped from the student release. Some hosts contain intentionally planted faults; do
the analysis first.

Usage:
    python tools/generate_snapshots.py            # writes ../data/
    python tools/generate_snapshots.py --check    # verify committed data is byte-identical
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

SEED = 3
SCHEMA = "hostdiag/1"
KERNEL = "5.15.0-122-generic"
NCPU = 224
NODE_CPUS = {0: list(range(0, 56)) + list(range(112, 168)), 1: list(range(56, 112)) + list(range(168, 224))}

GPU_BDF = ["18:00.0", "2a:00.0", "3a:00.0", "5d:00.0", "9a:00.0", "ab:00.0", "ba:00.0", "db:00.0"]
RAIL_BDF = ["19:00.0", "29:00.0", "3b:00.0", "5c:00.0", "9b:00.0", "aa:00.0", "bb:00.0", "da:00.0"]
FE_BDF = ["4c:00.0", "cc:00.0"]
NVME_BDF = ["0e:00.0", "0f:00.0", "10:00.0", "11:00.0", "8e:00.0", "8f:00.0", "90:00.0", "91:00.0"]
VGA_BDF = "03:00.0"

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def numa_of(bdf: str) -> int:
    return 0 if int(bdf.split(":")[0], 16) < 0x80 else 1


def cpu_list_str(cpus: list[int]) -> str:
    """Compress a sorted CPU list into kernel range syntax (0-55,112-167)."""
    out, start, prev = [], None, None
    for c in sorted(cpus):
        if start is None:
            start = prev = c
        elif c == prev + 1:
            prev = c
        else:
            out.append(f"{start}-{prev}" if start != prev else str(start))
            start = prev = c
    out.append(f"{start}-{prev}" if start != prev else str(start))
    return ",".join(out)


def section(argv: list[str], stdout: str = "", status: str = "ok", rc: int | None = 0,
            stderr: str = "", elapsed: float = 0.02) -> dict:
    return {"argv": argv, "status": status, "returncode": rc, "stdout": stdout,
            "stderr": stderr, "elapsed_s": round(elapsed, 3)}


# --------------------------------------------------------------------------- tool outputs
def lscpu_text(host: str) -> str:
    rows = [
        ("Architecture", "x86_64"), ("CPU op-mode(s)", "32-bit, 64-bit"),
        ("Address sizes", "52 bits physical, 57 bits virtual"), ("Byte Order", "Little Endian"),
        ("CPU(s)", "224"), ("On-line CPU(s) list", "0-223"), ("Vendor ID", "GenuineIntel"),
        ("Model name", "Intel(R) Xeon(R) Platinum 8480+"), ("CPU family", "6"), ("Model", "143"),
        ("Thread(s) per core", "2"), ("Core(s) per socket", "56"), ("Socket(s)", "2"),
        ("Stepping", "8"), ("CPU max MHz", "3800.0000"), ("CPU min MHz", "800.0000"),
        ("BogoMIPS", "4000.00"), ("Virtualization", "VT-x"),
        ("L1d cache", "5.3 MiB (112 instances)"), ("L1i cache", "3.5 MiB (112 instances)"),
        ("L2 cache", "224 MiB (112 instances)"), ("L3 cache", "210 MiB (2 instances)"),
        ("NUMA node(s)", "2"), ("NUMA node0 CPU(s)", cpu_list_str(NODE_CPUS[0])),
        ("NUMA node1 CPU(s)", cpu_list_str(NODE_CPUS[1])),
    ]
    return "".join(f"{k + ':':<33}{v}\n" for k, v in rows)


def numactl_text(node_size_mb: dict[int, int], node_free_mb: dict[int, int]) -> str:
    lines = ["available: 2 nodes (0-1)"]
    for n in (0, 1):
        lines.append(f"node {n} cpus: " + " ".join(str(c) for c in NODE_CPUS[n]))
        lines.append(f"node {n} size: {node_size_mb[n]} MB")
        lines.append(f"node {n} free: {node_free_mb[n]} MB")
    lines += ["node distances:", "node   0   1 ", "  0:  10  21 ", "  1:  21  10 "]
    return "\n".join(lines) + "\n"


def free_text(total: int, used: int, cache: int) -> str:
    free = total - used - cache
    avail = free + int(cache * 0.9)
    return ("               total        used        free      shared  buff/cache   available\n"
            f"Mem:      {total:>10} {used:>11} {free:>11} {512:>11} {cache:>11} {avail:>11}\n"
            f"Swap:     {0:>10} {0:>11} {0:>11}\n")


def vmstat_text(rng: random.Random, r: tuple[int, int], b: tuple[int, int], us: int, sy: int,
                wa: int, free_kb: int, bi: int) -> str:
    hdr = ("procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----\n"
           " r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st\n")
    rows = []
    # first row: averages since boot (deliberately different from the live samples)
    rows.append((2, 0, 0, free_kb, 412000, 198000000, 0, 0, 1830, 950, 12, 21, 3, 1, 96, 0, 0))
    for _ in range(4):
        rr = rng.randint(*r)
        bb = rng.randint(*b)
        u = max(0, us + rng.randint(-1, 1))
        s = max(0, sy + rng.randint(-1, 1))
        w = max(0, wa + rng.randint(-1, 1)) if wa else 0
        i = 100 - u - s - w
        rows.append((rr, bb, 0, free_kb - rng.randint(0, 9000), 412000, 198000000, 0, 0,
                     bi + rng.randint(-bi // 10, bi // 10) if bi else 0, rng.randint(200, 900),
                     rng.randint(180000, 260000), rng.randint(90000, 140000), u, s, i, w, 0))
    body = "".join("{:>2} {:>2} {:>6} {:>10} {:>6} {:>9} {:>4} {:>4} {:>7} {:>5} {:>6} {:>6} {:>2} {:>2} {:>2} {:>2} {:>2}\n"
                   .format(*row) for row in rows)
    return hdr + body


IOSTAT_COLS = ["r/s", "rkB/s", "rrqm/s", "%rrqm", "r_await", "rareq-sz", "w/s", "wkB/s", "wrqm/s",
               "%wrqm", "w_await", "wareq-sz", "d/s", "dkB/s", "drqm/s", "%drqm", "d_await",
               "dareq-sz", "f/s", "f_await", "aqu-sz", "%util"]


def iostat_text(host: str, rng: random.Random, cpu_live: tuple[float, float, float, float],
                dev_live: dict[str, tuple[float, float, float]]) -> str:
    """dev_live maps device -> (r/s, r_await ms, %util[, rareq-sz KiB]) for the interval report."""
    devices = [f"nvme{i}n1" for i in range(8)] + ["md0", "md1"]
    out = [f"Linux {KERNEL} ({host}) \t10/14/2026 \t_x86_64_\t({NCPU} CPU)", ""]

    def report(cpu: tuple[float, float, float, float], live: dict[str, tuple]) -> None:
        us, sy, wa, idle = cpu
        out.append("avg-cpu:  %user   %nice %system %iowait  %steal   %idle")
        out.append(f"          {us:6.2f}    0.00  {sy:6.2f}  {wa:6.2f}    0.00  {idle:6.2f}")
        out.append("")
        out.append(f"{'Device':<12}" + "".join(f" {c:>9}" for c in IOSTAT_COLS))
        for d in devices:
            rec = live.get(d, (0.0, 0.0, 0.0))
            rs, rawait, util = rec[:3]
            rareq = (rec[3] if len(rec) > 3 else 128.0) if rs else 0.0
            vals = [rs, rs * rareq, 0.0, 0.0, rawait, rareq, 0.4, 3.2, 0.0, 0.0, 0.05, 8.0,
                    0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, round(rs * rawait / 1000, 2), util]
            out.append(f"{d:<12}" + "".join(f" {v:>9.2f}" for v in vals))
        out.append("")

    boot = {d: (35.0, 0.14, 3.1) for d in devices if d.startswith("nvme")}
    boot.update({"md0": (70.0, 0.15, 0.0), "md1": (70.0, 0.15, 0.0)})
    report((2.9, 1.0, 0.4, 95.7), boot)
    report(cpu_live, dev_live)
    return "\n".join(out) + "\n"


def mpstat_text(host: str, rng: random.Random, all_vals: tuple[float, float, float, float, float],
                hot: dict[int, tuple[float, float, float, float]]) -> str:
    """all_vals = (%usr, %sys, %iowait, %soft, %idle) for the 'all' row; hot maps cpu -> (usr, sys, soft, idle)."""
    hdr = "CPU    %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle"
    out = [f"Linux {KERNEL} ({host}) \t10/14/2026 \t_x86_64_\t({NCPU} CPU)", ""]
    for label in ("09:14:52", "Average:"):
        out.append(f"{label:<9}    {hdr}")
        u, s, w, so, i = all_vals
        out.append(f"{label:<9}    all {u:7.2f} {0:7.2f} {s:7.2f} {w:7.2f} {0:7.2f} {so:7.2f} {0:7.2f} {0:7.2f} {0:7.2f} {i:7.2f}")
        for c in range(NCPU):
            if c in hot:
                hu, hs, hso, hi = hot[c]
                hw = 0.0
            else:
                hu = max(0.0, round(u + rng.uniform(-1.5, 1.5), 2))
                hs = max(0.0, round(s + rng.uniform(-0.5, 0.5), 2))
                hw = max(0.0, round(w + rng.uniform(-w / 2, w / 2), 2)) if w else 0.0
                hso = 0.0
                hi = round(100 - hu - hs - hw, 2)
            out.append(f"{label:<9}    {c:>3} {hu:7.2f} {0:7.2f} {hs:7.2f} {hw:7.2f} {0:7.2f} {hso:7.2f} {0:7.2f} {0:7.2f} {0:7.2f} {hi:7.2f}")
        out.append("")
    return "\n".join(out)


def ip_link_text(mtus: dict[str, int], rng: random.Random) -> str:
    lines = ["1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN mode DEFAULT group default qlen 1000",
             "    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00"]
    for idx, (name, mtu) in enumerate(mtus.items(), start=2):
        mac = "b8:3f:d2:" + ":".join(f"{rng.randint(0, 255):02x}" for _ in range(3))
        lines.append(f"{idx}: {name}: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu {mtu} qdisc mq state UP mode DEFAULT group default qlen 1000")
        lines.append(f"    link/ether {mac} brd ff:ff:ff:ff:ff:ff")
    return "\n".join(lines) + "\n"


def ethtool_text(iface: str, speed_mbps: int, link: bool = True) -> str:
    modes = "200000baseCR4/Full 400000baseCR4/Full" if iface.startswith("rail") else "100000baseCR4/Full 200000baseCR4/Full"
    speed = f"{speed_mbps}Mb/s" if link else "Unknown!"
    return (f"Settings for {iface}:\n"
            "\tSupported ports: [ FIBRE ]\n"
            f"\tSupported link modes:   {modes}\n"
            "\tSupported pause frame use: Symmetric\n"
            "\tSupports auto-negotiation: Yes\n"
            f"\tAdvertised link modes:  {modes}\n"
            "\tAdvertised pause frame use: Symmetric\n"
            "\tAdvertised auto-negotiation: Yes\n"
            f"\tSpeed: {speed}\n"
            f"\tDuplex: {'Full' if link else 'Unknown! (255)'}\n"
            "\tAuto-negotiation: on\n"
            "\tPort: Direct Attach Copper\n"
            "\tPHYAD: 0\n"
            "\tTransceiver: internal\n"
            f"\tLink detected: {'yes' if link else 'no'}\n")


def lspci_block(bdf: str, desc: str, subsystem: str, cap: tuple[str, int], sta: tuple[str, int],
                driver: str, root: bool, devsta_corr: bool = False) -> str:
    head = (f"{bdf} {desc}\n"
            f"\tSubsystem: {subsystem}\n"
            "\tControl: I/O- Mem+ BusMaster+ SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR+ FastB2B- DisINTx+\n"
            "\tStatus: Cap+ 66MHz- UDF- FastB2B- ParErr- DEVSEL=fast >TAbort- <TAbort- <MAbort- >SERR- <PERR- INTx-\n"
            f"\tNUMA node: {numa_of(bdf)}\n")
    if not root:
        return head + ("\tCapabilities: <access denied>\n"
                       f"\tKernel driver in use: {driver}\n\n")
    cap_speed, cap_w = cap
    sta_speed, sta_w = sta
    s_flag = "ok" if sta_speed == cap_speed else "downgraded"
    w_flag = "ok" if sta_w == cap_w else "downgraded"
    return head + (
        "\tCapabilities: [60] Express (v2) Endpoint, MSI 00\n"
        "\t\tDevCap:\tMaxPayload 256 bytes, PhantFunc 0, Latency L0s unlimited, L1 <64us\n"
        f"\t\tDevSta:\tCorrErr{'+' if devsta_corr else '-'} NonFatalErr- FatalErr- UnsupReq- AuxPwr- TransPend-\n"
        f"\t\tLnkCap:\tPort #0, Speed {cap_speed}GT/s, Width x{cap_w}, ASPM not supported\n"
        "\t\t\tClockPM+ Surprise- LLActRep- BwNot- ASPMOptComp+\n"
        "\t\tLnkCtl:\tASPM Disabled; RCB 64 bytes, Disabled- CommClk+\n"
        f"\t\tLnkSta:\tSpeed {sta_speed}GT/s ({s_flag}), Width x{sta_w} ({w_flag})\n"
        "\t\t\tTrErr- Train- SlotClk+ DLActive- BWMgmt- ABWMgmt-\n"
        "\tCapabilities: [100 v1] Advanced Error Reporting\n"
        f"\tKernel driver in use: {driver}\n\n")


def device_table(gpu_sta: dict[int, tuple[str, int]]) -> list[dict]:
    """All PCIe endpoints we care about, with capability and current link state."""
    devs = [dict(bdf=VGA_BDF, desc="VGA compatible controller: ASPEED Technology, Inc. ASPEED Graphics Family (rev 52)",
                 sub="ASPEED Technology, Inc. ASPEED Graphics Family", cls="0x030000", ven="0x1a03", dev="0x2000",
                 cap=("5", 1), sta=("5", 1), drv="ast")]
    for i, b in enumerate(NVME_BDF):
        devs.append(dict(bdf=b, desc="Non-Volatile memory controller: Samsung Electronics Co Ltd NVMe SSD Controller PM173X",
                         sub="Samsung Electronics Co Ltd Device a813", cls="0x010802", ven="0x144d", dev="0xa824",
                         cap=("16", 4), sta=("16", 4), drv="nvme"))
    for i, b in enumerate(GPU_BDF):
        devs.append(dict(bdf=b, desc="3D controller: NVIDIA Corporation GH100 [H100 SXM5 80GB] (rev a1)",
                         sub="NVIDIA Corporation GH100 [H100 SXM5 80GB]", cls="0x030200", ven="0x10de", dev="0x2330",
                         cap=("32", 16), sta=gpu_sta.get(i, ("32", 16)), drv="nvidia"))
    for i, b in enumerate(RAIL_BDF):
        devs.append(dict(bdf=b, desc="Ethernet controller: Mellanox Technologies MT2910 Family [ConnectX-7]",
                         sub="Mellanox Technologies Device 0026", cls="0x020000", ven="0x15b3", dev="0x1021",
                         cap=("32", 16), sta=("32", 16), drv="mlx5_core"))
    for b in FE_BDF:
        devs.append(dict(bdf=b, desc="Ethernet controller: Mellanox Technologies MT2892 Family [ConnectX-6 Dx]",
                         sub="Mellanox Technologies Device 0016", cls="0x020000", ven="0x15b3", dev="0x101d",
                         cap=("16", 16), sta=("16", 16), drv="mlx5_core"))
    return sorted(devs, key=lambda d: d["bdf"])


def lspci_text(devs: list[dict], root: bool, corr_bdf: set[str]) -> str:
    return "".join(lspci_block(d["bdf"], d["desc"], d["sub"], d["cap"], d["sta"], d["drv"], root,
                               d["bdf"] in corr_bdf) for d in devs)


def pcie_sysfs_text(devs: list[dict], aer_cor: dict[str, int] | None = None) -> str:
    def spd(s: str) -> str:
        return {"2.5": "2.5 GT/s PCIe", "5": "5.0 GT/s PCIe", "8": "8.0 GT/s PCIe",
                "16": "16.0 GT/s PCIe", "32": "32.0 GT/s PCIe"}[s]
    lines = []
    for d in devs:
        lines.append(";".join([f"0000:{d['bdf']}", f"class={d['cls']}", f"vendor={d['ven']}", f"device={d['dev']}",
                               f"numa_node={numa_of(d['bdf'])}", f"current_link_speed={spd(d['sta'][0])}",
                               f"current_link_width={d['sta'][1]}", f"max_link_speed={spd(d['cap'][0])}",
                               f"max_link_width={d['cap'][1]}",
                               f"aer_cor_total={(aer_cor or {}).get(d['bdf'], 0)}",
                               "aer_nonfatal_total=0", "aer_fatal_total=0"]))
    return "\n".join(lines) + "\n"


def interrupts_text(rng: random.Random, concentrate_on: int | None) -> str:
    """mlx5 completion IRQs for rail0 and fe0 (8 channels each); other IRQs omitted for size."""
    hdr = " " * 4 + "".join(f"{'CPU' + str(c):>11}" for c in range(NCPU))
    lines = [hdr]
    irq = 180
    for name, bdf in (("rail0", RAIL_BDF[0]), ("fe0", FE_BDF[0])):
        local = [c for c in NODE_CPUS[numa_of(bdf)] if c < 112]  # physical cores of the local socket
        for q in range(8):
            counts = [0] * NCPU
            total = rng.randint(40_000_000, 60_000_000)
            if concentrate_on is not None:
                counts[concentrate_on] = total
            else:
                target = local[(q * 7 + (0 if name == "rail0" else 3)) % len(local)]
                counts[target] = total
                counts[local[0]] = rng.randint(50, 400)  # residue from before irqbalance moved it
            cells = "".join(f"{v:>11}" for v in counts)
            lines.append(f"{irq:>4}:{cells}  IR-PCI-MSIX-0000:{bdf}{q + 1:>5}-edge      mlx5_comp{q}@pci:0000:{bdf}")
            irq += 1
    return "\n".join(lines) + "\n"


def dmesg_lines(extra: list[str]) -> str:
    base = [
        "[Mon Oct 12 06:02:11 2026] Linux version 5.15.0-122-generic (buildd@lcy02-amd64-034) (gcc (Ubuntu 11.4.0-1ubuntu1~22.04) 11.4.0, GNU ld (GNU Binutils for Ubuntu) 2.38) #132-Ubuntu SMP",
        "[Mon Oct 12 06:02:19 2026] mlx5_core 0000:19:00.0: firmware version: 28.39.1002",
        "[Mon Oct 12 06:02:21 2026] mlx5_core 0000:19:00.0 rail0: Link up",
        "[Mon Oct 12 06:02:24 2026] nvidia: module license 'NVIDIA' taints kernel.",
        "[Mon Oct 12 06:02:25 2026] NVRM: loading NVIDIA UNIX x86_64 Kernel Module  550.127.05",
        "[Mon Oct 12 06:02:31 2026] nvidia-fabricmanager: Fabric Manager started",
    ]
    return "\n".join(base + extra) + "\n"


def aer_burst(port: str, bdf: str, n: int, day: str = "Wed Oct 14", start_min: int = 2) -> list[str]:
    out = []
    for k in range(n):
        t = f"09:{start_min + k // 6:02d}:{(k * 9) % 60:02d}"
        out += [f"[{day} {t} 2026] pcieport 0000:{port}: AER: Corrected error received: 0000:{bdf}",
                f"[{day} {t} 2026] nvidia 0000:{bdf}: PCIe Bus Error: severity=Corrected, type=Physical Layer, (Receiver ID)",
                f"[{day} {t} 2026] nvidia 0000:{bdf}:   device [10de:2330] error status/mask=00000001/0000e000",
                f"[{day} {t} 2026] nvidia 0000:{bdf}:    [ 0] RxErr                  "]
    return out


def numastat_text(pid: int, node_mb: tuple[float, float]) -> str:
    heap = (node_mb[0] * 0.14, node_mb[1] * 0.14)
    priv = (node_mb[0] - heap[0] - 0.05, node_mb[1] - heap[1])
    tot = (node_mb[0], node_mb[1])
    def row(label: str, a: float, b: float) -> str:
        return f"{label:<16} {a:>15.2f} {b:>15.2f} {a + b:>15.2f}"
    return "\n".join([
        f"Per-node process memory usage (in MBs) for PID {pid} (python3)",
        f"{'':<16} {'Node 0':>15} {'Node 1':>15} {'Total':>15}",
        f"{'':<16} {'-' * 15:>15} {'-' * 15:>15} {'-' * 15:>15}",
        row("Huge", 0.0, 0.0), row("Heap", *heap), row("Stack", 0.05, 0.0), row("Private", *priv),
        f"{'-' * 16} {'-' * 15:>15} {'-' * 15:>15} {'-' * 15:>15}",
        row("Total", *tot)]) + "\n"


def nvidia_smi_text(gen_cur: dict[int, int], width_cur: dict[int, int], util: int, rng: random.Random) -> str:
    lines = ["index, pci.bus_id, pcie.link.gen.current, pcie.link.gen.max, pcie.link.width.current, pcie.link.width.max, utilization.gpu [%]"]
    for i, b in enumerate(GPU_BDF):
        u = max(0, min(100, util + (rng.randint(-3, 2) if util else 0)))
        lines.append(f"{i}, 00000000:{b.upper()}, {gen_cur.get(i, 5)}, 5, {width_cur.get(i, 16)}, 16, {u} %")
    return "\n".join(lines) + "\n"


def cpufreq_text(driver: str, governor: str, cur_khz: tuple[int, int, int]) -> str:
    return (f"scaling_driver: {driver} ({NCPU} cpus)\n"
            f"scaling_governor: {governor} ({NCPU} cpus)\n"
            f"scaling_cur_freq_khz: min={cur_khz[0]} median={cur_khz[1]} max={cur_khz[2]}\n")


# --------------------------------------------------------------------------- host assembly
HEALTHY_DEV = {f"nvme{i}n1": (36.0, 0.15, 3.4) for i in range(8)}
HEALTHY_DEV.update({"md0": (144.0, 0.16, 5.1), "md1": (144.0, 0.16, 5.1)})


def build_host(host: str, rng: random.Random, *, collected_at: str, note: str, root: bool = True,
               pid: int | None = 48211, gpu_sta: dict[int, tuple[str, int]] | None = None,
               gpu_util: int = 97, aer: list[str] | None = None, extra_log: list[str] | None = None,
               node_size: tuple[int, int] = (1031868, 1032151), proc_mem: tuple[float, float] = (205877.4, 2210.6),
               affinity: list[int] | None = None, irq_cpu: int | None = None,
               vm: dict | None = None, io_cpu: tuple[float, float, float, float] = (3.4, 1.2, 0.2, 95.2),
               io_dev: dict | None = None, mp_all: tuple[float, float, float, float, float] = (3.3, 1.2, 0.2, 0.05, 95.25),
               mp_hot: dict | None = None, mtus: dict[str, int] | None = None, speeds: dict[str, int] | None = None,
               cpufreq: tuple[str, str, tuple[int, int, int]] = ("intel_pstate", "performance", (2900000, 3400000, 3800000)),
               sysstat: bool = True, corr_bdf: set[str] | None = None,
               aer_sysfs: dict[str, int] | None = None) -> dict:
    gpu_sta = gpu_sta or {}
    devs = device_table(gpu_sta)
    ifaces = {f"rail{i}": 9000 for i in range(8)}
    ifaces.update({"fe0": 9000, "fe1": 9000})
    if mtus:
        ifaces.update(mtus)
    spd = {n: (400000 if n.startswith("rail") else 200000) for n in ifaces}
    if speeds:
        spd.update(speeds)
    used = int(proc_mem[0] + proc_mem[1]) + 98000
    total = node_size[0] + node_size[1]
    node_free = {0: node_size[0] - int(proc_mem[0]) - 160000, 1: node_size[1] - int(proc_mem[1]) - 140000}
    vm = vm or dict(r=(5, 9), b=(0, 1), us=3, sy=1, wa=0, bi=18000)

    s: dict[str, dict] = {}
    s["uname"] = section(["uname", "-a"], f"Linux {host} {KERNEL} #132-Ubuntu SMP x86_64 x86_64 x86_64 GNU/Linux\n")
    s["lscpu"] = section(["lscpu"], lscpu_text(host))
    s["numactl_hardware"] = section(["numactl", "--hardware"], numactl_text({0: node_size[0], 1: node_size[1]}, node_free))
    s["free"] = section(["free", "-m"], free_text(total, used, 196000))
    s["vmstat"] = section(["vmstat", "1", "5"], vmstat_text(rng, vm["r"], vm["b"], vm["us"], vm["sy"], vm["wa"],
                                                            (total - used - 196000) * 1024, vm["bi"]), elapsed=4.01)
    if sysstat:
        s["iostat"] = section(["iostat", "-x", "1", "2"], iostat_text(host, rng, io_cpu, io_dev or HEALTHY_DEV), elapsed=1.02)
        s["mpstat"] = section(["mpstat", "-P", "ALL", "1", "1"], mpstat_text(host, rng, mp_all, mp_hot or {}), elapsed=1.01)
    else:
        for name, argv in (("iostat", ["iostat", "-x", "1", "2"]), ("mpstat", ["mpstat", "-P", "ALL", "1", "1"])):
            s[name] = section(argv, "", status="missing", rc=None,
                              stderr=f"[Errno 2] No such file or directory: '{argv[0]}'", elapsed=0.0)
    s["ip_link"] = section(["ip", "link", "show"], ip_link_text(ifaces, rng))
    for name in ifaces:
        s[f"ethtool:{name}"] = section(["ethtool", name], ethtool_text(name, spd[name]))
    s["lspci"] = section(["lspci", "-vv"], lspci_text(devs, root, corr_bdf or set()), elapsed=0.41)
    s["pcie_sysfs"] = section(["read", "/sys/bus/pci/devices/*/{class,numa_node,*_link_*,aer_dev_*}"],
                              pcie_sysfs_text(devs, aer_sysfs))
    s["interrupts"] = section(["read", "/proc/interrupts"], interrupts_text(rng, irq_cpu))
    s["cpufreq"] = section(["read", "/sys/devices/system/cpu/cpu*/cpufreq/{scaling_driver,scaling_governor,scaling_cur_freq}"],
                           cpufreq_text(*cpufreq))
    gen_cur = {i: {"2.5": 1, "5": 2, "8": 3, "16": 4, "32": 5}[st[0]] for i, st in gpu_sta.items()}
    width_cur = {i: st[1] for i, st in gpu_sta.items()}
    s["nvidia_smi"] = section(["nvidia-smi", "--query-gpu=index,pci.bus_id,pcie.link.gen.current,pcie.link.gen.max,"
                               "pcie.link.width.current,pcie.link.width.max,utilization.gpu", "--format=csv"],
                              nvidia_smi_text(gen_cur, width_cur, gpu_util, rng), elapsed=0.38)
    if root:
        s["kernel_log"] = section(["dmesg", "-T"], dmesg_lines((aer or []) + (extra_log or [])), elapsed=0.05)
    else:
        s["kernel_log"] = section(["journalctl", "-k", "-b", "--no-pager"], "", status="denied", rc=1,
                                  stderr="dmesg: read kernel buffer failed: Operation not permitted\n"
                                         "No journal files were opened due to insufficient permissions.\n")
    if pid is not None:
        aff = affinity if affinity is not None else NODE_CPUS[0]
        s["numastat_pid"] = section(["numastat", "-p", str(pid)], numastat_text(pid, proc_mem))
        s["taskset_pid"] = section(["taskset", "-cp", str(pid)], f"pid {pid}'s current affinity list: {cpu_list_str(aff)}\n")
    return {"schema": SCHEMA, "host": host, "collected_at": collected_at, "platform": "linux",
            "user_is_root": root, "context": {"pid": pid, "note": note},
            "collector_version": "1.0", "sections": s}


def build_all() -> dict[str, dict]:
    rng = random.Random(SEED)
    hosts: dict[str, dict] = {}

    hosts["orion-n01"] = build_host(
        "orion-n01", rng, collected_at="2026-10-14T09:15:02Z",
        note="W-TRAIN steady state, step 41200; reference node", pid=41377, aer_sysfs={"9b:00.0": 2},
        aer=["[Tue Sep 22 14:40:03 2026] pcieport 0000:97:01.0: AER: Corrected error received: 0000:9b:00.0",
             "[Tue Sep 22 14:40:03 2026] mlx5_core 0000:9b:00.0: PCIe Bus Error: severity=Corrected, type=Physical Layer, (Receiver ID)",
             "[Tue Sep 22 14:40:03 2026] mlx5_core 0000:9b:00.0:    [ 0] RxErr                  ",
             "[Fri Oct  2 03:11:47 2026] pcieport 0000:97:01.0: AER: Corrected error received: 0000:9b:00.0",
             "[Fri Oct  2 03:11:47 2026] mlx5_core 0000:9b:00.0: PCIe Bus Error: severity=Corrected, type=Physical Layer, (Receiver ID)",
             "[Fri Oct  2 03:11:47 2026] mlx5_core 0000:9b:00.0:    [ 0] RxErr                  "])

    hosts["orion-n07"] = build_host(
        "orion-n07", rng, collected_at="2026-10-14T09:16:40Z",
        note="W-TRAIN steady state, step 41205; reported as straggler by training infra",
        gpu_sta={3: ("8", 8)}, aer=aer_burst("5b:01.0", GPU_BDF[3], 37), corr_bdf={GPU_BDF[3]},
        pid=52904, aer_sysfs={GPU_BDF[3]: 37})

    hosts["orion-n12"] = build_host(
        "orion-n12", rng, collected_at="2026-10-14T09:18:11Z",
        note="W-MM image-text fine-tune (shards on local NVMe md0); samples/s poor although CPU utilisation is low",
        proc_mem=(2315.6, 210855.6), affinity=NODE_CPUS[0], irq_cpu=0,
        vm=dict(r=(3, 6), b=(14, 17), us=3, sy=1, wa=7, bi=410000),
        io_cpu=(3.1, 1.1, 6.9, 88.9),
        io_dev={**HEALTHY_DEV, "nvme0n1": (830.0, 0.21, 17.4), "nvme1n1": (830.0, 0.21, 17.4),
                "nvme2n1": (830.0, 0.21, 17.4), "nvme3n1": (830.0, 48.6, 99.9), "md0": (830.0, 49.1, 100.0, 512.0)},
        gpu_util=58,
        mp_all=(3.12, 1.05, 6.90, 0.48, 88.45), mp_hot={0: (0.6, 22.4, 76.5, 0.5)})

    hosts["orion-n19"] = build_host(
        "orion-n19", rng, collected_at="2026-10-14T09:20:37Z",
        note="Returned to service after motherboard-tray swap; first job since RMA", pid=39952,
        node_size=(1031868, 774107), mtus={"rail3": 1500},
        cpufreq=("acpi-cpufreq", "powersave", (800000, 800000, 800000)))

    hosts["orion-n23"] = build_host(
        "orion-n23", rng, collected_at="2026-10-14T09:22:05Z",
        note="W-TRAIN steady state; NCCL bus bandwidth on rail 5 below peers", pid=57118,
        speeds={"rail5": 200000},
        extra_log=[f"[Wed Oct 14 0{6 + k // 5}:{(k * 11) % 60:02d}:{(k * 7) % 60:02d} 2026] EDAC MC2: 1 CE memory read error on "
                   f"CPU_SrcID#1_MC#2_Chan#0_DIMM#0 (channel:0 slot:0 page:0x8f2d31 offset:0x{(k * 64) % 4096:x} grain:32 "
                   "syndrome:0x0 - err_code:0x0000:0x009f)" for k in range(12)] +
                  ["[Wed Oct 14 08:51:30 2026] NVRM: Xid (PCI:0000:ab:00): 63, pid='<unknown>', name=<unknown>, "
                   "Row Remapper: New row (0x00000000000107c3) marked for remapping, reset gpu to activate."])

    hosts["orion-n28"] = build_host(
        "orion-n28", rng, collected_at="2026-10-14T09:24:49Z",
        note="Captured by on-call (non-root) between jobs during maintenance window",
        root=False, pid=None, gpu_util=0, gpu_sta={i: ("2.5", 16) for i in range(8)},
        vm=dict(r=(0, 2), b=(0, 0), us=0, sy=0, wa=0, bi=0),
        cpufreq=("intel_pstate", "powersave", (800000, 1200000, 3800000)), sysstat=False)
    return hosts


BASELINE_YAML = """\
# Expected configuration for an ORION HX8 node (docs/REFERENCE_CLUSTER.md) and the
# severity thresholds used by the Chapter 3 analyzer. All values [ILLUSTRATIVE].
platform: HX8
inventory:
  sockets: 2
  cores_per_socket: 56
  threads_per_core: 2
  numa_nodes: 2
  mem_total_mib_min: 2000000      # 2 TiB installed = 2,097,152 MiB; firmware/kernel reserve some
  numa_node_mem_mb_min: 1000000   # each socket carries 1 TiB
  gpu_count: 8
pcie:
  gpu:  {speed_gts: 32, width: 16}
  nic:  {speed_gts: 32, width: 16}
interfaces:
  rail: {prefix: rail, count: 8, mtu: 9000, speed_mbps: 400000}
  frontend: {prefix: fe, count: 2, mtu: 9000, speed_mbps: 200000}
cpufreq:
  expected_governor: performance
thresholds:
  aer_corrected_warn_per_bdf: 10
  edac_ce_warn: 5
  critical_xids: [48, 74, 79, 94, 95, 119, 120, 140, 154]   # [VENDOR-SPEC, 2026-10] verify against NVIDIA's Xid catalogue
  numa_remote_fraction_warn: 0.25
  numa_remote_fraction_crit: 0.50
  irq_single_cpu_fraction_warn: 0.90
  irq_min_queues: 4
  cpu_hotspot_busy_pct: 90
  cpu_hotspot_all_busy_max_pct: 30
  io_await_ms_warn: 10
  io_util_pct_warn: 90
  vmstat_blocked_warn: 4
  gpu_idle_util_pct: 5
"""


def write_all(out_dir: Path) -> list[Path]:
    snap_dir = out_dir / "snapshots"
    snap_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for host, snap in build_all().items():
        p = snap_dir / f"{host}.json"
        p.write_text(json.dumps(snap, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        written.append(p)
    b = out_dir / "orion_hx8_baseline.yaml"
    b.write_text(BASELINE_YAML, encoding="utf-8", newline="\n")
    written.append(b)
    return written


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=DATA_DIR, help="output directory (default: lab/data)")
    ap.add_argument("--check", action="store_true", help="regenerate to a temp dir and compare byte-for-byte")
    args = ap.parse_args()
    if args.check:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            fresh = write_all(Path(td))
            bad = [f.name for f in fresh
                   if f.read_bytes() != (DATA_DIR / f.relative_to(td)).read_bytes()]
        print("byte-identical" if not bad else f"DIFFERS: {bad}")
        return 1 if bad else 0
    for p in write_all(args.out):
        print(f"wrote {p} ({p.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
