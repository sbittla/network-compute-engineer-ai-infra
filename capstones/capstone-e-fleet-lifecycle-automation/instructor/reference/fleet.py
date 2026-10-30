"""Reference implementation — Capstone E fleet lifecycle automation (INSTRUCTOR ONLY).

Same public API as starter-kit/starter/fleet.py. Pure functions: no I/O except the loaders, no
global mutable state, no hardware access. Every decision returns machine-readable reasons so the
caller can write them to the audit trail.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

BUNDLE_FIELDS = ["os_image", "kernel", "gpu_driver", "gpu_vbios", "nic_fw", "rdma_stack", "bios", "bmc_fw"]
GENESIS = "0" * 64


# --------------------------------------------------------------------------- loaders (given)
def load_dataset(data_dir: Path) -> dict[str, Any]:
    """Load every file in data/ into plain Python structures (given; not a TODO)."""
    data_dir = Path(data_dir)
    with open(data_dir / "inventory.csv", encoding="utf-8") as fh:
        inventory = list(csv.DictReader(fh))
    with open(data_dir / "compat_matrix.csv", encoding="utf-8") as fh:
        matrix = list(csv.DictReader(fh))
    with open(data_dir / "acceptance_policy.yaml", encoding="utf-8") as fh:
        policy = yaml.safe_load(fh)
    with open(data_dir / "acceptance_results.json", encoding="utf-8") as fh:
        results = json.load(fh)
    with open(data_dir / "events.jsonl", encoding="utf-8") as fh:
        events = [json.loads(line) for line in fh if line.strip()]
    with open(data_dir / "rollout_constraints.yaml", encoding="utf-8") as fh:
        constraints = yaml.safe_load(fh)
    canary = pd.read_csv(data_dir / "canary_metrics.csv")
    with open(data_dir / "audit_log.jsonl", encoding="utf-8") as fh:
        audit = [json.loads(line) for line in fh if line.strip()]
    return {"inventory": inventory, "matrix": matrix, "policy": policy, "results": results,
            "events": events, "constraints": constraints, "canary": canary, "audit": audit}


def _utc(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")


# --------------------------------------------------------------------------- T1 state machine
def lifecycle_spec() -> dict[str, Any]:
    """Return the node lifecycle state machine.

    Returns a dict with:
      ``states``      list of state names
      ``initial``     the state a newly racked node enters
      ``terminal``    list of terminal states (no outgoing transitions)
      ``transitions`` {state: {event: [possible next states]}}; more than one target means the
                      transition is guarded and the guard picks the branch.
    """
    return {
        "states": ["discovered", "imaged", "validated", "schedulable", "drained", "repair", "retired"],
        "initial": "discovered",
        "terminal": ["retired"],
        "transitions": {
            "discovered": {"image_complete": ["imaged"]},
            "imaged": {"acceptance_complete": ["validated", "repair"]},
            "validated": {"admit": ["schedulable"], "drain": ["drained"]},
            "schedulable": {"drain": ["drained"]},
            "drained": {"undrain": ["schedulable"], "fault_confirmed": ["repair"],
                        "image_complete": ["imaged"], "retire": ["retired"]},
            "repair": {"image_complete": ["imaged"], "retire": ["retired"]},
            "retired": {},
        },
    }


# --------------------------------------------------------------------------- T2 acceptance
def evaluate_acceptance(result: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    """Evaluate one node's acceptance evidence against the policy.

    Returns ``{"node": str, "passed": bool, "failures": sorted list of check names}``. Check names:
    gpu_count, gpu_pcie_link, nic_pcie_link, nic_link_speed, ecc_uncorrected, row_remap, dcgm_diag,
    nvlink_bw, h2d_bw, rdma_bw, storage_bw, burn_in_duration, thermal, xid_events, evidence_freshness.
    Correctable ECC alone is NOT a failure (it is trended, not gated).
    """
    t = result["tests"]
    p = policy
    fails: set[str] = set()
    if t["gpu_count"] != p["expected_gpus"] or len(t["gpu_pcie"]) != p["expected_gpus"]:
        fails.add("gpu_count")
    if any(g["gen"] < p["pcie_min_gen"] or g["width"] < p["pcie_min_width"] for g in t["gpu_pcie"]):
        fails.add("gpu_pcie_link")
    if len(t["nic_pcie"]) != p["expected_nics"] or any(
            n["gen"] < p["pcie_min_gen"] or n["width"] < p["pcie_min_width"] for n in t["nic_pcie"]):
        fails.add("nic_pcie_link")
    if len(t["nic_link_gbps"]) != p["expected_nics"] or any(s != p["nic_link_gbps"] for s in t["nic_link_gbps"]):
        fails.add("nic_link_speed")
    if any(e > p["ecc_uncorrected_volatile_max"] for e in t["ecc_uncorrected_volatile"]):
        fails.add("ecc_uncorrected")
    if any(x > p["row_remap_pending_max"] for x in t["row_remap_pending"]) or any(
            x > p["row_remap_failure_max"] for x in t["row_remap_failure"]):
        fails.add("row_remap")
    if t["dcgm_diag_level3"] != p["dcgm_diag_required"]:
        fails.add("dcgm_diag")
    if t["nvlink_p2p_GBps_min"] < p["nvlink_p2p_GBps_min"]:
        fails.add("nvlink_bw")
    if t["h2d_GBps_min"] < p["h2d_GBps_min"]:
        fails.add("h2d_bw")
    if t["rdma_write_Gbps_min"] < p["rdma_write_Gbps_min"]:
        fails.add("rdma_bw")
    if t["storage_read_GBps"] < p["storage_read_GBps_min"]:
        fails.add("storage_bw")
    if t["burn_in_hours"] < p["burn_in_hours_min"]:
        fails.add("burn_in_duration")
    if t["gpu_temp_max_c"] > p["gpu_temp_max_c"]:
        fails.add("thermal")
    if len(t["xid_events"]) > p["xid_events_max"]:
        fails.add("xid_events")
    if _utc(result["started_utc"]) < _utc(result["image_completed_utc"]) or \
            _utc(result["completed_utc"]) < _utc(result["started_utc"]):
        fails.add("evidence_freshness")
    return {"node": result["node"], "passed": not fails, "failures": sorted(fails)}


# --------------------------------------------------------------------------- T3 compatibility
def check_compatibility(node: dict[str, str], matrix: list[dict[str, str]]) -> dict[str, Any]:
    """Classify a node's installed stack against the compatibility matrix.

    Returns ``{"status": golden|canary|deprecated|blocked|unknown|non_compliant,
               "bundle": bundle_id or None, "reasons": list[str]}``.

    * Mixed VBIOS across the 8 GPUs -> ``non_compliant`` (reason ``heterogeneous_vbios``) regardless
      of bundle match: a node must be internally uniform before it can match any bundle.
    * Exact match on every BUNDLE_FIELD -> that bundle's status.
    * No exact match -> ``unknown``; reasons name the fields that differ from the closest bundle
      as ``"<field>:<installed>!=<expected>"``.
    """
    vb = node["gpu_vbios"].split(";")
    if len(set(vb)) > 1:
        return {"status": "non_compliant", "bundle": None, "reasons": ["heterogeneous_vbios"]}
    installed = dict(node, gpu_vbios=vb[0])
    best: tuple[int, dict[str, str]] | None = None
    for b in matrix:
        diff = [f for f in BUNDLE_FIELDS if installed[f] != b[f]]
        if not diff:
            return {"status": b["status"], "bundle": b["bundle_id"], "reasons": []}
        # prefer non-blocked bundles as the "closest" explanation on ties
        key = (len(diff), b["status"] == "blocked")
        if best is None or key < best[0]:
            best = (key, b)  # type: ignore[assignment]
    assert best is not None
    b = best[1]
    reasons = [f"{f}:{installed[f]}!={b[f]}" for f in BUNDLE_FIELDS if installed[f] != b[f]]
    return {"status": "unknown", "bundle": None, "reasons": reasons}


# --------------------------------------------------------------------------- T4 events
ADMIT_OK = {"golden"}
UNDRAIN_OK = {"golden", "deprecated"}


def apply_event(state: str, event: str, node: str, ctx: dict[str, Any]) -> tuple[str, str, str]:
    """Apply one lifecycle event to one node.

    ``ctx`` holds ``acceptance`` ({node: evaluate_acceptance result}) and ``compat``
    ({node: check_compatibility result}).

    Returns ``(new_state, outcome, reason)`` with outcome in {"applied", "noop", "rejected"}.
    Rules: an event whose only target equals the current state is an idempotent ``noop``; an event
    not allowed from ``state`` is ``rejected``; guards: ``acceptance_complete`` branches on the
    acceptance verdict (missing evidence -> repair), ``admit`` requires acceptance passed AND compat
    status golden, ``undrain`` requires compat status golden or deprecated.
    """
    spec = lifecycle_spec()["transitions"]
    allowed = spec.get(state, {})
    if event not in allowed:
        # Idempotency: the requested end state already holds (e.g. drain on a drained node).
        targets = {t for s in spec.values() for e, ts in s.items() if e == event for t in ts}
        if targets == {state}:
            return state, "noop", f"already {state}"
        return state, "rejected", f"illegal transition: {event} from {state}"
    if event == "acceptance_complete":
        verdict = ctx.get("acceptance", {}).get(node)
        if verdict is None:
            return "repair", "applied", "no acceptance evidence"
        if verdict["passed"]:
            return "validated", "applied", "acceptance passed"
        return "repair", "applied", "acceptance failed: " + ",".join(verdict["failures"])
    if event == "admit":
        verdict = ctx.get("acceptance", {}).get(node)
        comp = ctx.get("compat", {}).get(node, {"status": "unknown", "reasons": ["no compat record"]})
        if verdict is None or not verdict["passed"]:
            return state, "rejected", "guard: acceptance not passed"
        if comp["status"] not in ADMIT_OK:
            return state, "rejected", f"guard: compat {comp['status']} " + ",".join(comp["reasons"])
        return "schedulable", "applied", "admitted"
    if event == "undrain":
        comp = ctx.get("compat", {}).get(node, {"status": "unknown", "reasons": []})
        if comp["status"] not in UNDRAIN_OK:
            return state, "rejected", f"guard: compat {comp['status']}"
        return "schedulable", "applied", "returned to service"
    return allowed[event][0], "applied", event


def replay(states: dict[str, str], events: list[dict[str, Any]], ctx: dict[str, Any]
           ) -> tuple[dict[str, str], list[dict[str, Any]]]:
    """Replay events in (utc, event_id) order; deliver each event_id at most once.

    Returns ``(final_states, journal)``. ``journal`` has one entry per input event (in processing
    order) with keys event_id, node, event, from_state, to_state, outcome, reason; duplicates have
    outcome ``duplicate``. Input ``states`` is not mutated.
    """
    cur = dict(states)
    seen: set[str] = set()
    journal: list[dict[str, Any]] = []
    for e in sorted(events, key=lambda x: (x["utc"], x["event_id"])):
        frm = cur.get(e["node"], "discovered")
        if e["event_id"] in seen:
            journal.append({**_j(e), "from_state": frm, "to_state": frm, "outcome": "duplicate",
                            "reason": "event_id already processed"})
            continue
        seen.add(e["event_id"])
        new, outcome, reason = apply_event(frm, e["event"], e["node"], ctx)
        cur[e["node"]] = new
        journal.append({**_j(e), "from_state": frm, "to_state": new, "outcome": outcome, "reason": reason})
    return cur, journal


def _j(e: dict[str, Any]) -> dict[str, Any]:
    return {"event_id": e["event_id"], "utc": e["utc"], "node": e["node"], "event": e["event"],
            "actor": e.get("actor", ""), "ticket": e.get("ticket", "")}


# --------------------------------------------------------------------------- T5 rollout waves
def plan_waves(nodes: list[dict[str, str]], constraints: dict[str, Any]) -> list[list[str]]:
    """Plan canary + rollout waves for the target bundle, protecting each partition's capacity.

    ``nodes``: dicts with node, rack, partition (``training``/``inference``/…), state, compat_status.
    Eligible nodes: state in ``eligible_states`` and compat_status in ``eligible_compat``.

    Capacity floors are per partition (``partition_floors``). A partition's headroom per wave is
    (schedulable nodes that will stay in service) − floor, where a schedulable node whose
    compat_status is NOT eligible is excluded because the remediation plan (T7) drains it. Raise
    ValueError when a partition with eligible nodes has headroom < 1.

    Wave 0 is the canary: ``canary_size`` nodes on distinct racks, one per partition first. Every
    wave holds at most ``max_nodes_per_rack_per_wave`` per rack, at most the partition headroom per
    partition and at most floor(max_wave_fraction × eligible) nodes. Nodes whose compat_status is in
    ``prefer_first`` (e.g. an expiring bundle) go first. Racks with the most remaining nodes are served
    first (after racks holding preferred nodes), which reaches the minimum wave count the rack and
    partition limits allow. Every eligible
    node appears exactly once. Deterministic.
    """
    good = set(constraints["eligible_compat"])
    floors = constraints.get("partition_floors", {})
    per_rack = constraints["max_nodes_per_rack_per_wave"]
    eligible = [n for n in nodes if n["state"] in constraints["eligible_states"] and n["compat_status"] in good]
    staying: dict[str, int] = {}
    for n in nodes:
        if n["state"] == "schedulable" and n["compat_status"] in good:
            staying[n["partition"]] = staying.get(n["partition"], 0) + 1
    parts = sorted({n["partition"] for n in eligible})
    head = {p: staying.get(p, 0) - floors.get(p, 0) for p in parts}
    short = [p for p in parts if head[p] < 1]
    if short:
        raise ValueError(f"no drain headroom in partition(s) {short}: cannot roll out safely")
    total_cap = math.floor(constraints["max_wave_fraction"] * len(eligible))
    if total_cap < 1:
        raise ValueError("max_wave_fraction leaves no room for a wave")
    prefer = set(constraints.get("prefer_first", []))
    key = lambda n: (0 if n["compat_status"] in prefer else 1, n["node"])  # noqa: E731
    remaining = sorted(eligible, key=key)

    canary: list[dict[str, str]] = []
    racks: set[str] = set()
    for p in parts:  # one per partition first
        n = next((x for x in remaining if x["partition"] == p and x["rack"] not in racks), None)
        if n is not None and len(canary) < constraints["canary_size"]:
            canary.append(n)
            racks.add(n["rack"])
    for n in remaining:
        if len(canary) >= constraints["canary_size"]:
            break
        if n not in canary and n["rack"] not in racks and                 sum(1 for c in canary if c["partition"] == n["partition"]) < head[n["partition"]]:
            canary.append(n)
            racks.add(n["rack"])
    waves = [[n["node"] for n in canary]]
    remaining = [n for n in remaining if n not in canary]
    while remaining:
        by_rack: dict[str, list[dict[str, str]]] = {}
        for n in remaining:
            by_rack.setdefault(n["rack"], []).append(n)
        wave: list[dict[str, str]] = []
        used: dict[str, int] = {}
        for rack in sorted(by_rack, key=lambda r: (key(by_rack[r][0])[0], -len(by_rack[r]), r)):
            if len(wave) >= total_cap:
                break
            taken = 0
            for n in by_rack[rack]:
                if taken >= per_rack:
                    break
                if used.get(n["partition"], 0) < head[n["partition"]]:
                    wave.append(n)
                    used[n["partition"]] = used.get(n["partition"], 0) + 1
                    taken += 1
        if not wave:
            raise ValueError("constraints admit no further wave")
        waves.append([n["node"] for n in wave])
        remaining = [n for n in remaining if n not in wave]
    return waves


# --------------------------------------------------------------------------- T6 canary gate
def canary_decision(metrics: pd.DataFrame, thresholds: dict[str, Any]) -> tuple[str, list[str]]:
    """Decide promote / abort / extend for ONE scenario's soak metrics.

    Each canary is compared with the mean of the baseline nodes **in its own partition** (training
    canaries also report training step time; inference canaries report serving TPOT p95). Metrics
    that are empty for a partition are skipped. Regressions: bandwidth (base − canary)/base × 100;
    step time and TPOT (canary − base)/base × 100. The WORST canary is gated — never a mean across
    canaries. Precedence: abort (any hard failure) > extend (soak shorter than ``min_soak_hours``) >
    promote. Returns (decision, sorted reasons).
    """
    th = thresholds
    checks = [("nccl_busbw_GBps", -1, "max_busbw_regression_pct", "busbw"),
              ("ib_write_Gbps", -1, "max_ib_bw_regression_pct", "ib_write"),
              ("step_time_s", 1, "max_step_time_regression_pct", "step_time"),
              ("tpot_p95_ms", 1, "max_tpot_regression_pct", "tpot_p95")]
    can = metrics[metrics["role"] == "canary"]
    if can.empty:
        return "abort", ["missing canary rows"]
    reasons: list[str] = []
    for _, r in can.iterrows():
        n = r["node"]
        base = metrics[(metrics["role"] == "baseline") & (metrics["partition"] == r["partition"])]
        if base.empty:
            reasons.append(f"{n}: no baseline in partition {r['partition']}")
            continue
        if int(r["xid_events"]) > th["max_xid_events"]:
            reasons.append(f"{n}: xid_events={int(r['xid_events'])}")
        if r["dcgm_diag"] != th["dcgm_diag_required"]:
            reasons.append(f"{n}: dcgm_diag={r['dcgm_diag']}")
        for col, sign, key, label in checks:
            b = pd.to_numeric(base[col], errors="coerce").mean()
            v = pd.to_numeric(pd.Series([r[col]]), errors="coerce").iloc[0]
            if pd.isna(b) or pd.isna(v):
                continue
            reg = (v - b) / b * 100 * sign
            if reg > th[key]:
                reasons.append(f"{n}: {label} regression {reg:.1f}%")
    if reasons:
        return "abort", sorted(reasons)
    short = [f"{r['node']}: soak {float(r['soak_hours']):.0f} h < {th['min_soak_hours']} h"
             for _, r in can.iterrows() if float(r["soak_hours"]) < th["min_soak_hours"]]
    if short:
        return "extend", sorted(short)
    return "promote", []


# --------------------------------------------------------------------------- T7 remediation
def plan_remediation(inventory: list[dict[str, str]], matrix: list[dict[str, str]],
                     golden_bundle: str) -> list[dict[str, str]]:
    """Produce an idempotent remediation plan (a desired-state diff), sorted by node then step.

    For nodes in state schedulable/validated/drained:
      * blocked / unknown / non_compliant  -> if schedulable: ``drain`` then ``reimage``; else ``reimage``
      * deprecated                         -> ``schedule_upgrade`` (no drain now; upgrade in a wave)
      * golden / canary                    -> nothing
    Nodes in discovered/imaged/repair/retired are owned by the lifecycle flow and get no action.
    Each action: {node, step (int), action, target_bundle, reason}. A converged fleet yields [].
    """
    plan: list[dict[str, str]] = []
    for row in sorted(inventory, key=lambda r: r["node"]):
        if row["state"] not in ("schedulable", "validated", "drained"):
            continue
        c = check_compatibility(row, matrix)
        reason = c["status"] + (":" + ",".join(c["reasons"]) if c["reasons"] else "")
        if c["status"] in ("blocked", "unknown", "non_compliant"):
            step = 1
            if row["state"] == "schedulable":
                plan.append({"node": row["node"], "step": step, "action": "drain",
                             "target_bundle": golden_bundle, "reason": reason})
                step += 1
            plan.append({"node": row["node"], "step": step, "action": "reimage",
                         "target_bundle": golden_bundle, "reason": reason})
        elif c["status"] == "deprecated":
            plan.append({"node": row["node"], "step": 1, "action": "schedule_upgrade",
                         "target_bundle": golden_bundle, "reason": reason})
    return plan


# --------------------------------------------------------------------------- T8 audit trail
def _canon(d: dict[str, Any]) -> str:
    return json.dumps(d, sort_keys=True, separators=(",", ":"))


def record_hash(record: dict[str, Any]) -> str:
    """SHA-256 hex of the canonical JSON of ``record`` without its ``hash`` key."""
    body = {k: v for k, v in record.items() if k != "hash"}
    return hashlib.sha256(_canon(body).encode()).hexdigest()


def audit_append(chain: list[dict[str, Any]], entry: dict[str, Any]) -> list[dict[str, Any]]:
    """Return a NEW chain with ``entry`` appended (input not mutated).

    Sets ``seq`` (previous seq + 1, starting at 1), ``prev_hash`` (previous record's hash or 64 zeros)
    and ``hash`` = record_hash(record).
    """
    rec = dict(entry)
    rec["seq"] = chain[-1]["seq"] + 1 if chain else 1
    rec["prev_hash"] = chain[-1]["hash"] if chain else GENESIS
    rec.pop("hash", None)
    rec["hash"] = record_hash(rec)
    return [*chain, rec]


def audit_verify(chain: list[dict[str, Any]]) -> int | None:
    """Return the ``seq`` of the first record that breaks the chain, or None if intact.

    A record breaks the chain if its hash does not match its content, its prev_hash does not equal
    the previous record's hash (genesis: 64 zeros), or its seq is not previous seq + 1.
    """
    prev_hash, prev_seq = GENESIS, 0
    for rec in chain:
        if rec.get("hash") != record_hash(rec) or rec.get("prev_hash") != prev_hash or rec.get("seq") != prev_seq + 1:
            return rec.get("seq", prev_seq + 1)
        prev_hash, prev_seq = rec["hash"], rec["seq"]
    return None
