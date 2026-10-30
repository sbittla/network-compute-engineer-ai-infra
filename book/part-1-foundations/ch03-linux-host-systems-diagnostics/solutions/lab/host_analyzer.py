#!/usr/bin/env python3
"""Fleet host-snapshot analyzer (Chapter 3, Progressive Lab 1) — REFERENCE SOLUTION.

Reads ``hostdiag/1`` snapshots (produced by host_collector.py, or the synthetic ORION
snapshots in lab/data/snapshots/), parses the raw tool output, compares it with the HX8
baseline, and emits findings with a severity (critical | warning | info) and the evidence
that supports each one.

Usage:
    python host_analyzer.py ../../lab/data/snapshots/*.json \
        --baseline ../../lab/data/orion_hx8_baseline.yaml --out fleet_report.md
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

SEVERITY_ORDER = {"critical": 0, "warning": 1, "info": 2}


@dataclass(frozen=True)
class Finding:
    """One diagnostic finding. ``subject`` names the device/interface/CPU concerned."""
    host: str
    check_id: str
    severity: str          # critical | warning | info
    subject: str
    evidence: str

    def key(self) -> str:
        return f"{self.host}|{self.check_id}|{self.severity}"


# --------------------------------------------------------------------------- helpers (given)
def load_snapshot(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_baseline(path: Path) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def parse_cpu_list(text: str) -> list[int]:
    """Parse kernel CPU-list syntax ("0-55,112-167") or space-separated lists ("0 1 2")."""
    cpus: list[int] = []
    for part in re.split(r"[,\s]+", text.strip()):
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            cpus.extend(range(int(a), int(b) + 1))
        else:
            cpus.append(int(part))
    return sorted(set(cpus))


def normalize_bdf(bdf: str) -> str:
    """'18:00.0' / '00000000:18:00.0' / '0000:18:00' -> '0000:18:00.0' (lower case)."""
    b = bdf.strip().lower()
    parts = b.split(":")
    if len(parts) == 2:                      # bus:dev.fn
        b = "0000:" + b
    elif len(parts) == 3 and len(parts[0]) > 4:
        b = parts[0][-4:] + ":" + parts[1] + ":" + parts[2]
    if "." not in b.split(":")[-1]:
        b += ".0"
    return b


def _num(tok: str) -> float | None:
    try:
        return float(tok)
    except ValueError:
        return None


# --------------------------------------------------------------------------- parsers
def parse_lscpu(text: str) -> dict:
    """Parse `lscpu` into a dict.

    Returns keys: cpus, sockets, cores_per_socket, threads_per_core, numa_nodes (ints),
    model_name (str), numa_cpus ({node_id: [cpu, ...]}).
    """
    kv: dict[str, str] = {}
    for line in text.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            kv[k.strip()] = v.strip()
    numa_cpus = {}
    for k, v in kv.items():
        m = re.fullmatch(r"NUMA node(\d+) CPU\(s\)", k)
        if m:
            numa_cpus[int(m.group(1))] = parse_cpu_list(v)
    return {"cpus": int(kv.get("CPU(s)", 0)), "sockets": int(kv.get("Socket(s)", 0)),
            "cores_per_socket": int(kv.get("Core(s) per socket", 0)),
            "threads_per_core": int(kv.get("Thread(s) per core", 0)),
            "numa_nodes": int(kv.get("NUMA node(s)", 0)), "model_name": kv.get("Model name", ""),
            "numa_cpus": numa_cpus}


def parse_numactl_hardware(text: str) -> dict:
    """Parse `numactl --hardware`.

    Returns {"nodes": {id: {"cpus": [...], "size_mb": int, "free_mb": int}},
             "distances": [[int, ...], ...]} (distance matrix rows in node order).
    """
    nodes: dict[int, dict] = {}
    distances: list[list[int]] = []
    in_dist = False
    for line in text.splitlines():
        m = re.match(r"node (\d+) (cpus|size|free):\s*(.*)$", line)
        if m:
            n, key, val = int(m.group(1)), m.group(2), m.group(3)
            node = nodes.setdefault(n, {"cpus": [], "size_mb": 0, "free_mb": 0})
            if key == "cpus":
                node["cpus"] = parse_cpu_list(val) if val.strip() else []
            else:
                node[f"{key}_mb"] = int(val.split()[0])
            continue
        if line.startswith("node distances"):
            in_dist = True
            continue
        if in_dist:
            m = re.match(r"\s*(\d+):\s+(.*)$", line)
            if m:
                distances.append([int(x) for x in m.group(2).split()])
    return {"nodes": nodes, "distances": distances}


def parse_free(text: str) -> dict:
    """Parse `free -m` (MiB). Returns mem_total_mib, mem_available_mib, swap_total_mib, swap_used_mib."""
    out = {"mem_total_mib": 0, "mem_available_mib": 0, "swap_total_mib": 0, "swap_used_mib": 0}
    for line in text.splitlines():
        t = line.split()
        if t and t[0] == "Mem:":
            out["mem_total_mib"] = int(t[1])
            out["mem_available_mib"] = int(t[6]) if len(t) > 6 else int(t[3])
        elif t and t[0] == "Swap:":
            out["swap_total_mib"], out["swap_used_mib"] = int(t[1]), int(t[2])
    return out


_DEVICE_HDR = re.compile(r"^((?:[0-9a-fA-F]{4}:)?[0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-7])\s+(.*)$")


def _kind_from_desc(desc: str) -> str:
    d = desc.lower()
    if d.startswith("3d controller") or ("nvidia" in d and "vga" not in d):
        return "gpu"
    if d.startswith(("ethernet controller", "infiniband controller", "network controller")):
        return "nic"
    if d.startswith("non-volatile memory"):
        return "nvme"
    if d.startswith("vga"):
        return "vga"
    return "other"


def _kind_from_class(cls: str) -> str:
    c = cls.lower()
    if c.startswith("0x0302"):
        return "gpu"
    if c.startswith(("0x0200", "0x0207", "0x0280")):
        return "nic"
    if c.startswith("0x0108"):
        return "nvme"
    if c.startswith("0x0300"):
        return "vga"
    return "other"


def parse_lspci_links(text: str) -> list[dict]:
    """Parse `lspci -vv` into one dict per device.

    Each dict: bdf (normalized '0000:bb:dd.f'), description, kind (gpu|nic|nvme|vga|other),
    numa_node (int|None), cap_speed_gts, cap_width, sta_speed_gts, sta_width (float/int or None
    when the capability is not visible), access_denied (bool: non-root lspci hides capabilities).
    Parentheses annotations such as "(ok)" / "(downgraded)" are ignored — compare numbers.
    """
    devices: list[dict] = []
    cur: dict | None = None
    for line in text.splitlines():
        m = _DEVICE_HDR.match(line)
        if m and not line.startswith(("\t", " ")):
            cur = {"bdf": normalize_bdf(m.group(1)), "description": m.group(2), "kind": _kind_from_desc(m.group(2)),
                   "numa_node": None, "cap_speed_gts": None, "cap_width": None, "sta_speed_gts": None,
                   "sta_width": None, "access_denied": False}
            devices.append(cur)
            continue
        if cur is None:
            continue
        s = line.strip()
        if s.startswith("NUMA node:"):
            cur["numa_node"] = int(s.split(":", 1)[1])
        elif "<access denied>" in s:
            cur["access_denied"] = True
        elif s.startswith(("LnkCap:", "LnkSta:")):
            sp = re.search(r"Speed ([\d.]+)GT/s", s)
            wd = re.search(r"Width x(\d+)", s)
            pre = "cap" if s.startswith("LnkCap:") else "sta"
            cur[f"{pre}_speed_gts"] = float(sp.group(1)) if sp else None
            cur[f"{pre}_width"] = int(wd.group(1)) if wd else None
    return devices


def parse_pcie_sysfs(text: str) -> list[dict]:
    """Parse the collector's sysfs PCIe summary (';'-separated key=value per device) into the
    same dict shape as :func:`parse_lspci_links` (description is '' and kind comes from class), plus
    the since-boot AER totals aer_cor_total / aer_nonfatal_total / aer_fatal_total (int or None)."""
    out = []
    for line in text.splitlines():
        if not line.strip():
            continue
        fields = line.split(";")
        kv = dict(f.split("=", 1) for f in fields[1:] if "=" in f)

        def spd(v: str | None) -> float | None:
            m = re.match(r"\s*([\d.]+)\s*GT/s", v or "")
            return float(m.group(1)) if m else None

        def wid(v: str | None) -> int | None:
            return int(v) if v and v.strip().isdigit() else None

        numa = kv.get("numa_node", "")
        out.append({"bdf": normalize_bdf(fields[0]), "description": "", "kind": _kind_from_class(kv.get("class", "")),
                    "numa_node": int(numa) if numa.lstrip("-").isdigit() and int(numa) >= 0 else None,
                    "cap_speed_gts": spd(kv.get("max_link_speed")), "cap_width": wid(kv.get("max_link_width")),
                    "sta_speed_gts": spd(kv.get("current_link_speed")), "sta_width": wid(kv.get("current_link_width")),
                    "access_denied": False, "aer_cor_total": wid(kv.get("aer_cor_total")),
                    "aer_nonfatal_total": wid(kv.get("aer_nonfatal_total")),
                    "aer_fatal_total": wid(kv.get("aer_fatal_total"))})
    return out


def parse_vmstat(text: str) -> dict:
    """Parse `vmstat <interval> <count>` and average the LIVE samples.

    The first data row reports averages since boot, so it is excluded. Columns are located
    by header name (works with or without the newer 'gu' column). Returns {"samples": n,
    <column>: mean, ...} for every header column (r, b, si, so, bi, bo, in, cs, us, sy, id, wa, st...).
    """
    header: list[str] | None = None
    rows: list[list[float]] = []
    for line in text.splitlines():
        t = line.split()
        if not t:
            continue
        if t[0] == "r" and "b" in t:
            header = t
            continue
        if header and all(_num(x) is not None for x in t) and len(t) == len(header):
            rows.append([float(x) for x in t])
    live = rows[1:] if len(rows) > 1 else rows
    out: dict = {"samples": len(live)}
    if header and live:
        for i, col in enumerate(header):
            out[col] = sum(r[i] for r in live) / len(live)
    return out


def parse_iostat(text: str) -> dict:
    """Parse `iostat -x <interval> <count>` and keep the LAST report (the first is since boot).

    Returns {"avg_cpu": {"%user": .., "%iowait": .., "%idle": .., ...},
             "devices": {name: {column: value}}}.
    """
    reports: list[dict] = []
    cur: dict | None = None
    mode = None
    cpu_hdr: list[str] = []
    dev_hdr: list[str] = []
    for line in text.splitlines():
        t = line.split()
        if not t:
            mode = None if mode == "dev" else mode
            continue
        if t[0] == "avg-cpu:":
            cur = {"avg_cpu": {}, "devices": {}}
            reports.append(cur)
            cpu_hdr = t[1:]
            mode = "cpu"
            continue
        if t[0] in ("Device", "Device:"):
            dev_hdr = t[1:]
            mode = "dev"
            if cur is None:
                cur = {"avg_cpu": {}, "devices": {}}
                reports.append(cur)
            continue
        if mode == "cpu" and cur is not None and all(_num(x) is not None for x in t):
            cur["avg_cpu"] = dict(zip(cpu_hdr, (float(x) for x in t)))
            mode = None
        elif mode == "dev" and cur is not None and len(t) == len(dev_hdr) + 1:
            cur["devices"][t[0]] = {c: float(v) for c, v in zip(dev_hdr, t[1:])}
    return reports[-1] if reports else {"avg_cpu": {}, "devices": {}}


def parse_mpstat(text: str) -> dict:
    """Parse `mpstat -P ALL <interval> <count>`; prefer the 'Average:' block, else the last block.

    Returns {"all": {"%usr": .., "%idle": .., ...}, "cpus": {cpu_id: {...}}}. Columns are found
    by header name and values are aligned from the right (robust to 12h 'AM/PM' timestamps).
    """
    blocks: list[dict] = []
    cur: dict | None = None
    cols: list[str] = []
    for line in text.splitlines():
        t = line.split()
        if "CPU" in t and any(c.startswith("%") for c in t):
            cols = t[t.index("CPU") + 1:]
            cur = {"all": {}, "cpus": {}, "average": t[0].startswith("Average")}
            blocks.append(cur)
            continue
        if cur is None or len(t) < len(cols) + 1:
            continue
        vals = t[-len(cols):]
        if any(_num(v) is None for v in vals):
            continue
        cpu = t[-len(cols) - 1]
        rec = {c: float(v) for c, v in zip(cols, vals)}
        if cpu == "all":
            cur["all"] = rec
        elif cpu.isdigit():
            cur["cpus"][int(cpu)] = rec
    if not blocks:
        return {"all": {}, "cpus": {}}
    avg = [b for b in blocks if b["average"]]
    b = avg[-1] if avg else blocks[-1]
    return {"all": b["all"], "cpus": b["cpus"]}


def parse_interrupts(text: str) -> list[dict]:
    """Parse /proc/interrupts.

    Returns one dict per numbered IRQ line: {"irq": "180", "counts": [int per CPU],
    "name": last token (e.g. 'mlx5_comp0@pci:0000:19:00.0'), "bdf": normalized BDF or None}.
    Non-numeric rows (NMI, LOC, ...) are ignored.
    """
    lines = text.splitlines()
    if not lines:
        return []
    ncpu = len(lines[0].split())
    out = []
    for line in lines[1:]:
        m = re.match(r"\s*(\d+):\s*(.*)$", line)
        if not m:
            continue
        toks = m.group(2).split()
        counts = []
        for tok in toks[:ncpu]:
            if tok.isdigit():
                counts.append(int(tok))
            else:
                break
        rest = toks[len(counts):]
        name = rest[-1] if rest else ""
        bm = re.search(r"([0-9a-fA-F]{4}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-7])", " ".join(rest))
        out.append({"irq": m.group(1), "counts": counts + [0] * (ncpu - len(counts)), "name": name,
                    "bdf": normalize_bdf(bm.group(1)) if bm else None})
    return out


def parse_ip_link(text: str) -> dict:
    """Parse `ip link show` -> {iface: {"mtu": int, "state": str, "flags": [str]}}."""
    out = {}
    for line in text.splitlines():
        m = re.match(r"^\d+:\s+([^:@\s]+)(?:@\S+)?:\s+<([^>]*)>\s+mtu\s+(\d+).*?\bstate\s+(\S+)", line)
        if m:
            out[m.group(1)] = {"mtu": int(m.group(3)), "state": m.group(4), "flags": m.group(2).split(",")}
    return out


def parse_ethtool(text: str) -> dict:
    """Parse `ethtool <iface>` -> {"speed_mbps": int|None, "duplex": str|None, "link_detected": bool|None}."""
    out: dict = {"speed_mbps": None, "duplex": None, "link_detected": None}
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("Speed:"):
            m = re.search(r"(\d+)\s*Mb/s", s)
            out["speed_mbps"] = int(m.group(1)) if m else None
        elif s.startswith("Duplex:"):
            out["duplex"] = s.split(":", 1)[1].strip()
        elif s.startswith("Link detected:"):
            out["link_detected"] = s.split(":", 1)[1].strip() == "yes"
    return out


def parse_numastat_process(text: str) -> dict:
    """Parse `numastat -p <pid>` -> {node_id: total_MB} from the 'Total' row."""
    nodes: list[int] = []
    for line in text.splitlines():
        if "Node" in line and "Total" in line:
            nodes = [int(x) for x in re.findall(r"Node (\d+)", line)]
        elif line.startswith("Total") and nodes:
            vals = [float(x) for x in line.split()[1:]]
            return {n: vals[i] for i, n in enumerate(nodes)}
    return {}


def parse_taskset(text: str) -> list[int]:
    """Parse `taskset -cp <pid>` ("pid N's current affinity list: 0-55,112-167") -> CPU list."""
    m = re.search(r"affinity list:\s*(.+)$", text.strip(), re.M)
    return parse_cpu_list(m.group(1)) if m else []


def parse_nvidia_smi_csv(text: str) -> list[dict]:
    """Parse the collector's `nvidia-smi --query-gpu=... --format=csv` output.

    Returns dicts with index, bdf (normalized), gen_cur, gen_max, width_cur, width_max, util_pct.
    """
    out = []
    lines = [l for l in text.splitlines() if l.strip()]
    for line in lines[1:]:
        t = [x.strip() for x in line.split(",")]
        if len(t) < 7:
            continue
        out.append({"index": int(t[0]), "bdf": normalize_bdf(t[1]), "gen_cur": int(t[2]), "gen_max": int(t[3]),
                    "width_cur": int(t[4]), "width_max": int(t[5]), "util_pct": int(t[6].split()[0])})
    return out


def parse_cpufreq(text: str) -> dict:
    """Parse the collector's cpufreq summary -> {"drivers": {name: n}, "governors": {name: n}, "cur_khz": {...}}."""
    out: dict = {"drivers": {}, "governors": {}, "cur_khz": {}}
    for line in text.splitlines():
        m = re.match(r"scaling_(driver|governor):\s*(\S+)\s*\((\d+) cpus\)", line)
        if m:
            out["drivers" if m.group(1) == "driver" else "governors"][m.group(2)] = int(m.group(3))
        elif line.startswith("scaling_cur_freq_khz:"):
            out["cur_khz"] = {k: int(v) for k, v in re.findall(r"(\w+)=(\d+)", line)}
    return out


_AER_RX = re.compile(r"AER: (Corrected|Uncorrected \((?:Non-Fatal|Fatal)\)) error received: ([0-9a-fA-F:.]+)")
_EDAC = re.compile(r"EDAC MC(\d+): (\d+) (CE|UE)")
_XID = re.compile(r"NVRM: Xid \(PCI:([0-9a-fA-F:]+)\): (\d+)")
_LINK_DOWN = re.compile(r"(?:mlx5_core|ice|bnxt_en|i40e)\s+([0-9a-fA-F:.]+)\s+(\S+): Link down")


def scan_kernel_log(text: str) -> list[dict]:
    """Extract hardware-health events from dmesg/journalctl -k text.

    Returns events {"kind": aer_corrected|aer_uncorrected|edac_ce|edac_ue|xid|mce|link_down,
    "device": BDF/MC/interface, "count": int, "xid": int (xid only), "line": raw line}.
    One AER *event* is counted per "error received" line (detail lines are not double-counted).
    """
    ev = []
    for line in text.splitlines():
        m = _AER_RX.search(line)
        if m:
            kind = "aer_corrected" if m.group(1) == "Corrected" else "aer_uncorrected"
            ev.append({"kind": kind, "device": normalize_bdf(m.group(2)), "count": 1, "line": line})
            continue
        m = _EDAC.search(line)
        if m:
            ev.append({"kind": "edac_ce" if m.group(3) == "CE" else "edac_ue", "device": f"MC{m.group(1)}",
                       "count": int(m.group(2)), "line": line})
            continue
        m = _XID.search(line)
        if m:
            ev.append({"kind": "xid", "device": normalize_bdf(m.group(1)), "count": 1, "xid": int(m.group(2)),
                       "line": line})
            continue
        if "mce: [Hardware Error]" in line:
            ev.append({"kind": "mce", "device": "cpu", "count": 1, "line": line})
            continue
        m = _LINK_DOWN.search(line)
        if m:
            ev.append({"kind": "link_down", "device": m.group(2), "count": 1, "line": line})
    return ev


# --------------------------------------------------------------------------- analysis
def _sec(snapshot: dict, name: str) -> str | None:
    s = snapshot.get("sections", {}).get(name)
    return s["stdout"] if s and s.get("status") == "ok" else None


def analyze_host(snapshot: dict, baseline: dict) -> list[Finding]:
    """Apply every rule in the lab README's severity policy to one snapshot.

    Must never raise because a section is missing, denied, skipped or empty: instead emit an
    EVIDENCE_GAP info finding for each section whose status is not "ok".
    """
    host = snapshot.get("host", "?")
    th = baseline["thresholds"]
    inv = baseline["inventory"]
    F: list[Finding] = []

    def add(check: str, sev: str, subject: str, evidence: str) -> None:
        F.append(Finding(host, check, sev, subject, evidence))

    for name, s in snapshot.get("sections", {}).items():
        if s.get("status") != "ok":
            add("EVIDENCE_GAP", "info", name,
                f"{' '.join(s.get('argv', []))}: {s.get('status')} - "
                + " | ".join((s.get('stderr') or '').strip().splitlines())[:160])

    # --- inventory
    numa_cpus: dict[int, list[int]] = {}
    t = _sec(snapshot, "lscpu")
    if t:
        c = parse_lscpu(t)
        numa_cpus = c["numa_cpus"]
        for key in ("sockets", "cores_per_socket", "threads_per_core", "numa_nodes"):
            if c[key] != inv[key]:
                add("INVENTORY_MISMATCH", "critical", key, f"lscpu {key}={c[key]}, baseline {inv[key]}")
    t = _sec(snapshot, "free")
    if t:
        fr = parse_free(t)
        if fr["mem_total_mib"] < inv["mem_total_mib_min"]:
            add("INVENTORY_MISMATCH", "critical", "memory",
                f"free -m total {fr['mem_total_mib']} MiB < baseline minimum {inv['mem_total_mib_min']} MiB")
    t = _sec(snapshot, "numactl_hardware")
    if t:
        nh = parse_numactl_hardware(t)
        for n, node in nh["nodes"].items():
            numa_cpus.setdefault(n, node["cpus"])
            if node["size_mb"] < inv["numa_node_mem_mb_min"]:
                add("INVENTORY_MISMATCH", "critical", f"numa{n}",
                    f"numactl node {n} size {node['size_mb']} MB < {inv['numa_node_mem_mb_min']} MB (DIMM mapped out?)")

    # --- GPU idle state (PCIe speed downshift at idle is normal power management)
    gpus = parse_nvidia_smi_csv(_sec(snapshot, "nvidia_smi") or "")
    gpu_idle = bool(gpus) and max(g["util_pct"] for g in gpus) <= th["gpu_idle_util_pct"]

    # --- PCIe link state: lspci when capabilities are visible, otherwise sysfs
    devs = parse_lspci_links(_sec(snapshot, "lspci") or "")
    src = "lspci -vv"
    if not devs or all(d["sta_width"] is None for d in devs if d["kind"] in ("gpu", "nic", "nvme")):
        devs, src = parse_pcie_sysfs(_sec(snapshot, "pcie_sysfs") or ""), "sysfs"
    gpu_devs = [d for d in devs if d["kind"] == "gpu"]
    count = len(gpus) if gpus else len(gpu_devs)
    if (gpus or gpu_devs) and count != inv["gpu_count"]:
        add("INVENTORY_MISMATCH", "critical", "gpu_count", f"{count} GPUs visible, baseline {inv['gpu_count']}")
    for d in devs:
        if None in (d["cap_width"], d["sta_width"], d["cap_speed_gts"], d["sta_speed_gts"]):
            continue
        ev = (f"{src}: {d['bdf']} {d['kind']} LnkCap {d['cap_speed_gts']:g}GT/s x{d['cap_width']}, "
              f"LnkSta {d['sta_speed_gts']:g}GT/s x{d['sta_width']}")
        if d["sta_width"] < d["cap_width"]:
            add("PCIE_WIDTH_DEGRADED", "critical", d["bdf"], ev)
        if d["sta_speed_gts"] < d["cap_speed_gts"]:
            if d["kind"] == "gpu" and gpu_idle:
                add("PCIE_SPEED_LOW_IDLE", "info", d["bdf"], ev + " (GPUs idle: re-check under load)")
            else:
                add("PCIE_SPEED_DEGRADED", "warning", d["bdf"], ev)
    dev_numa = {d["bdf"]: d["numa_node"] for d in devs}

    # --- AER from sysfs counters (since boot) when the kernel log is unavailable
    if not _sec(snapshot, "kernel_log"):
        for d in parse_pcie_sysfs(_sec(snapshot, "pcie_sysfs") or ""):
            unc = (d.get("aer_nonfatal_total") or 0) + (d.get("aer_fatal_total") or 0)
            if unc:
                add("PCIE_AER_UNCORRECTED", "critical", d["bdf"], f"sysfs aer_dev_nonfatal/fatal totals = {unc} since boot")
            n = d.get("aer_cor_total") or 0
            if n:
                sev = "warning" if n >= th["aer_corrected_warn_per_bdf"] else "info"
                add("PCIE_AER_CORRECTED", sev, d["bdf"], f"sysfs aer_dev_correctable TOTAL_ERR_COR = {n} since boot")

    # --- kernel log
    t = _sec(snapshot, "kernel_log")
    if t:
        events = scan_kernel_log(t)
        aer: dict[str, int] = {}
        for e in events:
            if e["kind"] == "aer_corrected":
                aer[e["device"]] = aer.get(e["device"], 0) + 1
            elif e["kind"] == "aer_uncorrected":
                add("PCIE_AER_UNCORRECTED", "critical", e["device"], e["line"].strip())
            elif e["kind"] == "edac_ue":
                add("MEM_ECC_UNCORRECTED", "critical", e["device"], e["line"].strip())
            elif e["kind"] == "xid":
                sev = "critical" if e["xid"] in th["critical_xids"] else "warning"
                add("GPU_XID", sev, e["device"], f"Xid {e['xid']}: {e['line'].strip()[:160]}")
            elif e["kind"] == "mce":
                add("MCE_LOGGED", "warning", "cpu", e["line"].strip())
            elif e["kind"] == "link_down":
                add("NIC_LINK_FLAP", "warning", e["device"], e["line"].strip())
        for bdf, n in aer.items():
            sev = "warning" if n >= th["aer_corrected_warn_per_bdf"] else "info"
            add("PCIE_AER_CORRECTED", sev, bdf, f"{n} corrected AER events for {bdf} in kernel log")
        ce = sum(e["count"] for e in events if e["kind"] == "edac_ce")
        if ce:
            mcs = sorted({e["device"] for e in events if e["kind"] == "edac_ce"})
            add("MEM_ECC_CORRECTED", "warning" if ce >= th["edac_ce_warn"] else "info", ",".join(mcs),
                f"{ce} EDAC corrected memory errors ({', '.join(mcs)})")

    # --- interfaces
    links = parse_ip_link(_sec(snapshot, "ip_link") or "") if _sec(snapshot, "ip_link") else None
    for grp in baseline["interfaces"].values():
        for i in range(grp["count"]):
            name = f"{grp['prefix']}{i}"
            if links is not None:
                if name not in links:
                    add("INTERFACE_MISSING", "critical", name, f"{name} not present in ip link show")
                    continue
                if links[name]["mtu"] != grp["mtu"]:
                    add("MTU_MISMATCH", "critical", name, f"{name} mtu {links[name]['mtu']}, expected {grp['mtu']}")
                if links[name]["state"] != "UP":
                    add("LINK_DOWN", "critical", name, f"{name} state {links[name]['state']}")
            et = _sec(snapshot, f"ethtool:{name}")
            if et:
                e = parse_ethtool(et)
                if e["link_detected"] is False:
                    add("LINK_DOWN", "critical", name, f"ethtool {name}: Link detected: no")
                elif e["speed_mbps"] is not None and e["speed_mbps"] < grp["speed_mbps"]:
                    add("LINK_SPEED_DEGRADED", "critical", name,
                        f"ethtool {name}: Speed {e['speed_mbps']}Mb/s, expected {grp['speed_mbps']}Mb/s")

    # --- CPU frequency policy
    t = _sec(snapshot, "cpufreq")
    if t:
        cf = parse_cpufreq(t)
        drivers = ",".join(cf["drivers"]) or "unknown"
        if "powersave" in cf["governors"]:
            sev = "warning" if "acpi-cpufreq" in cf["drivers"] else "info"
            add("CPUFREQ_POWERSAVE", sev, "cpufreq",
                f"governor powersave on {cf['governors']['powersave']} CPUs, driver {drivers}, cur_khz {cf['cur_khz']}")
        elif cf["governors"] and set(cf["governors"]) != {baseline["cpufreq"]["expected_governor"]}:
            add("CPUFREQ_GOVERNOR", "info", "cpufreq", f"governors {cf['governors']}, driver {drivers}")

    # --- process NUMA placement
    ns, ts = _sec(snapshot, "numastat_pid"), _sec(snapshot, "taskset_pid")
    if ns and ts and numa_cpus:
        mem = parse_numastat_process(ns)
        aff = set(parse_taskset(ts))
        local_nodes = {n for n, cpus in numa_cpus.items() if aff & set(cpus)}
        total = sum(mem.values())
        if total > 0:
            remote = sum(v for n, v in mem.items() if n not in local_nodes) / total
            pid = (snapshot.get("context") or {}).get("pid")
            ev = (f"pid {pid}: CPUs on node(s) {sorted(local_nodes)}, memory by node (MB) {mem}; "
                  f"remote fraction {remote:.1%}")
            if remote >= th["numa_remote_fraction_crit"]:
                add("NUMA_REMOTE_MEMORY", "critical", f"pid {pid}", ev)
            elif remote >= th["numa_remote_fraction_warn"]:
                add("NUMA_REMOTE_MEMORY", "warning", f"pid {pid}", ev)

    # --- interrupts
    t = _sec(snapshot, "interrupts")
    if t:
        by_dev: dict[str, list[dict]] = {}
        for irq in parse_interrupts(t):
            if irq["bdf"]:
                by_dev.setdefault(irq["bdf"], []).append(irq)
        for bdf, irqs in by_dev.items():
            if len(irqs) < th["irq_min_queues"]:
                continue
            per_cpu = [sum(col) for col in zip(*(i["counts"] for i in irqs))]
            total = sum(per_cpu)
            if not total:
                continue
            top = max(range(len(per_cpu)), key=per_cpu.__getitem__)
            share = per_cpu[top] / total
            if share >= th["irq_single_cpu_fraction_warn"]:
                add("IRQ_CONCENTRATION", "warning", bdf,
                    f"{len(irqs)} IRQs of {bdf}: {share:.1%} of {total} interrupts on CPU{top}")
            node = dev_numa.get(bdf)
            if node is not None and node in numa_cpus:
                local = sum(per_cpu[c] for c in numa_cpus[node] if c < len(per_cpu))
                if local / total < 0.5:
                    add("IRQ_REMOTE_NUMA", "warning", bdf,
                        f"only {local / total:.1%} of {bdf} interrupts serviced on its NUMA node {node}")

    # --- per-CPU hot spot hidden by the average
    t = _sec(snapshot, "mpstat")
    if t:
        mp = parse_mpstat(t)
        if mp["all"]:
            all_busy = 100.0 - mp["all"].get("%idle", 100.0)
            for cpu, rec in mp["cpus"].items():
                busy = 100.0 - rec.get("%idle", 100.0)
                if busy >= th["cpu_hotspot_busy_pct"] and all_busy < th["cpu_hotspot_all_busy_max_pct"]:
                    add("CPU_HOTSPOT", "warning", f"cpu{cpu}",
                        f"CPU{cpu} {busy:.1f}% busy (%soft {rec.get('%soft', 0):.1f}, %sys {rec.get('%sys', 0):.1f}) "
                        f"while all-CPU busy is {all_busy:.1f}%")

    # --- storage
    t = _sec(snapshot, "iostat")
    if t:
        io = parse_iostat(t)
        for dev, rec in io["devices"].items():
            aw = max(rec.get("r_await", 0.0), rec.get("w_await", 0.0))
            if aw >= th["io_await_ms_warn"] and rec.get("%util", 0.0) >= th["io_util_pct_warn"]:
                add("IO_SATURATION", "warning", dev,
                    f"{dev}: r_await {rec.get('r_await', 0):.1f} ms, w_await {rec.get('w_await', 0):.1f} ms, "
                    f"%util {rec.get('%util', 0):.1f}; avg-cpu %iowait {io['avg_cpu'].get('%iowait', 0):.1f}")
    t = _sec(snapshot, "vmstat")
    if t:
        vm = parse_vmstat(t)
        if vm.get("b", 0) >= th["vmstat_blocked_warn"]:
            add("PROC_BLOCKED", "warning", "vmstat",
                f"avg {vm['b']:.1f} tasks in uninterruptible sleep (b) over {vm['samples']} live samples; wa {vm.get('wa', 0):.0f}%")
    return F


def analyze_fleet(snapshots: dict[str, dict], baseline: dict) -> list[Finding]:
    """Analyze every host, add cross-host consistency findings, de-duplicate, and sort
    (severity, host, check_id, subject). A cross-host MTU check flags any interface whose MTU
    differs from the fleet majority for that interface name (MTU_MISMATCH, critical)."""
    out: list[Finding] = []
    for snap in snapshots.values():
        out.extend(analyze_host(snap, baseline))
    mtus: dict[str, dict[str, int]] = {}
    for host, snap in snapshots.items():
        t = _sec(snap, "ip_link")
        if t:
            for iface, rec in parse_ip_link(t).items():
                mtus.setdefault(iface, {})[host] = rec["mtu"]
    for iface, per_host in mtus.items():
        if len(per_host) < 3:
            continue
        values = list(per_host.values())
        majority = max(set(values), key=values.count)
        for host, mtu in per_host.items():
            if mtu != majority:
                out.append(Finding(host, "MTU_MISMATCH", "critical", iface,
                                   f"{iface} mtu {mtu} differs from fleet majority {majority}"))
    uniq = {(f.host, f.check_id, f.severity, f.subject): f for f in out}
    return sorted(uniq.values(), key=lambda f: (SEVERITY_ORDER[f.severity], f.host, f.check_id, f.subject))


def write_report(findings: list[Finding], hosts: list[str]) -> str:
    """Render a Markdown fleet report: a per-host severity count table (every host listed, even
    with zero findings) followed by findings grouped critical -> warning -> info."""
    counts = {h: {"critical": 0, "warning": 0, "info": 0} for h in hosts}
    for f in findings:
        counts.setdefault(f.host, {"critical": 0, "warning": 0, "info": 0})[f.severity] += 1
    lines = ["# ORION host diagnostic report", "",
             "| Host | Critical | Warning | Info | Verdict |", "|---|---|---|---|---|"]
    for h in sorted(counts):
        c = counts[h]
        verdict = "DRAIN / repair" if c["critical"] else ("investigate" if c["warning"] else "healthy (check gaps)")
        lines.append(f"| {h} | {c['critical']} | {c['warning']} | {c['info']} | {verdict} |")
    for sev in ("critical", "warning", "info"):
        sel = [f for f in findings if f.severity == sev]
        if not sel:
            continue
        lines += ["", f"## {sev.capitalize()} ({len(sel)})", ""]
        lines += [f"- **{f.host}** `{f.check_id}` [{f.subject}] — {f.evidence}" for f in sel]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("snapshots", nargs="+", type=Path, help="hostdiag/1 JSON files")
    ap.add_argument("--baseline", type=Path, required=True, help="baseline YAML (expected config + thresholds)")
    ap.add_argument("--out", type=Path, help="write the Markdown report here (default: stdout)")
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    snaps = {s["host"]: s for s in (load_snapshot(p) for p in args.snapshots)}
    findings = analyze_fleet(snaps, load_baseline(args.baseline))
    report = write_report(findings, sorted(snaps))
    if args.out:
        args.out.write_text(report, encoding="utf-8")
        print(f"wrote {args.out}: {len(findings)} findings")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
