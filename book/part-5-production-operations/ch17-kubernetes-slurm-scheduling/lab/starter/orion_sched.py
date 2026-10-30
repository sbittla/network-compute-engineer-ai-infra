"""ORION topology-aware gang scheduler simulator and pending-job diagnoser (STARTER — complete the TODOs).

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
# Helpers (provided — no changes needed)
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
    # TODO 1: loop over taints; skip effects other than NoSchedule/NoExecute.
    # TODO 1: a taint is tolerated if ANY toleration matches key, value (unless operator Exists), effect.
    raise NotImplementedError("tolerates: TODO")


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
    # TODO 2: apply the seven filters in the documented order and return the first failing code.
    raise NotImplementedError("node_filter: TODO")


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
    # TODO 3: implement the socket-aware best-fit selection described above (SOCKETS constant).
    raise NotImplementedError("select_gpus: TODO")


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
    # TODO 4: validate -> quota -> eligible nodes -> multi-node (whole nodes, rack-compact)
    #         or single-node (score = aligned, free_after, rail_complete, name) -> commit or pending.
    raise NotImplementedError("place_job: TODO")


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
    # TODO 5: loop: pick min key among remaining jobs, attempt with place_job, record the result.
    raise NotImplementedError("schedule: TODO")


# --------------------------------------------------------------------------------------------
# Task 6 — pending-despite-free-GPUs diagnoser
# --------------------------------------------------------------------------------------------
def _node_block_reason(node: dict, job: dict) -> str | None:
    """First failing check for one node in the diagnoser's fixed order (README Section 5.6)."""
    # TODO 6a: drained/cordoned -> resource not advertised (MIG vs device plugin) -> selector -> taint.
    raise NotImplementedError("_node_block_reason: TODO")


def diagnose_pending(case: dict) -> list[str]:
    """Return the sorted list of cause codes for a pending job's evidence bundle.

    Codes: QUOTA_EXHAUSTED, NODE_DRAINED, DEVICE_PLUGIN_NOT_ADVERTISING, MIG_PROFILE_MISMATCH,
    SELECTOR_MISMATCH, UNTOLERATED_TAINT, FRAGMENTATION; or ["NONE_FOUND"] if nothing explains it.
    """
    # TODO 6b: quota check; per-node block reasons for nodes with apparent free >= gpus_per_node;
    #          FRAGMENTATION rule; return sorted codes or ['NONE_FOUND'].
    raise NotImplementedError("diagnose_pending: TODO")


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
