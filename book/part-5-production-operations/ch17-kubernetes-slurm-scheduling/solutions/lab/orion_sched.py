"""ORION topology-aware gang scheduler simulator and pending-job diagnoser (REFERENCE SOLUTION).

Chapter 17 lab (Progressive Lab 7, part 2). Level 1: pure Python, no cluster, no GPU.

Two tools live in this module:

1. A policy simulator that places a queue of GPU jobs onto a snapshot of the ORION-256 cluster,
   honouring gang (all-or-nothing) semantics, node lifecycle/health, pools, node selectors,
   taints/tolerations, MIG partitioning, rail completeness for multi-node jobs, tenant GPU quotas,
   priority, and a dynamic fair-share ordering. Units: GPUs are whole physical GPUs; time is seconds
   since the snapshot epoch.
2. A diagnoser that, given an evidence bundle for a job that is pending "despite free GPUs", returns
   the set of cause codes that explain why the apparently free GPUs are not usable.

The algorithm is specified exactly in lab/README.md, Section 5; this file implements that spec.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

GPUS_PER_NODE = 8
SOCKETS: tuple[tuple[int, ...], ...] = ((0, 1, 2, 3), (4, 5, 6, 7))  # HX8: GPU0-3 on NUMA 0, GPU4-7 on NUMA 1
BLOCKING_EFFECTS = {"NoSchedule", "NoExecute"}
UNAVAILABLE_SLURM_STATES = {"DRAIN", "DRAINING", "DRAINED", "DOWN", "FAIL", "MAINT"}


# --------------------------------------------------------------------------------------------
# Helpers (provided in the starter as well)
# --------------------------------------------------------------------------------------------
def load_json(path: str | Path) -> Any:
    """Load a JSON file (UTF-8)."""
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def rack_key(rack: str) -> int:
    """Numeric sort key for rack names like 'rack-06'."""
    return int(rack.rsplit("-", 1)[1])


# --------------------------------------------------------------------------------------------
# Task 1 — taint/toleration matching
# --------------------------------------------------------------------------------------------
def tolerates(taints: list[dict], tolerations: list[dict]) -> bool:
    """Return True if every *blocking* taint (effect NoSchedule or NoExecute) is tolerated.

    A toleration matches a taint when the keys are equal and either the toleration operator is
    "Exists" or the values are equal, and the toleration effect is empty or equal to the taint
    effect. Taints with effect PreferNoSchedule never block placement.
    """
    for taint in taints:
        if taint.get("effect") not in BLOCKING_EFFECTS:
            continue
        matched = False
        for tol in tolerations:
            if tol.get("key") != taint.get("key"):
                continue
            if tol.get("operator", "Equal") != "Exists" and tol.get("value") != taint.get("value"):
                continue
            if tol.get("effect") and tol.get("effect") != taint.get("effect"):
                continue
            matched = True
            break
        if not matched:
            return False
    return True


# --------------------------------------------------------------------------------------------
# Task 2 — node eligibility filter
# --------------------------------------------------------------------------------------------
def node_filter(node: dict, job: dict, multi_node: bool) -> str | None:
    """Return the first failing filter code for placing ``job`` on ``node``, or None if eligible.

    Filters, in this exact order:
      NotSchedulable   lifecycle_state != "schedulable" (Chapter 16 state machine)
      Unhealthy        health == "failed"
      PoolMismatch     node label halcyon.ai/pool != job["pool"]
      SelectorMismatch any job node_selector key/value not present in node labels
      UntoleratedTaint a NoSchedule/NoExecute taint not tolerated by the job
      MIGEnabled       node has MIG enabled (job asks for whole GPUs)
      RailIncomplete   multi_node and fewer than 8 backend rails up
    """
    if node.get("lifecycle_state") != "schedulable":
        return "NotSchedulable"
    if node.get("health") == "failed":
        return "Unhealthy"
    labels = node.get("labels", {})
    if labels.get("halcyon.ai/pool") != job.get("pool"):
        return "PoolMismatch"
    for key, value in job.get("node_selector", {}).items():
        if labels.get(key) != value:
            return "SelectorMismatch"
    if not tolerates(node.get("taints", []), job.get("tolerations", [])):
        return "UntoleratedTaint"
    if node.get("mig_enabled"):
        return "MIGEnabled"
    if multi_node and len(node.get("rails_up", [])) < GPUS_PER_NODE:
        return "RailIncomplete"
    return None


# --------------------------------------------------------------------------------------------
# Task 3 — socket-aware GPU selection inside one node
# --------------------------------------------------------------------------------------------
def select_gpus(free: list[int] | set[int], n: int) -> tuple[list[int], bool] | None:
    """Choose ``n`` GPU indices from ``free`` on one HX8 node.

    Returns (indices sorted ascending, socket_aligned) or None if len(free) < n.
      * n == 8: all eight GPUs; aligned=True.
      * n <= 4: among sockets with >= n free GPUs pick the one with the FEWEST free GPUs
        (best fit; tie -> lower socket) and take its lowest n indices; aligned=True.
        If no single socket fits, take the lowest n free indices; aligned=False.
      * 5 <= n <= 7: lowest n free indices; aligned=True (spanning sockets is unavoidable).
    """
    free_sorted = sorted(free)
    if len(free_sorted) < n:
        return None
    if n == GPUS_PER_NODE:
        return free_sorted, True
    if n <= 4:
        fits = []
        for s_idx, socket in enumerate(SOCKETS):
            s_free = [g for g in free_sorted if g in socket]
            if len(s_free) >= n:
                fits.append((len(s_free), s_idx, s_free))
        if fits:
            fits.sort()
            return fits[0][2][:n], True
        return free_sorted[:n], False
    return free_sorted[:n], True


# --------------------------------------------------------------------------------------------
# Task 4 — place one job (gang, all-or-nothing)
# --------------------------------------------------------------------------------------------
def place_job(state: dict, job: dict) -> dict:
    """Try to place ``job`` on ``state``; mutate state only if the whole gang fits.

    ``state`` = {"nodes": {name: node_dict_with_"free": set[int]}, "tenants": {t: {"quota", "used"}}}.
    Returns {"status": "placed", "nodes": {name: [gpu indices]}, "socket_aligned": bool}
         or {"status": "pending", "reason": code} with code in
         InvalidRequest | QuotaExceeded | NoEligibleNodes | Fragmentation | InsufficientCapacity.
    Checks run in that order. See lab/README.md Section 5 for scoring rules.
    """
    gpus = int(job["gpus"])
    if gpus < 1 or (gpus > GPUS_PER_NODE and gpus % GPUS_PER_NODE != 0):
        return {"status": "pending", "reason": "InvalidRequest"}
    tenant = state["tenants"][job["tenant"]]
    if tenant["used"] + gpus > tenant["quota"]:
        return {"status": "pending", "reason": "QuotaExceeded"}

    multi = gpus > GPUS_PER_NODE
    eligible = [n for n in state["nodes"].values() if node_filter(n, job, multi) is None]
    if not eligible:
        return {"status": "pending", "reason": "NoEligibleNodes"}
    total_free = sum(len(n["free"]) for n in eligible)

    if multi:
        need = gpus // GPUS_PER_NODE
        whole = [n for n in eligible if len(n["free"]) == GPUS_PER_NODE]
        if len(whole) < need:
            reason = "Fragmentation" if total_free >= gpus else "InsufficientCapacity"
            return {"status": "pending", "reason": reason}
        by_rack: dict[str, list[dict]] = {}
        for n in whole:
            by_rack.setdefault(n["rack"], []).append(n)
        racks = sorted(by_rack, key=lambda r: (-len(by_rack[r]), rack_key(r)))
        chosen: list[dict] = []
        for r in racks:
            for n in sorted(by_rack[r], key=lambda x: x["name"]):
                if len(chosen) < need:
                    chosen.append(n)
        placement = {n["name"]: sorted(n["free"]) for n in chosen}
        aligned = True
    else:
        candidates = []
        for n in eligible:
            sel = select_gpus(n["free"], gpus)
            if sel is None:
                continue
            idx, aligned_n = sel
            rail_complete = len(n.get("rails_up", [])) == GPUS_PER_NODE
            score = (0 if aligned_n else 1, len(n["free"]) - gpus, 1 if rail_complete else 0, n["name"])
            candidates.append((score, n, idx, aligned_n))
        if not candidates:
            reason = "Fragmentation" if total_free >= gpus else "InsufficientCapacity"
            return {"status": "pending", "reason": reason}
        candidates.sort(key=lambda c: c[0])
        _, best, idx, aligned = candidates[0]
        placement = {best["name"]: idx}

    for name, idx in placement.items():
        state["nodes"][name]["free"] -= set(idx)
    tenant["used"] += gpus
    return {"status": "placed", "nodes": placement, "socket_aligned": aligned}


# --------------------------------------------------------------------------------------------
# Task 5 — whole-queue scheduling with priority and dynamic fair share
# --------------------------------------------------------------------------------------------
def build_state(cluster: dict) -> dict:
    """Build the mutable scheduler state from a cluster snapshot (running jobs already applied)."""
    nodes = {}
    for n in cluster["nodes"]:
        node = dict(n)
        node["free"] = set(range(GPUS_PER_NODE)) - set(n.get("gpus_allocated", []))
        nodes[n["name"]] = node
    tenants = {t: {"quota": v["gpu_quota"], "used": 0} for t, v in cluster["tenants"].items()}
    for r in cluster.get("running", []):
        tenants[r["tenant"]]["used"] += sum(len(v) for v in r["nodes"].values())
    return {"nodes": nodes, "tenants": tenants}


def schedule(cluster: dict, jobs: list[dict]) -> dict:
    """Schedule the whole queue; return {"order", "results", "tenant_used"}.

    Each iteration picks, among not-yet-attempted jobs, the minimum of
    (-priority, round(used/quota of the job's tenant, 6), submit_time, job_id), attempts it once
    with place_job, and records the result. Shares are recomputed after every placement.
    """
    state = build_state(cluster)
    remaining = list(jobs)
    order: list[str] = []
    results: dict[str, dict] = {}

    def key(j: dict) -> tuple:
        t = state["tenants"][j["tenant"]]
        return (-int(j["priority"]), round(t["used"] / t["quota"], 6), j["submit_time"], j["job_id"])

    while remaining:
        job = min(remaining, key=key)
        remaining.remove(job)
        order.append(job["job_id"])
        results[job["job_id"]] = place_job(state, job)
    return {
        "order": order,
        "results": results,
        "tenant_used": {t: v["used"] for t, v in sorted(state["tenants"].items())},
    }


# --------------------------------------------------------------------------------------------
# Task 6 — pending-despite-free-GPUs diagnoser
# --------------------------------------------------------------------------------------------
def _node_block_reason(node: dict, job: dict) -> str | None:
    """First failing check for one node in the diagnoser's fixed order (README Section 5.6)."""
    resource = job.get("resource", "nvidia.com/gpu")
    if (not node.get("schedulable", True)
            or node.get("slurm_state", "").upper().rstrip("*~#") in UNAVAILABLE_SLURM_STATES
            or node.get("lifecycle_state", "schedulable") != "schedulable"):
        return "NODE_DRAINED"
    if node.get("allocatable", {}).get(resource, 0) == 0 and node.get("physical_gpus", 0) > 0:
        if any(k.startswith("nvidia.com/mig-") and v > 0 for k, v in node.get("allocatable", {}).items()):
            return "MIG_PROFILE_MISMATCH"
        return "DEVICE_PLUGIN_NOT_ADVERTISING"
    labels = node.get("labels", {})
    for key, value in job.get("node_selector", {}).items():
        if labels.get(key) != value:
            return "SELECTOR_MISMATCH"
    if not tolerates(node.get("taints", []), job.get("tolerations", [])):
        return "UNTOLERATED_TAINT"
    return None


def diagnose_pending(case: dict) -> list[str]:
    """Return the sorted list of cause codes for a pending job's evidence bundle.

    Codes: QUOTA_EXHAUSTED, NODE_DRAINED, DEVICE_PLUGIN_NOT_ADVERTISING, MIG_PROFILE_MISMATCH,
    SELECTOR_MISMATCH, UNTOLERATED_TAINT, FRAGMENTATION; or ["NONE_FOUND"] if nothing explains it.
    """
    job = case["job"]
    resource = job.get("resource", "nvidia.com/gpu")
    per_node = int(job["gpus_per_node"])
    total = per_node * int(job["nodes"])
    causes: set[str] = set()

    quota = case.get("quota")
    if quota and quota["used"] + total > quota["hard"]:
        causes.add("QUOTA_EXHAUSTED")

    eligible_free: list[int] = []
    for node in case["nodes"]:
        allocated = node.get("allocated", {}).get(resource, 0)
        apparent_free = node.get("physical_gpus", 0) - allocated
        reason = _node_block_reason(node, job)
        if reason is None:
            eligible_free.append(node.get("allocatable", {}).get(resource, 0) - allocated)
        elif apparent_free >= per_node:
            causes.add(reason)

    if sum(eligible_free) >= total and sum(1 for f in eligible_free if f >= per_node) < int(job["nodes"]):
        causes.add("FRAGMENTATION")
    return sorted(causes) if causes else ["NONE_FOUND"]


if __name__ == "__main__":
    import argparse

    here = Path(__file__).resolve().parent
    default_data = here.parents[1] / "lab" / "data"
    ap = argparse.ArgumentParser(description="Run the ORION scheduler simulator and diagnoser.")
    ap.add_argument("--data", default=str(default_data), help="directory with cluster_state.json etc.")
    args = ap.parse_args()
    d = Path(args.data)
    out = schedule(load_json(d / "cluster_state.json"), load_json(d / "job_queue.json"))
    for jid in out["order"]:
        r = out["results"][jid]
        detail = r.get("nodes") if r["status"] == "placed" else r["reason"]
        print(f"{jid:6s} {r['status']:8s} {detail}")
    print("tenant_used", out["tenant_used"])
    for case in load_json(d / "pending_cases.json"):
        print(case["case_id"], diagnose_pending(case))
