"""Capstone E starter module — bare-metal GPU fleet lifecycle automation.

Implement every function marked TODO. The loaders, constants and ``record_hash()`` are given.
Run ``python check.py`` from starter-kit/ to see which checks pass. Read starter-kit/README.md
for the task list and acceptance criteria.

Design rules (they are graded):
  * pure functions: no file writes, no global mutable state, no hardware access
  * every decision returns machine-readable reasons (they feed the audit trail)
  * thresholds come from the data files, never hard-coded
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
    # TODO: include the seven outline states: discovered, imaged, validated, schedulable, drained, repair, retired
    # TODO: decide which events move a node between them (image_complete, acceptance_complete, admit, drain, undrain, fault_confirmed, retire)
    # TODO: a node must never reach schedulable without passing through validated, and repair must never lead directly to schedulable
    # TODO: jobs run on schedulable nodes: fault_confirmed and retire must require a drained (or repair) node first
    # TODO: retired is terminal: no outgoing transitions
    raise NotImplementedError("TODO: implement lifecycle_spec()")


# --------------------------------------------------------------------------- T2 acceptance
def evaluate_acceptance(result: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    """Evaluate one node's acceptance evidence against the policy.

    Returns ``{"node": str, "passed": bool, "failures": sorted list of check names}``. Check names:
    gpu_count, gpu_pcie_link, nic_pcie_link, nic_link_speed, ecc_uncorrected, row_remap, dcgm_diag,
    nvlink_bw, h2d_bw, rdma_bw, storage_bw, burn_in_duration, thermal, xid_events, evidence_freshness.
    Correctable ECC alone is NOT a failure (it is trended, not gated).
    """
    # TODO: implement one comparison per check name listed above, reading thresholds only from `policy`
    # TODO: count GPUs/NICs from BOTH the count field and the per-device lists (a missing device shortens the list)
    # TODO: evidence_freshness: the test must have started after image_completed_utc and completed after it started
    # TODO: think carefully about which ECC counters gate admission and which are only trended
    raise NotImplementedError("TODO: implement evaluate_acceptance()")


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
    # TODO: split gpu_vbios on ';' - all eight GPUs must match each other first
    # TODO: compare every field in BUNDLE_FIELDS; an exact match returns that bundle's status
    # TODO: otherwise return unknown with '<field>:<installed>!=<expected>' reasons against the closest bundle
    raise NotImplementedError("TODO: implement check_compatibility()")


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
    # TODO: look up allowed events for `state` in lifecycle_spec()
    # TODO: idempotency: if the event's only possible target is the current state, return noop (not rejected)
    # TODO: implement the guards for acceptance_complete, admit and undrain described above
    # TODO: never raise for bad input from the event stream: reject with a reason
    raise NotImplementedError("TODO: implement apply_event()")


def replay(states: dict[str, str], events: list[dict[str, Any]], ctx: dict[str, Any]
           ) -> tuple[dict[str, str], list[dict[str, Any]]]:
    """Replay events in (utc, event_id) order; deliver each event_id at most once.

    Returns ``(final_states, journal)``. ``journal`` has one entry per input event (in processing
    order) with keys event_id, node, event, from_state, to_state, outcome, reason; duplicates have
    outcome ``duplicate``. Input ``states`` is not mutated.
    """
    # TODO: sort by (utc, event_id) - the file is NOT in time order
    # TODO: deliver each event_id at most once (the queue is at-least-once); record duplicates in the journal
    # TODO: do not mutate the caller's `states` dict
    raise NotImplementedError("TODO: implement replay()")


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
    # TODO: compute headroom per PARTITION: schedulable nodes that stay in service minus that partition's floor; a non-compliant schedulable node is about to be drained by T7, so it does not count
    # TODO: wave 0 = canary on distinct racks, one per partition first; later waves respect the per-rack and per-partition limits
    # TODO: upgrade expiring-bundle nodes (prefer_first) first; serve racks with the most remaining nodes first to reach the minimum number of waves
    # TODO: refuse (raise ValueError) if any partition with eligible nodes has no headroom
    raise NotImplementedError("TODO: implement plan_waves()")


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
    # TODO: compare each canary with the baseline nodes of ITS OWN partition (training: step time; inference: serving TPOT)
    # TODO: gate EVERY canary node individually (worst case, not the mean); skip metrics that are empty for a partition
    # TODO: abort beats extend beats promote; reasons name the node and the metric
    raise NotImplementedError("TODO: implement canary_decision()")


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
    # TODO: use check_compatibility() for each node in schedulable/validated/drained
    # TODO: a schedulable node on a blocked/unknown/non-compliant stack must be drained BEFORE it is reimaged
    # TODO: deprecated nodes are scheduled into an upgrade wave, not drained immediately
    # TODO: the plan must be a pure function of its inputs: running it twice gives the same list
    raise NotImplementedError("TODO: implement plan_remediation()")


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
    # TODO: copy the entry; set seq, prev_hash (64 zeros for the first record) and hash via record_hash()
    # TODO: do not mutate `chain` or `entry`
    raise NotImplementedError("TODO: implement audit_append()")


def audit_verify(chain: list[dict[str, Any]]) -> int | None:
    """Return the ``seq`` of the first record that breaks the chain, or None if intact.

    A record breaks the chain if its hash does not match its content, its prev_hash does not equal
    the previous record's hash (genesis: 64 zeros), or its seq is not previous seq + 1.
    """
    # TODO: walk the chain recomputing record_hash() and checking prev_hash links and seq continuity
    # TODO: return the seq of the first bad record, or None
    raise NotImplementedError("TODO: implement audit_verify()")
