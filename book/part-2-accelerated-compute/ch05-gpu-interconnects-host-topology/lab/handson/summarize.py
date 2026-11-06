#!/usr/bin/env python3
"""Turn the raw outputs of one Chapter 5 hands-on run into summary.json and report.md.

    python summarize.py results/<run-id>

Only parses what run.sh captured; it never edits the raw files.
"""
from __future__ import annotations

import csv
import io
import json
import re
import statistics
import sys
from pathlib import Path

GTS = {1: 2.5, 2: 5.0, 3: 8.0, 4: 16.0, 5: 32.0, 6: 64.0}
ENC = {1: 8 / 10, 2: 8 / 10, 3: 128 / 130, 4: 128 / 130, 5: 128 / 130, 6: 242 / 256}   # Gen6: FLIT mode, approximate


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""


def link_rate_gb_s(gen: int, width: int) -> float:
    """Per-direction rate after line encoding (Section 3.6 / Table 5.1): GT/s x lanes x encoding / 8."""
    return round(GTS[gen] * width * ENC[gen] / 8, 2)


def smi_csv(text: str) -> list[dict]:
    rows = [r for r in csv.reader(io.StringIO(text)) if r]
    if not rows:
        return []
    head = [h.strip().split(" [")[0] for h in rows[0]]
    return [dict(zip(head, (c.strip() for c in r))) for r in rows[1:] if len(r) == len(head)]


def num(v):
    try:
        return float(str(v).split()[0])
    except (ValueError, IndexError):
        return None


def step1(d: Path) -> dict:
    s = d / "step1-discovery"
    gpus = [ln for ln in read(s / "nvidia-smi-L.txt").splitlines() if ln.startswith("GPU ")]
    pci = smi_csv(read(s / "gpu-pci.csv"))
    lspci = read(s / "lspci-D-nn.txt")
    topo = re.sub(r"\x1b\[[0-9;]*m", "", read(s / "topo-m.txt"))   # nvidia-smi underlines the header
    topo_head = next((ln for ln in topo.splitlines() if "GPU0" in ln), "")
    sysfs = read(s / "sysfs-pci.txt").splitlines()
    ib = [x for x in read(s / "infiniband.txt").split() if x and "cannot access" not in x and x != "ls:"]
    nodes = [x for x in read(s / "numa-nodes.txt").split() if x.startswith("node")]
    lookup = read(s / "gpu-sysfs-lookup.txt")
    q = read(s / "nvidia-smi-q.txt")
    return {
        "gpu_count": len(gpus), "gpu_bus_id": pci[0].get("pci.bus_id") if pci else None,
        "lspci_functions": len([ln for ln in lspci.splitlines() if re.match(r"^[0-9a-f]{4}:", ln)]),
        "lspci_nvidia_functions": len(re.findall(r"\[10de:[0-9a-f]{4}\]", lspci)),
        "lspci_gpu_class_functions": len(re.findall(r"\[030[02]\]", lspci)),
        "lspci_vendors": sorted(set(re.findall(r"\[([0-9a-f]{4}):[0-9a-f]{4}\]", lspci))),
        "lspci_tree_has_bridges": bool(re.search(r"\+-|\\-", read(s / "lspci-tv.txt"))),
        "lspci_vvv_lnkcap_lines": read(s / "lspci-vvv.txt").count("LnkCap:"),
        "gpu_bdf_in_sysfs": "No such file" not in lookup and bool(lookup.strip()),
        "sysfs_pci_functions": len(sysfs), "sysfs_functions_with_link_files": sum(1 for ln in sysfs if "cur_width=none" not in ln),
        "numa_nodes": len(nodes),
        "topo_m_columns": topo_head.split(),
        "topo_m_nic_columns": len(re.findall(r"\bNIC\d+\b", topo_head)),
        "rdma_devices": ib, "rdma_devices_pci_backed": 0 if not ib else None,
        "net_devices": read(s / "net-devices.txt").splitlines(),
        "lstopo_pci_objects": len(re.findall(r"^\s*PCI ", read(s / "lstopo.txt"), re.M)),
        "lstopo_gpu_osdev": bool(re.search(r'(CoProc|GPU) .*"(cuda|nvml|opencl)', read(s / "lstopo.txt"), re.I)),
        "smi_q_host_max_gen": num(re.search(r"Host Max\s*:\s*(\S+)", q).group(1)) if re.search(r"Host Max\s*:\s*(\S+)", q) else None,
    }


def link_stats(rows: list[dict]) -> dict:
    def col(k):
        return [num(r.get(k)) for r in rows if num(r.get(k)) is not None]
    out = {"samples": len(rows)}
    for k in ("pcie.link.gen.current", "pcie.link.gen.gpucurrent", "pcie.link.width.current", "utilization.gpu"):
        v = col(k)
        out[k] = {"min": min(v), "max": max(v)} if v else None
    for k in ("pcie.link.gen.max", "pcie.link.gen.gpumax", "pcie.link.gen.hostmax", "pcie.link.width.max"):
        v = col(k)
        out[k] = max(v) if v else None
    return out


def step2(d: Path) -> dict:
    rows = smi_csv(read(d / "step2-link-idle" / "link-idle.csv"))
    st = link_stats(rows)
    gen_max = int(st.get("pcie.link.gen.gpumax") or st["pcie.link.gen.max"])
    w_max = int(st["pcie.link.width.max"])
    st["theoretical_gb_s_per_direction"] = link_rate_gb_s(gen_max, w_max)
    st["link_label"] = f"Gen{gen_max} x{w_max}"
    host_max = st.get("pcie.link.gen.hostmax")
    st["host_side_label"] = f"Gen{int(host_max)}" if host_max else None
    return st


def step3(d: Path, theo: float) -> dict:
    sw = json.loads(read(d / "step3-bandwidth" / "sweep.json"))
    rows = sw["rows"]
    for r in rows:
        r["pct_of_link"] = round(100 * r["gb_per_s"] / theo, 1)
    big = {f"{r['direction']}_{r['memory']}": r for r in rows if r["mib"] == 256}
    bi = json.loads(read(d / "step3-bandwidth" / "bidir.json"))
    best = {k: max(r["gb_per_s"] for r in rows if f"{r['direction']}_{r['memory']}" == k) for k in big}
    small = {f"{r['direction']}_{r['memory']}": r["gb_per_s"] for r in rows if r["mib"] == 0.0625}
    return {"rows": rows, "at_256mib_gb_s": {k: v["gb_per_s"] for k, v in big.items()},
            "at_256mib_pct_of_link": {k: v["pct_of_link"] for k, v in big.items()},
            "best_gb_s": best, "at_64kib_gb_s": small,
            "bidir": {k: bi[k] for k in ("h2d_alone_gb_per_s", "d2h_alone_gb_per_s", "concurrent_aggregate_gb_per_s", "aggregate_over_best_unidirectional")}}


def step4(d: Path) -> dict:
    s = d / "step4-under-load"
    st = link_stats(smi_csv(read(s / "link-load.csv")))
    dm = [ln.split() for ln in read(s / "dmon-pcie.txt").splitlines() if ln.strip() and not ln.startswith("#")]
    rx = [float(x[1]) for x in dm if len(x) >= 3 and x[1].replace(".", "").isdigit()]
    tx = [float(x[2]) for x in dm if len(x) >= 3 and x[2].replace(".", "").isdigit()]
    hold = json.loads(read(s / "hold.json"))
    ct = json.loads(read(s / "contend.json"))
    return {"link_under_load": st, "dmon_rxpci_mb_s_max": max(rx) if rx else None, "dmon_txpci_mb_s_max": max(tx) if tx else None,
            "dmon_samples": len(rx), "hold_gb_s_each_way": round(hold["bytes_each_way"] / hold["seconds"] / 1e9, 2),
            "copy_alone_gb_s": ct["alone_gb_per_s"], "copy_under_gemm_gb_s": ct["under_gemm_gb_per_s"],
            "copy_under_gemm_ratio": ct["ratio_under_over_alone"]}


def step5(d: Path) -> dict:
    a = json.loads(read(d / "step5-affinity" / "cpu-first.json"))
    b = json.loads(read(d / "step5-affinity" / "cpu-last.json"))
    return {"first": {"cpus": a["cpu_affinity"], "pinned": a["h2d_pinned_gb_per_s"], "pageable": a["h2d_pageable_gb_per_s"]},
            "last": {"cpus": b["cpu_affinity"], "pinned": b["h2d_pinned_gb_per_s"], "pageable": b["h2d_pageable_gb_per_s"]},
            "pinned_ratio_last_over_first": round(b["h2d_pinned_gb_per_s"] / a["h2d_pinned_gb_per_s"], 3)}


def rng(x: dict | None) -> str:
    if not x:
        return "n/a"
    lo, hi = int(x["min"]), int(x["max"])
    return str(lo) if lo == hi else f"{lo}–{hi}"


def report(sm: dict) -> str:
    e, s1, s2, s3, s4, s5 = (sm[k] for k in ("environment", "step1", "step2", "step3", "step4", "step5"))
    M = "`[MEASURED]`"
    theo = s2["theoretical_gb_s_per_direction"]
    L = [f"# Chapter 5 hands-on: host topology from the inside on `{e.get('gpu')}`", "",
         f"Run captured {e.get('captured_at')}, kernel `{e.get('kernel')}`. Numbers are {M} by the step named, except the "
         f"link rate, which is `[MODELED]` from the PCIe encoding. Raw outputs are in the step directories.", "",
         "## Step 1: what this host shows and hides", "",
         "| Question | Native multi-GPU server | This host |", "|---|---|---|",
         f"| GPUs | 8 on ORION HX8 | {s1['gpu_count']} {M} |",
         f"| GPU in `lspci` (vendor 10de) | yes, with its BDF | {s1['lspci_nvidia_functions']} NVIDIA functions; "
         f"{s1['lspci_functions']} functions in all, vendors {', '.join(s1['lspci_vendors'])} {M} |",
         f"| PCIe tree (`lspci -tv`) | root ports, switches, endpoints | {'bridges present' if s1['lspci_tree_has_bridges'] else 'flat: no bridges or switches'} {M} |",
         f"| `LnkCap`/`LnkSta` (`lspci -vvv`) | per device | {s1['lspci_vvv_lnkcap_lines']} LnkCap lines {M} |",
         f"| GPU's BDF `{s1['gpu_bus_id']}` in sysfs | yes | {'yes' if s1['gpu_bdf_in_sysfs'] else 'no'} {M} |",
         f"| NUMA nodes | 2 | {s1['numa_nodes']} {M} |",
         f"| NIC columns in `nvidia-smi topo -m` | NIC0..NIC9 | {s1['topo_m_nic_columns']} {M} |",
         f"| RDMA devices | mlx5_0..9 on PCIe | {', '.join(s1['rdma_devices']) or 'none'} {M} |", "",
         "## Step 2: the link nvidia-smi reports", "",
         f"- GPU link capability {s2['link_label']}, host side up to {s2['host_side_label']} {M}; per-direction rate "
         f"{theo} GB/s `[MODELED]` (GT/s × lanes × 128/130 ÷ 8).",
         f"- At idle: generation {rng(s2['pcie.link.gen.current'])}, width x{rng(s2['pcie.link.width.current'])} over {s2['samples']} samples {M}.", "",
         "## Step 3: copy bandwidth against the link", "",
         "| Size | H2D pageable | H2D pinned | D2H pageable | D2H pinned |", "|---|---|---|---|---|"]
    by = {}
    for r in s3["rows"]:
        by.setdefault(r["mib"], {})[f"{r['direction']}_{r['memory']}"] = r
    for mib, x in sorted(by.items()):
        size = f"{int(mib * 1024)} KiB" if mib < 1 else f"{int(mib)} MiB"
        cell = lambda k: f"{x[k]['gb_per_s']:.2f} GB/s ({x[k]['pct_of_link']:.0f} %)"
        L.append(f"| {size} | {cell('h2d_pageable')} | {cell('h2d_pinned')} | {cell('d2h_pageable')} | {cell('d2h_pinned')} |")
    b = s3["bidir"]
    L += ["", f"All cells {M}; percentages are of the {theo} GB/s per-direction link rate.", "",
          f"- Both directions at once (256 MiB each, pinned): {b['concurrent_aggregate_gb_per_s']} GB/s aggregate versus "
          f"{b['h2d_alone_gb_per_s']} (H2D) and {b['d2h_alone_gb_per_s']} (D2H) alone: {b['aggregate_over_best_unidirectional']}× {M}.",
          "", "## Step 4: under load", "",
          f"- Link during sustained copies: generation {rng(s4['link_under_load']['pcie.link.gen.current'])}, width "
          f"x{rng(s4['link_under_load']['pcie.link.width.current'])} {M}; `nvidia-smi dmon -s t` peak rxpci {s4['dmon_rxpci_mb_s_max']} MB/s, "
          f"txpci {s4['dmon_txpci_mb_s_max']} MB/s {M}; the copy loop moved {s4['hold_gb_s_each_way']} GB/s each way {M}.",
          f"- Pinned H2D alone {s4['copy_alone_gb_s']} GB/s; while a GEMM loop runs on another stream {s4['copy_under_gemm_gb_s']} GB/s "
          f"(ratio {s4['copy_under_gemm_ratio']}) {M}.", "", "## Step 5: CPU placement of the copying process", "",
          f"- CPUs {s5['first']['cpus']} (node 0): pinned {s5['first']['pinned']}, pageable {s5['first']['pageable']} GB/s; "
          f"CPUs {s5['last']['cpus']}: pinned {s5['last']['pinned']}, pageable {s5['last']['pageable']} GB/s {M}.", ""]
    return "\n".join(L) + "\n"


def main() -> int:
    d = Path(sys.argv[1])
    env = json.loads(read(d / "environment.json"))
    s2 = step2(d)
    sm = {"lab": "ch05-host-topology", "run": d.name, "environment": env, "step1": step1(d), "step2": s2,
          "step3": step3(d, s2["theoretical_gb_s_per_direction"]), "step4": step4(d), "step5": step5(d)}
    (d / "summary.json").write_text(json.dumps(sm, indent=1) + "\n", encoding="utf-8")
    (d / "report.md").write_text(report(sm), encoding="utf-8")
    print(f"wrote {d / 'summary.json'} and {d / 'report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
