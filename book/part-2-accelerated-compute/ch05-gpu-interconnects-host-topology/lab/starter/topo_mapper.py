#!/usr/bin/env python3
"""Chapter 5 lab — STARTER: GPU/NIC/NUMA/rail topology mapper and all-reduce model.

Implement every function that raises NotImplementedError, then run `python ../check.py`.

Inputs per host (lab/data/hosts/<host>/): nvidia-smi_topo_m.txt, lstopo.txt, gpu_inventory.csv,
lspci_vmm.txt, ibdev2netdev.txt, lldp.txt, gdr_prereqs.txt. Model parameters: lab/data/path_model.yaml.

Outputs: a machine-readable GPU→NIC/HCA mapping (one row per GPU), a list of locality/GPUDirect
findings per host, rank→NIC maps under three policies, and a [MODELED] all-reduce estimate.

Units: bandwidth GB/s (1e9 B/s, per direction); time ms; sizes bytes.

CLI:
    python topo_mapper.py --data ../data --out gpu_nic_mapping.csv
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
    # TODO: lower-case; handle 2-part (no domain), 8-digit and 4-digit domains.
    raise NotImplementedError("normalize_bdf")


def parse_topo_matrix(text: str) -> dict:
    """Parse `nvidia-smi topo -m` text.

    Returns {"devices": [...], "rel": {(row, col): label}, "cpu_affinity": {gpu: str},
    "numa_affinity": {gpu: int}, "nic_names": {"NIC0": "mlx5_0", ...}}.
    Columns are tab-separated; "CPU Affinity", "NUMA Affinity", "GPU NUMA ID" follow the device columns.
    """
    # TODO: find the header line (starts with a tab, contains GPU0); split rows on tabs;
    #       collect relations, CPU/NUMA affinity for GPU rows, and the 'NICn: mlx5_m' legend.
    raise NotImplementedError("parse_topo_matrix")


def parse_lstopo(text: str) -> dict:
    """Parse indented `lstopo-no-graphics` text into PCI device records keyed by normalized BDF.

    Each record: {"bdf", "pci_class", "package", "ancestors": [bridge ids from HostBridge down],
    "hostbridge": id, "kind": "GPU"|"NIC"|"OTHER", "name": "nvml3"/"mlx5_1"/..., "netdev": str|None}.
    Bridge ids are assigned in document order: "HB0", "HB1", ... and "BR0", "BR1", ...
    """
    # TODO: walk lines keeping a stack of (indent, node); assign HB<n>/BR<n> ids in document order;
    #       attach GPU(NVML)/OpenFabrics/Net child lines to the PCI device above them.
    raise NotImplementedError("parse_lstopo")


def classify_path(a: dict, b: dict) -> str:
    """nvidia-smi-style relation between two lstopo device records.

    A PCIe switch is an upstream-port bridge with one downstream-port bridge per device, so every device
    has its own immediate parent bridge. Let k = length of the common ancestor prefix.
    SYS: different packages; NODE: same package, different host bridges; PHB: the only shared ancestor is
    the host bridge (k == 1); PIX: the deepest common ancestor is one switch's upstream port and each
    device hangs directly from one of its downstream ports (k >= 2 and exactly one bridge remains below the
    common prefix on each side); PXB: otherwise with k >= 2 (the path crosses more than one switch).
    """
    # TODO: apply the rules in the docstring using package, hostbridge and the ancestor lists.
    raise NotImplementedError("classify_path")


def parse_gpu_inventory(text: str) -> pd.DataFrame:
    """Parse `nvidia-smi --query-gpu=index,uuid,pci.bus_id --format=csv` → columns index, uuid, bdf."""
    # TODO: skip the header; split on commas; normalize the BDF.
    raise NotImplementedError("parse_gpu_inventory")


def parse_lspci_vmm(text: str) -> dict:
    """Parse `lspci -D -vmm` blocks → {bdf: {"slot": int|None, "numa": int|None, "device": str}}."""
    # TODO: blocks are separated by blank lines; 'Key:<TAB>value' per line.
    raise NotImplementedError("parse_lspci_vmm")


def parse_ibdev2netdev(text: str) -> dict:
    """'mlx5_0 port 1 ==> enp13s0np0 (Up)' → {"mlx5_0": "enp13s0np0"}."""
    # TODO: one regex over the text.
    raise NotImplementedError("parse_ibdev2netdev")


def parse_lldp(text: str) -> dict:
    """`lldpcli show neighbors -f keyvalue` → {netdev: {"chassis": str, "port": str}}."""
    # TODO: keys look like lldp.<netdev>.chassis.name=<value> and lldp.<netdev>.port.ifname=<value>.
    raise NotImplementedError("parse_lldp")


def rail_from_chassis(name: str | None) -> int | None:
    """'orion-be-leaf-r3' → 3; anything else (frontend leaves) → None."""
    # TODO: regex on the canonical backend leaf name orion-be-leaf-r<R>.
    raise NotImplementedError("rail_from_chassis")


def parse_gdr(text: str) -> dict:
    """Parse gdr_prereqs.txt → {"peermem": bool, "iommu_passthrough": bool, "iommu_enabled": bool,
    "acs_redirect_ports": [bdf...], "driver": str, "ofed": str}."""
    # TODO: split into '### <command>' sections; inspect lsmod, /proc/cmdline, ACSCtl lines, versions.
    raise NotImplementedError("parse_gdr")


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
    # TODO: parse every file, build the compute-NIC table with _nic_table(), then one mapping row per GPU
    #       (see build_mapping for the columns and the nearest-NIC tie-break rule).
    raise NotImplementedError("load_host")


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
    # TODO: implement each rule in the docstring; one NIC_SHARED finding per shared NIC.
    raise NotImplementedError("detect_issues")


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
    # TODO: for each node in order, assign each GPU a NIC per policy; count sharers per (node, NIC).
    raise NotImplementedError("make_rank_map")


def path_params(row: dict, params: dict) -> tuple[float, float]:
    """(mean GB/s, cv) for one rank's GPU→NIC path: class value, then ACS factor, then host-staging cap
    (applied when row["host_staged"] is true OR the relation is farther than params["gdr_max_relation"],
    the NCCL_NET_GDR_LEVEL distance gate), then division by the number of GPUs sharing the NIC."""
    # TODO: class mean/cv, then ACS factor and cv_add, then host-staged cap and cv_add, then / sharers.
    raise NotImplementedError("path_params")


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
    # TODO: sample with the exact RNG call in the docstring (so results are reproducible), compute per-ring
    #       times, take the max, add alpha, and summarise.
    raise NotImplementedError("model_allreduce")


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
      S5_scheduled_pxn        same nodes, policy pxn
      S4_gdr_level_sys        S4 with gdr_max_relation = SYS (what NCCL_NET_GDR_LEVEL=SYS would do)
    (orion-n23 failed node acceptance with a blocker and is not schedulable.)
    Returns {"mappings": {host: df}, "issues": [..], "scenarios": {name: model result}}.
    """
    d = Path(data_dir)
    params = yaml.safe_load((d / "path_model.yaml").read_text(encoding="utf-8"))
    hosts = {p.name: load_host(p) for p in sorted((d / "hosts").iterdir()) if p.is_dir()}
    issues = [i for h in hosts.values() for i in detect_issues(h)]
    good = hosts["orion-n01"]
    sched = [good] * 30 + [hosts["orion-n02"], hosts["orion-n17"]]
    scenarios = {
        "S1_aligned_healthy": model_allreduce(make_rank_map([good] * 32, "aligned"), params),
        "S2_cross_socket_healthy": model_allreduce(make_rank_map([good] * 32, "cross_socket"), params),
        "S3_scheduled_nearest": model_allreduce(make_rank_map(sched, "nearest"), params),
        "S4_scheduled_aligned": model_allreduce(make_rank_map(sched, "aligned"), params),
    }
    return {"mappings": {k: v.mapping for k, v in hosts.items()}, "issues": issues, "scenarios": scenarios}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", type=Path, default=Path(__file__).resolve().parents[1] / "data")
    ap.add_argument("--out", type=Path, default=Path("gpu_nic_mapping.csv"))
    args = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    a = analyze(args.data)
    write_mapping_csv(pd.concat(a["mappings"].values(), ignore_index=True), args.out)
    print(f"mapping written to {args.out}")
    for i in a["issues"]:
        print(f"[{i['severity']:7}] {i['host']} {i['code']}: {i['detail']}")
    print("\nScenario (1 GiB all-reduce, 256 ranks)        median ms   p99 ms   busbw GB/s   CV   [MODELED]")
    for k, v in a["scenarios"].items():
        print(f"{k:42} {v['median_ms']:9.2f} {v['p99_ms']:8.2f} {v['busbw_median_GBps']:11.1f} {v['cv']:6.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
