#!/usr/bin/env python3
"""Chapter 5 lab — reference solution: GPU/NIC/NUMA/rail topology mapper and all-reduce model.

Inputs per host (lab/data/hosts/<host>/): nvidia-smi_topo_m.txt, lstopo.txt, gpu_inventory.csv,
lspci_vmm.txt, ibdev2netdev.txt, lldp.txt, gdr_prereqs.txt. Model parameters: lab/data/path_model.yaml.

Outputs: a machine-readable GPU→NIC/HCA mapping (one row per GPU), a list of locality/GPUDirect
findings per host, rank→NIC maps under three policies, and a [MODELED] all-reduce estimate.

Units: bandwidth GB/s (1e9 B/s, per direction); time ms; sizes bytes.

CLI:
    python topo_mapper.py --data ../../lab/data --out mapping.csv
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REL_RANK = {"X": 0, "PIX": 1, "PXB": 2, "PHB": 3, "NODE": 4, "SYS": 5}
FLEET_DRIVER = "570.124.06"
SCENARIO_BYTES = 1 << 30  # 1 GiB all-reduce


# --------------------------------------------------------------------------------------
# Task 1 — parsers
# --------------------------------------------------------------------------------------
def normalize_bdf(s: str) -> str:
    """Return a PCI address as 'dddd:bb:dd.f' lower-case.

    Accepts nvidia-smi's 8-digit domain ('00000000:1A:00.0'), lspci's 4-digit domain, and
    lstopo's domain-less form ('1a:00.0').
    """
    s = s.strip().lower()
    parts = s.split(":")
    if len(parts) == 2:
        return f"0000:{parts[0]:0>2}:{parts[1]}"
    dom = parts[0][-4:]
    return f"{dom}:{parts[1]:0>2}:{parts[2]}"


def parse_topo_matrix(text: str) -> dict:
    """Parse `nvidia-smi topo -m` text.

    Returns {"devices": [...], "rel": {(row, col): label}, "cpu_affinity": {gpu: str},
    "numa_affinity": {gpu: int}, "nic_names": {"NIC0": "mlx5_0", ...}}.
    Columns are tab-separated; "CPU Affinity", "NUMA Affinity", "GPU NUMA ID" follow the device columns.
    """
    lines = text.splitlines()
    hdr_i = next(i for i, ln in enumerate(lines) if "GPU0" in ln and ln.startswith("\t"))
    header = [h.strip() for h in lines[hdr_i].split("\t")[1:]]
    devices = [h for h in header if re.fullmatch(r"(GPU|NIC)\d+", h)]
    rel, cpu, numa = {}, {}, {}
    for ln in lines[hdr_i + 1:]:
        if not ln.strip():
            break
        parts = ln.split("\t")
        row = parts[0].strip()
        cells = [p.strip() for p in parts[1:]]
        for col, val in zip(devices, cells[: len(devices)]):
            rel[(row, col)] = val
        extra = cells[len(devices):]
        if row.startswith("GPU") and len(extra) >= 2:
            cpu[row] = extra[0]
            numa[row] = int(extra[1]) if extra[1].isdigit() else None
    nic_names = {m.group(1): m.group(2) for m in re.finditer(r"^\s*(NIC\d+):\s*(\S+)\s*$", text, re.M)}
    return {"devices": devices, "rel": rel, "cpu_affinity": cpu, "numa_affinity": numa, "nic_names": nic_names}


def parse_lstopo(text: str) -> dict:
    """Parse indented `lstopo-no-graphics` text into PCI device records keyed by normalized BDF.

    Each record: {"bdf", "pci_class", "package", "ancestors": [bridge ids from HostBridge down],
    "hostbridge": id, "kind": "GPU"|"NIC"|"OTHER", "name": "nvml3"/"mlx5_1"/..., "netdev": str|None}.
    Bridge ids are assigned in document order: "HB0", "HB1", ... and "BR0", "BR1", ...
    """
    devs: dict[str, dict] = {}
    stack: list[tuple[int, str]] = []  # (indent, node id or device bdf)
    package = None
    n_hb = n_br = 0
    current = None
    for raw in text.splitlines():
        if not raw.strip():
            continue
        ind = len(raw) - len(raw.lstrip(" "))
        s = raw.strip()
        while stack and stack[-1][0] >= ind:
            stack.pop()
        m = re.match(r"Package L#(\d+)", s)
        if m:
            package = int(m.group(1))
            stack = [(ind, "PKG")]
            continue
        if s.startswith("HostBridge"):
            stack.append((ind, f"HB{n_hb}")); n_hb += 1
            continue
        if s.startswith("PCIBridge"):
            stack.append((ind, f"BR{n_br}")); n_br += 1
            continue
        m = re.match(r"PCI ([0-9a-fA-F:.]+) \(([^)]*)\)", s)
        if m:
            bdf = normalize_bdf(m.group(1))
            anc = [x for _, x in stack if x.startswith(("HB", "BR"))]
            current = {"bdf": bdf, "pci_class": m.group(2), "package": package, "ancestors": anc,
                       "hostbridge": anc[0] if anc else None, "kind": "OTHER", "name": None, "netdev": None}
            devs[bdf] = current
            stack.append((ind, bdf))
            continue
        m = re.match(r'(GPU\(NVML\)|OpenFabrics|Net|Block\(Disk\)|CoProc\(CUDA\))\s+"([^"]+)"', s)
        if m and current is not None and stack and stack[-1][1] == current["bdf"]:
            kind, name = m.groups()
            if kind == "GPU(NVML)":
                current["kind"], current["name"] = "GPU", name
            elif kind == "OpenFabrics":
                current["kind"], current["name"] = "NIC", name
            elif kind == "Net":
                current["netdev"] = name
    return devs


def classify_path(a: dict, b: dict) -> str:
    """nvidia-smi-style relation between two lstopo device records.

    A PCIe switch is an upstream-port bridge with one downstream-port bridge per device, so every device
    has its own immediate parent bridge. Let k = length of the common ancestor prefix.
    SYS: different packages; NODE: same package, different host bridges; PHB: the only shared ancestor is
    the host bridge (k == 1); PIX: the deepest common ancestor is one switch's upstream port and each
    device hangs directly from one of its downstream ports (k >= 2 and exactly one bridge remains below the
    common prefix on each side); PXB: otherwise with k >= 2 (the path crosses more than one switch).
    """
    if a["bdf"] == b["bdf"]:
        return "X"
    if a["package"] != b["package"]:
        return "SYS"
    if a["hostbridge"] != b["hostbridge"]:
        return "NODE"
    pa, pb = a["ancestors"], b["ancestors"]
    common = 0
    for x, y in zip(pa, pb):
        if x != y:
            break
        common += 1
    if common >= 2 and len(pa) - common == 1 and len(pb) - common == 1:
        return "PIX"
    return "PXB" if common >= 2 else "PHB"


def parse_gpu_inventory(text: str) -> pd.DataFrame:
    """Parse `nvidia-smi --query-gpu=index,uuid,pci.bus_id --format=csv` → columns index, uuid, bdf."""
    rows = []
    for ln in text.splitlines()[1:]:
        if ln.strip():
            i, u, b = [x.strip() for x in ln.split(",")]
            rows.append({"index": int(i), "uuid": u, "bdf": normalize_bdf(b)})
    return pd.DataFrame(rows)


def parse_lspci_vmm(text: str) -> dict:
    """Parse `lspci -D -vmm` blocks → {bdf: {"slot": int|None, "numa": int|None, "device": str}}."""
    out = {}
    for block in text.strip().split("\n\n"):
        kv = {}
        for ln in block.splitlines():
            if ":" in ln:
                k, v = ln.split(":", 1)
                kv[k.strip()] = v.strip()
        if "Slot" in kv:
            out[normalize_bdf(kv["Slot"])] = {
                "slot": int(kv["PhySlot"]) if kv.get("PhySlot", "").isdigit() else None,
                "numa": int(kv["NUMANode"]) if kv.get("NUMANode", "").lstrip("-").isdigit() else None,
                "device": kv.get("Device", "")}
    return out


def parse_ibdev2netdev(text: str) -> dict:
    """'mlx5_0 port 1 ==> enp13s0np0 (Up)' → {"mlx5_0": "enp13s0np0"}."""
    return {m.group(1): m.group(2) for m in re.finditer(r"^(\S+) port \d+ ==> (\S+)", text, re.M)}


def parse_lldp(text: str) -> dict:
    """`lldpcli show neighbors -f keyvalue` → {netdev: {"chassis": str, "port": str}}."""
    out: dict[str, dict] = {}
    for m in re.finditer(r"^lldp\.([^.]+)\.(chassis\.name|port\.ifname)=(.*)$", text, re.M):
        nd, key, val = m.groups()
        out.setdefault(nd, {})["chassis" if key == "chassis.name" else "port"] = val.strip()
    return out


def rail_from_chassis(name: str | None) -> int | None:
    """'orion-be-leaf-r3' → 3; anything else (frontend leaves) → None."""
    m = re.search(r"be-leaf-r(\d+)$", name or "")
    return int(m.group(1)) if m else None


def parse_gdr(text: str) -> dict:
    """Parse gdr_prereqs.txt → {"peermem": bool, "iommu_passthrough": bool, "iommu_enabled": bool,
    "acs_redirect_ports": [bdf...], "driver": str, "ofed": str}."""
    sec: dict[str, list[str]] = {}
    cur = None
    for ln in text.splitlines():
        if ln.startswith("### "):
            cur = ln[4:]
            sec[cur] = []
        elif cur is not None and ln.strip():
            sec[cur].append(ln)
    get = lambda pfx: next((v for k, v in sec.items() if k.startswith(pfx)), [])  # noqa: E731
    cmdline = " ".join(get("cat /proc/cmdline"))
    lsmod = get("lsmod")
    acs = [normalize_bdf(ln.split()[0]) for ln in get("lspci -vvv") if "ReqRedir+" in ln]
    return {"peermem": any(ln.split()[0] in ("nvidia_peermem", "nv_peer_mem") for ln in lsmod),
            "iommu_enabled": bool(re.search(r"(intel|amd)_iommu=on", cmdline)),
            "iommu_passthrough": "iommu=pt" in cmdline.split(),
            "acs_redirect_ports": acs,
            "driver": (get("nvidia-smi") or [""])[0].strip(),
            "ofed": (get("ofed_info") or [""])[0].strip().rstrip(":")}


# --------------------------------------------------------------------------------------
# Task 2 — mapping
# --------------------------------------------------------------------------------------
@dataclass
class HostInfo:
    name: str
    topo: dict
    lstopo: dict
    mapping: pd.DataFrame
    gdr: dict
    nics: pd.DataFrame = field(default_factory=pd.DataFrame)


def _nic_table(host_dir: Path, topo: dict, lst: dict) -> pd.DataFrame:
    vmm = parse_lspci_vmm((host_dir / "lspci_vmm.txt").read_text(encoding="utf-8"))
    nd = parse_ibdev2netdev((host_dir / "ibdev2netdev.txt").read_text(encoding="utf-8"))
    lldp = parse_lldp((host_dir / "lldp.txt").read_text(encoding="utf-8"))
    by_name = {d["name"]: d for d in lst.values() if d["kind"] == "NIC"}
    rows = []
    for topo_name, hca in topo["nic_names"].items():
        d = by_name[hca]
        netdev = nd.get(hca, d["netdev"])
        chassis = lldp.get(netdev, {}).get("chassis")
        rows.append({"topo_name": topo_name, "hca": hca, "netdev": netdev, "bdf": d["bdf"],
                     "numa": vmm.get(d["bdf"], {}).get("numa"), "slot": vmm.get(d["bdf"], {}).get("slot"),
                     "leaf": chassis, "port": lldp.get(netdev, {}).get("port"), "rail": rail_from_chassis(chassis)})
    return pd.DataFrame(rows)


def build_mapping(host_dir: str | Path) -> pd.DataFrame:
    """One row per GPU with columns:
    host, gpu_index, gpu_uuid, gpu_bdf, gpu_numa, gpu_hostbridge, rail, rail_nic, rail_nic_netdev,
    rail_nic_bdf, rail_nic_numa, rail_nic_slot, rail_relation, nearest_nic, nearest_relation,
    nearest_nic_rail, relation_crosscheck_ok, aligned.

    rail = the GPU index (ORION convention: GPU i ↔ rail i). rail_nic = the compute NIC whose LLDP
    neighbour is the rail-i leaf. nearest_nic = the compute NIC with the best topo relation to the GPU
    (ties: prefer the NIC on the GPU's rail, then lowest HCA name). aligned = rail_relation == "PIX"
    and nearest_nic == rail_nic. relation_crosscheck_ok = lstopo-derived relation equals nvidia-smi's.
    """
    return load_host(host_dir).mapping


def load_host(host_dir: str | Path) -> HostInfo:
    """Parse every capture for one host and build its mapping (see build_mapping)."""
    hd = Path(host_dir)
    topo = parse_topo_matrix((hd / "nvidia-smi_topo_m.txt").read_text(encoding="utf-8"))
    lst = parse_lstopo((hd / "lstopo.txt").read_text(encoding="utf-8"))
    inv = parse_gpu_inventory((hd / "gpu_inventory.csv").read_text(encoding="utf-8"))
    gdr = parse_gdr((hd / "gdr_prereqs.txt").read_text(encoding="utf-8"))
    nics = _nic_table(hd, topo, lst)
    compute = nics[nics["rail"].notna()]
    rows = []
    for g in inv.itertuples(index=False):
        gname = f"GPU{g.index}"
        gdev = lst[g.bdf]
        rels = {r.hca: topo["rel"][(gname, r.topo_name)] for r in compute.itertuples(index=False)}
        rail_row = compute[compute["rail"] == g.index]
        rail_nic = rail_row.iloc[0] if len(rail_row) else None
        best = sorted(compute.itertuples(index=False),
                      key=lambda r: (REL_RANK[rels[r.hca]], 0 if r.rail == g.index else 1, r.hca))[0]
        cross = all(classify_path(gdev, lst[r.bdf]) == rels[r.hca] for r in compute.itertuples(index=False))
        rail_rel = rels[rail_nic["hca"]] if rail_nic is not None else None
        rows.append({
            "host": hd.name, "gpu_index": g.index, "gpu_uuid": g.uuid, "gpu_bdf": g.bdf,
            "gpu_numa": topo["numa_affinity"].get(gname), "gpu_hostbridge": gdev["hostbridge"],
            "rail": g.index,
            "rail_nic": None if rail_nic is None else rail_nic["hca"],
            "rail_nic_netdev": None if rail_nic is None else rail_nic["netdev"],
            "rail_nic_bdf": None if rail_nic is None else rail_nic["bdf"],
            "rail_nic_numa": None if rail_nic is None else rail_nic["numa"],
            "rail_nic_slot": None if rail_nic is None else rail_nic["slot"],
            "rail_relation": rail_rel, "nearest_nic": best.hca, "nearest_relation": rels[best.hca],
            "nearest_nic_rail": int(best.rail), "relation_crosscheck_ok": cross,
            "aligned": bool(rail_rel == "PIX" and best.hca == (rail_nic["hca"] if rail_nic is not None else None)),
        })
    return HostInfo(name=hd.name, topo=topo, lstopo=lst, mapping=pd.DataFrame(rows), gdr=gdr, nics=nics)


def write_mapping_csv(mapping: pd.DataFrame, path: str | Path) -> None:
    """Write the mapping as CSV with a stable column order and LF line endings."""
    mapping.to_csv(path, index=False, lineterminator="\n")


# --------------------------------------------------------------------------------------
# Task 3 — findings
# --------------------------------------------------------------------------------------
def detect_issues(info: HostInfo, fleet_driver: str = FLEET_DRIVER) -> list[dict]:
    """Return findings for one host: dicts with host, gpu (int|None), code, severity, detail.

    Codes and severities:
      RAIL_MISMATCH (blocker)        GPU has a PIX-local NIC whose LLDP rail ≠ GPU index (cabling)
      NIC_NOT_LOCAL (major)          GPU has no PIX-local compute NIC (card in wrong slot/socket)
      NIC_SHARED (major)             two GPUs' nearest compute NIC is the same NIC (one finding per NIC)
      ACS_REDIRECT (major)           ACS request redirect enabled on GPU/NIC-facing switch ports
      GDR_PEERMEM_MISSING (major)    no nvidia_peermem/nv_peer_mem loaded (GPUDirect RDMA path absent
                                     unless a DMA-BUF path is verified)
      IOMMU_NOT_PASSTHROUGH (minor)  IOMMU enabled without iommu=pt
      DRIVER_DRIFT (minor)           GPU driver differs from the fleet baseline
    """
    m, gdr, host = info.mapping, info.gdr, info.name
    out = []
    compute = info.nics[info.nics["rail"].notna()]
    for r in m.itertuples(index=False):
        g = f"GPU{r.gpu_index}"
        pix = [n for n in compute.itertuples(index=False) if info.topo["rel"][(g, n.topo_name)] == "PIX"]
        if not pix:
            out.append({"host": host, "gpu": r.gpu_index, "code": "NIC_NOT_LOCAL", "severity": "major",
                        "detail": f"{g} has no PIX-local NIC; its rail-{r.rail} NIC {r.rail_nic} is {r.rail_relation} "
                                  f"(slot {r.rail_nic_slot}, NUMA {r.rail_nic_numa}); nearest is {r.nearest_nic} ({r.nearest_relation})"})
        else:
            for n in pix:
                if int(n.rail) != r.gpu_index:
                    out.append({"host": host, "gpu": r.gpu_index, "code": "RAIL_MISMATCH", "severity": "blocker",
                                "detail": f"{g}'s local NIC {n.hca} ({n.netdev}) is cabled to {n.leaf} {n.port}; expected "
                                          f"orion-be-leaf-r{r.gpu_index}"})
    for nic, grp in m.groupby("nearest_nic"):
        if len(grp) > 1:
            out.append({"host": host, "gpu": None, "code": "NIC_SHARED", "severity": "major",
                        "detail": f"{nic} is the nearest compute NIC for GPUs {sorted(grp['gpu_index'].tolist())}"})
    if gdr["acs_redirect_ports"]:
        out.append({"host": host, "gpu": None, "code": "ACS_REDIRECT", "severity": "major",
                    "detail": f"ReqRedir+ on {len(gdr['acs_redirect_ports'])} switch downstream ports: GPU↔NIC peer "
                              f"traffic is forced up to the root complex"})
    if not gdr["peermem"]:
        out.append({"host": host, "gpu": None, "code": "GDR_PEERMEM_MISSING", "severity": "major",
                    "detail": "nvidia_peermem not loaded; GPUDirect RDMA unavailable unless a DMA-BUF path is verified "
                              "(NCCL_DEBUG=INFO channel lines end in /GDRDMA only when GDR is used)"})
    if gdr["iommu_enabled"] and not gdr["iommu_passthrough"]:
        out.append({"host": host, "gpu": None, "code": "IOMMU_NOT_PASSTHROUGH", "severity": "minor",
                    "detail": "IOMMU enabled without iommu=pt: DMA is translated; check vendor guidance"})
    if gdr["driver"] and gdr["driver"] != fleet_driver:
        out.append({"host": host, "gpu": None, "code": "DRIVER_DRIFT", "severity": "minor",
                    "detail": f"driver {gdr['driver']} != fleet {fleet_driver}"})
    return out


# --------------------------------------------------------------------------------------
# Task 4 — rank maps and the all-reduce model
# --------------------------------------------------------------------------------------
def make_rank_map(nodes: list[HostInfo], policy: str) -> pd.DataFrame:
    """Rank → NIC assignment for a job with one rank per GPU on each node in `nodes` (order = node order).

    policy: "aligned" (GPU i → its rail-i NIC per LLDP), "nearest" (GPU i → nearest compute NIC, what a
    topology-aware library picks by default), "cross_socket" (GPU i → rail NIC of GPU (i+4) % 8, the
    effect of a rotated per-rank NIC table), "pxn" (PXN eligibility rule: ring r exits through the rail-r
    NIC via an NVLink-connected peer GPU only if some GPU on the node reaches that NIC at PXB or closer;
    relation = that best relation. If no GPU qualifies, PXN is never engaged and the rank falls back to its
    nearest NIC, exactly as in "nearest"). Columns: rank, node, host,
    local_rank, ring, nic, relation, acs, host_staged, sharers. ring = local_rank (one ring per rail).
    host_staged = no peer-memory module on the host (the GDR distance gate is applied in path_params).
    """
    rows = []
    rank = 0
    for ni, info in enumerate(nodes):
        m = info.mapping.sort_values("gpu_index")
        nic_by_rail = {int(r.rail): r for r in info.nics[info.nics["rail"].notna()].itertuples(index=False)}
        local = []
        for r in m.itertuples(index=False):
            if policy == "aligned":
                nic = nic_by_rail[r.gpu_index]
            elif policy == "nearest":
                nic = next(n for n in nic_by_rail.values() if n.hca == r.nearest_nic)
            elif policy == "cross_socket":
                nic = nic_by_rail[(r.gpu_index + 4) % 8]
            elif policy == "pxn":
                nic = nic_by_rail[r.gpu_index]
                best = min((info.topo["rel"][(f"GPU{g}", nic.topo_name)] for g in range(8)), key=REL_RANK.get)
                if REL_RANK[best] > REL_RANK["PXB"]:  # no eligible proxy: PXN not engaged -> nearest NIC
                    nic = next(n for n in nic_by_rail.values() if n.hca == r.nearest_nic)
            else:
                raise ValueError(policy)
            if policy == "pxn" and nic.hca == nic_by_rail[r.gpu_index].hca:
                relation = min((info.topo["rel"][(f"GPU{g}", nic.topo_name)] for g in range(8)), key=REL_RANK.get)
            else:
                relation = info.topo["rel"][(f"GPU{r.gpu_index}", nic.topo_name)]
            local.append({"rank": rank, "node": ni, "host": info.name, "local_rank": int(r.gpu_index),
                          "ring": int(r.gpu_index), "nic": nic.hca, "relation": relation,
                          "acs": bool(info.gdr["acs_redirect_ports"]), "host_staged": not info.gdr["peermem"]})
            rank += 1
        counts = pd.Series([x["nic"] for x in local]).value_counts()
        for x in local:
            x["sharers"] = int(counts[x["nic"]])
        rows += local
    return pd.DataFrame(rows)


def path_params(row: dict, params: dict) -> tuple[float, float]:
    """(mean GB/s, cv) for one rank's GPU→NIC path: class value, then ACS factor, then host-staging cap
    (applied when row["host_staged"] is true OR the relation is farther than params["gdr_max_relation"],
    the NCCL_NET_GDR_LEVEL distance gate), then division by the number of GPUs sharing the NIC."""
    c = params["classes"][row["relation"]]
    mean, cv = float(c["mean_GBps"]), float(c["cv"])
    if row["acs"]:
        mean *= params["modifiers"]["acs_redirect"]["bw_factor"]
        cv += params["modifiers"]["acs_redirect"]["cv_add"]
    gate = params.get("gdr_max_relation", "SYS")
    if row["host_staged"] or REL_RANK[row["relation"]] > REL_RANK[gate]:
        mean = min(mean, params["modifiers"]["host_staged"]["bw_cap_GBps"])
        cv += params["modifiers"]["host_staged"]["cv_add"]
    return mean / row["sharers"], cv


def model_allreduce(rank_map: pd.DataFrame, params: dict, size_bytes: int = SCENARIO_BYTES,
                    iters: int = 200, seed: int = 7) -> dict:
    """[MODELED] ring all-reduce, one ring per rail.

    For each iteration, every rank's path bandwidth is sampled as mean × max(min_bw_fraction, 1 + cv·z),
    z ~ N(0,1) from np.random.default_rng(seed).standard_normal((iters, n_ranks)) in rank order. Ring r
    carries size/R bytes and is limited by its slowest member: t_r = 2(n−1)/n × (size/R) / min_bw_r.
    Iteration time t = max_r t_r + alpha. busbw = 2(n−1)/n × size / t.
    Returns n_ranks, median_ms, p99_ms (numpy linear percentile), mean_ms, cv (std/mean of t),
    busbw_median_GBps.
    """
    n = len(rank_map)
    rings = sorted(rank_map["ring"].unique())
    pr = [path_params(r, params) for r in rank_map.to_dict("records")]
    mean = np.array([p[0] for p in pr])
    cv = np.array([p[1] for p in pr])
    z = np.random.default_rng(seed).standard_normal((iters, n))
    bw = mean * np.maximum(params.get("min_bw_fraction", 0.2), 1.0 + cv * z)  # GB/s
    ring_idx = rank_map["ring"].to_numpy()
    factor = 2 * (n - 1) / n
    per_ring = size_bytes / len(rings)
    t_rings = np.stack([factor * per_ring / (bw[:, ring_idx == r].min(axis=1) * 1e9) for r in rings], axis=1)
    t = t_rings.max(axis=1) + params.get("alpha_ms", 0.0) / 1e3
    med = float(np.median(t))
    return {"n_ranks": n, "median_ms": med * 1e3, "p99_ms": float(np.percentile(t, 99)) * 1e3,
            "mean_ms": float(t.mean()) * 1e3, "cv": float(t.std() / t.mean()),
            "busbw_median_GBps": factor * size_bytes / med / 1e9}


# --------------------------------------------------------------------------------------
# Task 5 — end-to-end analysis
# --------------------------------------------------------------------------------------
def analyze(data_dir: str | Path) -> dict:
    """Load every host, build mappings and findings, and run scenarios on a job of N = params["nodes_per_job"]
    nodes (16 → 128 GPUs):
      S1_aligned_healthy      N × orion-n01, policy aligned
      S2_cross_socket_healthy N × orion-n01, policy cross_socket
      S3_scheduled_nearest    (N−2) × orion-n01 + orion-n02 + orion-n17, policy nearest
      S4_scheduled_aligned    same nodes, policy aligned
      S5_scheduled_pxn        same nodes, policy pxn (not eligible on n17 -> identical to S3)
      S4_gdr_level_sys        S4 with gdr_max_relation = SYS (what NCCL_NET_GDR_LEVEL=SYS would do)
    (orion-n23 failed node acceptance with a blocker and is not schedulable.)
    Returns {"mappings": {host: df}, "issues": [..], "scenarios": {name: model result}}.
    """
    d = Path(data_dir)
    params = yaml.safe_load((d / "path_model.yaml").read_text(encoding="utf-8"))
    hosts = {p.name: load_host(p) for p in sorted((d / "hosts").iterdir()) if p.is_dir()}
    issues = [i for h in hosts.values() for i in detect_issues(h)]
    good = hosts["orion-n01"]
    n = int(params.get("nodes_per_job", 16))
    sched = [good] * (n - 2) + [hosts["orion-n02"], hosts["orion-n17"]]
    sys_params = dict(params, gdr_max_relation="SYS")
    scenarios = {
        "S1_aligned_healthy": model_allreduce(make_rank_map([good] * n, "aligned"), params),
        "S2_cross_socket_healthy": model_allreduce(make_rank_map([good] * n, "cross_socket"), params),
        "S3_scheduled_nearest": model_allreduce(make_rank_map(sched, "nearest"), params),
        "S4_scheduled_aligned": model_allreduce(make_rank_map(sched, "aligned"), params),
        "S5_scheduled_pxn": model_allreduce(make_rank_map(sched, "pxn"), params),
        "S4_gdr_level_sys": model_allreduce(make_rank_map(sched, "aligned"), sys_params),
    }
    return {"mappings": {k: v.mapping for k, v in hosts.items()}, "issues": issues, "scenarios": scenarios}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", type=Path, default=Path(__file__).resolve().parents[2] / "lab" / "data")
    ap.add_argument("--out", type=Path, default=Path("gpu_nic_mapping.csv"))
    args = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    a = analyze(args.data)
    write_mapping_csv(pd.concat(a["mappings"].values(), ignore_index=True), args.out)
    print(f"mapping written to {args.out}")
    for i in a["issues"]:
        print(f"[{i['severity']:7}] {i['host']} {i['code']}: {i['detail']}")
    print("\nScenario (1 GiB all-reduce, 128 ranks)        median ms   p99 ms   busbw GB/s   CV   [MODELED]")
    for k, v in a["scenarios"].items():
        print(f"{k:42} {v['median_ms']:9.2f} {v['p99_ms']:8.2f} {v['busbw_median_GBps']:11.1f} {v['cv']:6.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
