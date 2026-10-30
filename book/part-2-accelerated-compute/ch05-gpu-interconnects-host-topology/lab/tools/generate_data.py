#!/usr/bin/env python3
"""Generate raw topology captures for four ORION HX8 hosts (Chapter 5 lab).

For each host it writes the files an engineer would collect during node acceptance:

    nvidia-smi_topo_m.txt   `nvidia-smi topo -m`
    lstopo.txt              `lstopo-no-graphics --no-caches` (abridged: Core/PU objects removed)
    gpu_inventory.csv       `nvidia-smi --query-gpu=index,uuid,pci.bus_id --format=csv`
    lspci_vmm.txt           `lspci -D -vmm -d 15b3:` (Mellanox/NVIDIA NICs; abridged fields)
    ibdev2netdev.txt        `ibdev2netdev` (vendor OFED/DOCA utility)
    lldp.txt                `lldpcli show neighbors -f keyvalue` (abridged keys)
    gdr_prereqs.txt         kernel cmdline, peer-memory module, driver/OFED versions, ACSCtl of the downstream
                            switch ports above each GPU/NIC (sections reformatted; see lab/capture/)

All outputs are [ILLUSTRATIVE] reconstructions of what these tools print on an H100-class 8-GPU
server shaped like docs/REFERENCE_CLUSTER.md Figure R.1; field layouts are abridged and version-sensitive.
Some hosts carry planted faults (documented only in solutions/).

Also writes data/path_model.yaml: [ILLUSTRATIVE] per-path-class bandwidth/variance parameters for the
[MODELED] all-reduce estimate.

Deterministic: seed 5; regeneration is byte-identical.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

SEED = 5
REL_ORDER = ["X", "PIX", "PXB", "PHB", "NODE", "SYS"]


def uuid(rng: np.random.Generator) -> str:
    v = [int(x) for x in rng.integers(0, 2**32, size=5, dtype=np.uint64)]
    return f"GPU-{v[0]:08x}-{v[1] & 0xffff:04x}-{v[2] & 0xffff:04x}-{v[3] & 0xffff:04x}-{v[4]:08x}{v[0] & 0xffff:04x}"


def base_layout() -> list[dict]:
    """Device list with tree paths. path = (package, hostbridge, bridge1, bridge2, ...)."""
    devs = []

    def gpu(i, bus, pkg, hb, path, slot):
        devs.append({"kind": "GPU", "idx": i, "bus": bus, "pkg": pkg, "path": (f"HB{hb}",) + path, "slot": slot})

    def nic(rail, bus, pkg, hb, path, slot):
        devs.append({"kind": "NIC", "rail": rail, "bus": bus, "pkg": pkg, "path": (f"HB{hb}",) + path, "slot": slot})

    def other(kind, bus, pkg, hb, path, label, slot=None):
        devs.append({"kind": kind, "bus": bus, "pkg": pkg, "path": (f"HB{hb}",) + path, "label": label, "slot": slot})

    # Each "SWk" is a two-level PCIe switch complex: a top switch (upstream port SWku, one downstream port per
    # leaf) and two leaf switches (upstream port SWkXu, one downstream port per device: SWkXd0 -> GPU,
    # SWkXd1 -> NIC). Every device sits alone under its own downstream port, as on real hardware.
    def pair(k, x, i, gbus, pkg, hb, rp, nslot):
        up = (rp, f"SW{k}u", f"SW{k}d{x}", f"SW{k}{x}u")
        gpu(i, gbus, pkg, hb, up + (f"SW{k}{x}d0",), None)
        nic(i, gbus + 1, pkg, hb, up + (f"SW{k}{x}d1",), nslot)

    # socket 0
    pair(0, "A", 0, 0x18, 0, 0, "RP0a", 1); pair(0, "B", 1, 0x22, 0, 0, "RP0a", 2)
    nic("fe0", 0x0d, 0, 0, ("RP0b",), 9)
    other("NVMe", 0x0e, 0, 0, ("RP0c",), "nvme0n1")
    pair(1, "A", 2, 0x38, 0, 1, "RP1a", 3); pair(1, "B", 3, 0x42, 0, 1, "RP1a", 4)
    other("NVMe", 0x4e, 0, 1, ("RP1c",), "nvme1n1")
    # socket 1
    pair(2, "A", 4, 0x98, 1, 2, "RP2a", 5); pair(2, "B", 5, 0xA2, 1, 2, "RP2a", 6)
    nic("fe1", 0x8D, 1, 2, ("RP2b",), 10)
    other("NVMe", 0x8E, 1, 2, ("RP2c",), "nvme2n1")
    pair(3, "A", 6, 0xB8, 1, 3, "RP3a", 7); pair(3, "B", 7, 0xC2, 1, 3, "RP3a", 8)
    other("NVMe", 0xCE, 1, 3, ("RP3c",), "nvme3n1")
    return devs


HOSTS = {
    # name: (node number for LLDP port, layout mutator, gdr profile)
    "orion-n01": {"node": 1},
    "orion-n02": {"node": 2, "acs": True, "cmdline_pt": False},
    "orion-n17": {"node": 17, "misplaced_rail3": True},
    "orion-n23": {"node": 23, "swap_rails": (4, 5), "peermem": False, "driver": "550.127.05"},
}
FLEET_DRIVER = "570.124.06"
FLEET_OFED = "MLNX_OFED_LINUX-24.10-1.1.4.0"


def relation(a: dict, b: dict) -> str:
    if a is b:
        return "X"
    if a["pkg"] != b["pkg"]:
        return "SYS"
    pa, pb = a["path"], b["path"]
    if pa[0] != pb[0]:
        return "NODE"
    common = 0
    for x, y in zip(pa, pb):
        if x != y:
            break
        common += 1
    # PIX: the deepest common ancestor is one switch's upstream port and each device hangs directly from
    # one of its downstream ports. PXB: the path crosses more than one switch (below the host bridge).
    # PHB: the only shared ancestor is the host bridge.
    if common >= 2 and len(pa) - common == 1 and len(pb) - common == 1:
        return "PIX"
    if common >= 2:
        return "PXB"
    return "PHB"


def build_host(name: str, cfg: dict) -> list[dict]:
    devs = base_layout()
    if cfg.get("misplaced_rail3"):
        for d in devs:
            if d["kind"] == "NIC" and d["rail"] == 3:
                d.update({"bus": 0x86, "pkg": 1, "path": ("HB2", "RP2d"), "slot": 11})
    nics = sorted([d for d in devs if d["kind"] == "NIC"], key=lambda d: d["bus"])
    for i, d in enumerate(nics):
        # The golden image pins RDMA device names to rails (compute NIC on rail r -> mlx5_r, frontend
        # NICs -> mlx5_8/mlx5_9). nvidia-smi numbers its NIC columns in PCI bus order, so NICk != mlx5_k.
        d["hca"] = f"mlx5_{d['rail']}" if isinstance(d["rail"], int) else ("mlx5_8" if d["rail"] == "fe0" else "mlx5_9")
        d["netdev"] = f"enp{d['bus']}s0np0"
        d["topo_name"] = f"NIC{i}"
        if isinstance(d["rail"], int):
            d["leaf"] = f"orion-be-leaf-r{d['rail']}"
        else:
            d["leaf"] = "orion-fe-leaf-01" if d["rail"] == "fe0" else "orion-fe-leaf-02"
    if "swap_rails" in cfg:
        r1, r2 = cfg["swap_rails"]
        n1 = next(d for d in nics if d["rail"] == r1)
        n2 = next(d for d in nics if d["rail"] == r2)
        n1["leaf"], n2["leaf"] = n2["leaf"], n1["leaf"]
    return devs


def bdf(bus: int) -> str:
    return f"0000:{bus:02x}:00.0"


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def topo_m(devs: list[dict]) -> str:
    gpus = sorted([d for d in devs if d["kind"] == "GPU"], key=lambda d: d["idx"])
    nics = sorted([d for d in devs if d["kind"] == "NIC"], key=lambda d: d["topo_name"])
    cols = [f"GPU{g['idx']}" for g in gpus] + [n["topo_name"] for n in nics]
    rows = gpus + nics
    out = ["\t" + "\t".join(cols) + "\tCPU Affinity\tNUMA Affinity\tGPU NUMA ID"]
    for r in rows:
        label = f"GPU{r['idx']}" if r["kind"] == "GPU" else r["topo_name"]
        cells = []
        for c in rows:
            if r["kind"] == "GPU" and c["kind"] == "GPU" and r is not c:
                cells.append("NV18")
            else:
                cells.append(relation(r, c))
        line = label + "\t" + "\t".join(f"{x:<4}" if x != "X" else " X  " for x in cells)
        if r["kind"] == "GPU":
            aff = "0-55,112-167" if r["pkg"] == 0 else "56-111,168-223"
            line += f"\t{aff}\t{r['pkg']}\tN/A"
        out.append(line.rstrip())
    out += ["", "Legend:", "",
            "  X    = Self",
            "  SYS  = Connection traversing PCIe as well as the SMP interconnect between NUMA nodes (e.g., QPI/UPI)",
            "  NODE = Connection traversing PCIe as well as the interconnect between PCIe Host Bridges within a NUMA node",
            "  PHB  = Connection traversing PCIe as well as a PCIe Host Bridge (typically the CPU)",
            "  PXB  = Connection traversing multiple PCIe bridges (without traversing the PCIe Host Bridge)",
            "  PIX  = Connection traversing at most a single PCIe bridge",
            "  NV#  = Connection traversing a bonded set of # NVLinks", "", "NIC Legend:", ""]
    out += [f"  {n['topo_name']}: {n['hca']}" for n in nics]
    return "\n".join(out) + "\n"


def lstopo(devs: list[dict]) -> str:
    lines = ["Machine (2015GB total)"]
    for pkg in (0, 1):
        lines.append(f"  Package L#{pkg}")
        lines.append(f"    NUMANode L#{pkg} (P#{pkg} 1007GB)")
        pdevs = sorted([d for d in devs if d["pkg"] == pkg], key=lambda d: (d["path"], d["bus"]))
        printed: list[tuple] = []
        for d in pdevs:
            path = d["path"]
            for depth in range(len(path)):
                prefix = path[: depth + 1]
                if prefix in printed:
                    continue
                printed.append(prefix)
                ind = "    " + "  " * depth
                lines.append(ind + ("HostBridge" if depth == 0 else "PCIBridge"))
            ind = "    " + "  " * len(path)
            if d["kind"] == "GPU":
                lines += [f"{ind}PCI {d['bus']:02x}:00.0 (3D)", f'{ind}  GPU(NVML) "nvml{d["idx"]}"']
            elif d["kind"] == "NIC":
                lines += [f"{ind}PCI {d['bus']:02x}:00.0 (Ethernet)", f'{ind}  Net "{d["netdev"]}"',
                          f'{ind}  OpenFabrics "{d["hca"]}"']
            else:
                lines += [f"{ind}PCI {d['bus']:02x}:00.0 (NVMExp)", f'{ind}  Block(Disk) "{d["label"]}"']
    return "\n".join(lines) + "\n"


def lspci_vmm(devs: list[dict]) -> str:
    out = []
    for d in sorted([d for d in devs if d["kind"] == "NIC"], key=lambda d: d["bus"]):
        out += [f"Slot:\t{bdf(d['bus'])}", "Class:\tEthernet controller", "Vendor:\tMellanox Technologies",
                "Device:\tMT2910 Family [ConnectX-7]", f"PhySlot:\t{d['slot']}", "Driver:\tmlx5_core",
                f"NUMANode:\t{d['pkg']}", ""]
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parent.parent / "data")
    args = ap.parse_args()
    rng = np.random.default_rng(SEED)
    for name, cfg in HOSTS.items():
        devs = build_host(name, cfg)
        hd = args.out / "hosts" / name
        hd.mkdir(parents=True, exist_ok=True)
        write(hd / "nvidia-smi_topo_m.txt", topo_m(devs))
        write(hd / "lstopo.txt", lstopo(devs))
        gpus = sorted([d for d in devs if d["kind"] == "GPU"], key=lambda d: d["idx"])
        write(hd / "gpu_inventory.csv", "index, uuid, pci.bus_id\n" +
              "".join(f"{g['idx']}, {uuid(rng)}, 0000{bdf(g['bus'])}\n" for g in gpus))
        write(hd / "lspci_vmm.txt", lspci_vmm(devs))
        nics = sorted([d for d in devs if d["kind"] == "NIC"], key=lambda d: d["bus"])
        write(hd / "ibdev2netdev.txt", "".join(f"{n['hca']} port 1 ==> {n['netdev']} (Up)\n" for n in nics))
        lldp = []
        for n in nics:
            port = f"Ethernet{cfg['node']}" if n["leaf"].startswith("orion-be-leaf") else f"Ethernet{cfg['node'] + 32}"
            lldp += [f"lldp.{n['netdev']}.via=LLDP", f"lldp.{n['netdev']}.chassis.name={n['leaf']}",
                     f"lldp.{n['netdev']}.port.ifname={port}"]
        write(hd / "lldp.txt", "\n".join(lldp) + "\n")
        cmd = "BOOT_IMAGE=/vmlinuz-6.8.0-45-generic root=UUID=3f1c9a52-6c1e-4f0e-9a51-0d6b8e2f7a10 ro intel_iommu=on"
        cmd += " iommu=pt" if cfg.get("cmdline_pt", True) else ""
        cmd += " console=ttyS0,115200n8"
        g = ["### uname -r", "6.8.0-45-generic", "### cat /proc/cmdline", cmd,
             "### lsmod | grep -E 'nvidia_peermem|nv_peer_mem'"]
        if cfg.get("peermem", True):
            g.append("nvidia_peermem         16384  0")
        g += ["### nvidia-smi --query-gpu=driver_version --format=csv,noheader -i 0", cfg.get("driver", FLEET_DRIVER),
              "### ofed_info -s", FLEET_OFED + ":",
              "### lspci -vvv | grep ACSCtl  (downstream switch port directly above each GPU and NIC)"]
        acs_on = cfg.get("acs", False)
        flags = ("SrcValid+ TransBlk- ReqRedir+ CmpltRedir+ UpstreamFwd+ EgressCtrl- DirectTrans-" if acs_on
                 else "SrcValid- TransBlk- ReqRedir- CmpltRedir- UpstreamFwd- EgressCtrl- DirectTrans-")
        for d in sorted([d for d in devs if d["kind"] in ("GPU", "NIC") and len(d["path"]) == 6], key=lambda d: d["bus"]):
            gbus = d["bus"] if d["kind"] == "GPU" else d["bus"] - 1
            port_bdf = f"0000:{gbus - 1:02x}:{0 if d['kind'] == 'GPU' else 1:02x}.0"
            what = f"GPU{d['idx']}" if d["kind"] == "GPU" else d["hca"]
            g.append(f"{port_bdf} (above {what}) ACSCtl:\t{flags}")
        write(hd / "gdr_prereqs.txt", "\n".join(g) + "\n")

    write(args.out / "path_model.yaml", """# [ILLUSTRATIVE] parameters for the Chapter 5 [MODELED] all-reduce estimate.
# Effective per-direction GPU<->NIC<->fabric bandwidth (GB/s) and coefficient of variation per
# GPU-to-NIC path class. Calibrate against nccl-tests on real hardware before trusting any output.
line_rate_GBps: 50.0          # 400 Gb/s NIC
classes:
  PIX:  {mean_GBps: 48.0, cv: 0.02}
  PXB:  {mean_GBps: 45.0, cv: 0.03}
  PHB:  {mean_GBps: 40.0, cv: 0.06}
  NODE: {mean_GBps: 36.0, cv: 0.08}
  SYS:  {mean_GBps: 24.0, cv: 0.18}   # only reachable if NCCL_NET_GDR_LEVEL=SYS; ~ UPI share, see manuscript 5.9
modifiers:
  acs_redirect: {bw_factor: 0.70, cv_add: 0.06}   # P2P TLPs redirected up to the root complex
  host_staged:  {bw_cap_GBps: 18.0, cv_add: 0.10} # no GPUDirect RDMA: bounce through host memory
  shared_nic:   {divide_by_sharers: true}          # two GPUs driving one NIC share its bandwidth
alpha_ms: 0.2                 # fixed per-collective latency term
gdr_max_relation: PXB         # NCCL_NET_GDR_LEVEL default in recent releases (~PXB; verify per release):
                              # GPU-NIC pairs farther than this are host-staged even when peer memory works
nodes_per_job: 16             # worked-example job: 16 HX8 nodes = 128 GPUs
min_bw_fraction: 0.2          # samples are clipped at 20 % of the class mean
""")
    print(f"wrote {len(HOSTS)} hosts and path_model.yaml to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
