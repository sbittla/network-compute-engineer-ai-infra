#!/usr/bin/env python3
"""Fleet host-snapshot analyzer (Chapter 3, Progressive Lab 1) — STARTER (complete the TODOs).

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
    # TODO: Split each line on the FIRST ':' only. Use parse_cpu_list() for 'NUMA nodeN CPU(s)' values.
    raise NotImplementedError("TODO: implement parse_lscpu()")


def parse_numactl_hardware(text: str) -> dict:
    """Parse `numactl --hardware`.

    Returns {"nodes": {id: {"cpus": [...], "size_mb": int, "free_mb": int}},
             "distances": [[int, ...], ...]} (distance matrix rows in node order).
    """
    # TODO: Lines look like 'node 0 cpus: 0 1 2 ...', 'node 0 size: 1031868 MB', 'node 0 free: ...'.
    #       After 'node distances:' read rows like '  0:  10  21'.
    raise NotImplementedError("TODO: implement parse_numactl_hardware()")


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
    # TODO: A device starts at column 0 with a BDF ('18:00.0 3D controller: ...').
    #       Look for 'NUMA node:', 'LnkCap:', 'LnkSta:' and '<access denied>' in indented lines.
    #       Extract numbers with regexes; ignore '(ok)'/'(downgraded)' annotations. Use _kind_from_desc().
    raise NotImplementedError("TODO: implement parse_lspci_links()")


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
    # TODO: Find the header row starting with 'r b'. Exclude the FIRST data row: it is the since-boot average.
    raise NotImplementedError("TODO: implement parse_vmstat()")


def parse_iostat(text: str) -> dict:
    """Parse `iostat -x <interval> <count>` and keep the LAST report (the first is since boot).

    Returns {"avg_cpu": {"%user": .., "%iowait": .., "%idle": .., ...},
             "devices": {name: {column: value}}}.
    """
    # TODO: Reports start at 'avg-cpu:'. Keep only the LAST report: the first one is since boot.
    #       Map device columns by the 'Device' header names.
    raise NotImplementedError("TODO: implement parse_iostat()")


def parse_mpstat(text: str) -> dict:
    """Parse `mpstat -P ALL <interval> <count>`; prefer the 'Average:' block, else the last block.

    Returns {"all": {"%usr": .., "%idle": .., ...}, "cpus": {cpu_id: {...}}}. Columns are found
    by header name and values are aligned from the right (robust to 12h 'AM/PM' timestamps).
    """
    # TODO: Header rows contain 'CPU' and '%'-columns. Align values from the RIGHT of each row.
    #       Prefer the 'Average:' block.
    raise NotImplementedError("TODO: implement parse_mpstat()")


def parse_interrupts(text: str) -> list[dict]:
    """Parse /proc/interrupts.

    Returns one dict per numbered IRQ line: {"irq": "180", "counts": [int per CPU],
    "name": last token (e.g. 'mlx5_comp0@pci:0000:19:00.0'), "bdf": normalized BDF or None}.
    Non-numeric rows (NMI, LOC, ...) are ignored.
    """
    # TODO: Line 1 lists CPU0..CPUn (count them). Each numbered IRQ row has one count per CPU,
    #       then chip/type text, then the action name. Extract a PCI BDF if the text contains one.
    raise NotImplementedError("TODO: implement parse_interrupts()")


def parse_ip_link(text: str) -> dict:
    """Parse `ip link show` -> {iface: {"mtu": int, "state": str, "flags": [str]}}."""
    # TODO: Match '<idx>: <name>[@peer]: <FLAGS> mtu <n> ... state <STATE>'.
    raise NotImplementedError("TODO: implement parse_ip_link()")


def parse_ethtool(text: str) -> dict:
    """Parse `ethtool <iface>` -> {"speed_mbps": int|None, "duplex": str|None, "link_detected": bool|None}."""
    # TODO: Read 'Speed: 400000Mb/s' (may be 'Unknown!'), 'Duplex:', 'Link detected: yes|no'.
    raise NotImplementedError("TODO: implement parse_ethtool()")


def parse_numastat_process(text: str) -> dict:
    """Parse `numastat -p <pid>` -> {node_id: total_MB} from the 'Total' row."""
    # TODO: Find the header with 'Node 0 Node 1 ... Total', then the row starting with 'Total'.
    raise NotImplementedError("TODO: implement parse_numastat_process()")


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
    # TODO: Use the module regexes (_AER_RX, _EDAC, _XID, _LINK_DOWN) and the 'mce: [Hardware Error]' marker.
    #       Count one AER event per 'error received' line (not per detail line).
    raise NotImplementedError("TODO: implement scan_kernel_log()")


# --------------------------------------------------------------------------- analysis
def _sec(snapshot: dict, name: str) -> str | None:
    s = snapshot.get("sections", {}).get(name)
    return s["stdout"] if s and s.get("status") == "ok" else None


def analyze_host(snapshot: dict, baseline: dict) -> list[Finding]:
    """Apply every rule in the lab README's severity policy to one snapshot.

    Must never raise because a section is missing, denied, skipped or empty: instead emit an
    EVIDENCE_GAP info finding for each section whose status is not "ok".
    """
    # TODO: Implement the severity policy in lab/README.md, rule by rule. Use _sec() so that sections whose
    #       status is not 'ok' are skipped, and emit EVIDENCE_GAP (info) for each of them.
    #       Fall back to pcie_sysfs when lspci shows '<access denied>' (non-root).
    #       A GPU whose link SPEED is below capability while all GPUs are idle is info (PCIE_SPEED_LOW_IDLE),
    #       not a fault: GPUs lower link speed when idle. Link WIDTH below capability is always critical.
    raise NotImplementedError("TODO: implement analyze_host()")


def analyze_fleet(snapshots: dict[str, dict], baseline: dict) -> list[Finding]:
    """Analyze every host, add cross-host consistency findings, de-duplicate, and sort
    (severity, host, check_id, subject). A cross-host MTU check flags any interface whose MTU
    differs from the fleet majority for that interface name (MTU_MISMATCH, critical)."""
    # TODO: Concatenate analyze_host() results, add the cross-host MTU majority check, de-duplicate on
    #       (host, check_id, severity, subject) and sort by (severity, host, check_id, subject).
    raise NotImplementedError("TODO: implement analyze_fleet()")


def write_report(findings: list[Finding], hosts: list[str]) -> str:
    """Render a Markdown fleet report: a per-host severity count table (every host listed, even
    with zero findings) followed by findings grouped critical -> warning -> info."""
    # TODO: Per-host table (every host, even with zero findings) then findings grouped by severity.
    raise NotImplementedError("TODO: implement write_report()")


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
