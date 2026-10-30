"""Chapter 20 lab - safe-change automation for ORION (STARTER - implement the TODOs).

Three parts:
  Part 1  validate desired state -> compute an idempotent plan -> apply (dry-run / capped) to a simulated fleet
  Part 2  canary rollout controller over per-wave health evidence with pre-declared abort conditions
  Part 3  (findings.yaml next to this module) review of an unsafe change plan

Units: MTU values are bytes; busbw is GB/s; rates are events per second; sample interval is minutes.
Everything here runs against in-memory data. Nothing touches a real host or switch.
"""
from __future__ import annotations

import copy
import json
import statistics
from pathlib import Path
from typing import Any

# --------------------------------------------------------------------------- provided helpers

NODE_SCHEMA: dict[str, type | tuple] = {
    "host_mtu": int,
    "rdma_path_mtu": int,
    "trust_mode": str,
    "roce_dscp": int,
    "roce_priority": int,
    "pfc_priorities": list,
    "ecn_enabled": bool,
    "cnp_dscp": int,
    "nic_firmware": str,
}
LEAF_SCHEMA: dict[str, type | tuple] = {
    "port_mtu": int,
    "pfc_priorities": list,
    "ecn_queues": list,
    "dscp_to_tc": dict,
    "strict_priority_tc": list,
}
TRUST_MODES = {"dscp", "pcp"}


def load_json(path: str | Path) -> Any:
    """Load a JSON file (UTF-8)."""
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


class SimFleet:
    """In-memory stand-in for a fleet API (Redfish / NIC tool / switch gNMI in real life).

    ``state`` maps target name -> config dict, or ``None`` when the target is unreachable.
    ``writes`` counts mutating calls so tests can prove a dry run or a no-op wrote nothing.
    """

    def __init__(self, state: dict[str, dict | None]):
        self._state = copy.deepcopy(state)
        self.writes = 0

    def targets(self) -> list[str]:
        return sorted(self._state)

    def get(self, target: str) -> dict | None:
        cfg = self._state.get(target)
        return copy.deepcopy(cfg) if cfg is not None else None

    def set(self, target: str, key: str, value: Any) -> None:
        if self._state.get(target) is None:
            raise ConnectionError(f"{target} unreachable")
        self._state[target][key] = copy.deepcopy(value)
        self.writes += 1

    def snapshot(self) -> dict[str, dict | None]:
        return copy.deepcopy(self._state)


def target_kind(target: str) -> str:
    """'node' or 'leaf' from the ORION naming convention."""
    return "leaf" if target.startswith("orion-be-leaf-") else "node"


# --------------------------------------------------------------------------- Part 1

def resolve_desired(desired: dict) -> dict[str, dict]:
    """Merge defaults[kind] with per-target overrides for every target in desired['targets'].

    Returns {target: full desired config}. Overrides replace whole values (no deep merge).
    """
    # TODO: copy defaults[kind] for each target, then apply overrides (whole-value replace).
    raise NotImplementedError("resolve_desired")


def _schema_violations(target: str, cfg: dict) -> list[dict]:
    """SCHEMA rule for one resolved target: unknown keys, missing keys, wrong types, trust_mode enum.

    Returns violations {"rule": "SCHEMA", "target", "key", "message"}.
    """
    schema = LEAF_SCHEMA if target_kind(target) == "leaf" else NODE_SCHEMA
    # TODO: report unknown/missing keys and wrong types (watch out: bool is a subclass of int).
    raise NotImplementedError("_schema_violations")


def validate_desired(desired: dict) -> list[dict]:
    """Validate the resolved desired state. Returns a list of violations.

    Each violation: {"rule", "target", "key", "message"}. Rules:
      SCHEMA          keys present/known and correctly typed; trust_mode enum
      POL-MTU-RDMA    rdma_path_mtu allowed and rdma_path_mtu + roce_header_budget <= host_mtu
      POL-MTU-FABRIC  host_mtu + l2_overhead <= min(leaf port_mtu)
      POL-PFC         node pfc_priorities == [roce_priority]; leaf pfc_priorities == [fleet roce priority];
                      leaf dscp_to_tc maps roce_dscp -> roce priority and cnp_dscp -> a strict, non-PFC TC
      POL-CNP         cnp_dscp != roce_dscp
      POL-FW          nic_firmware in policy.approved_nic_firmware
    A target with a SCHEMA violation is not evaluated by the policy rules (its values are untrusted).
    Output is sorted by (target, rule, key).
    """
    # TODO: run _schema_violations on every resolved target, then the POL-* rules on targets
    #       that passed the schema. Use desired['policy'] for thresholds; never hard-code 9216 or 3.
    raise NotImplementedError("validate_desired")


def compute_plan(desired: dict, actual: dict[str, dict | None], violations: list[dict]) -> dict:
    """Diff resolved desired state against actual state.

    Returns {"actions": [...], "blocked": [...], "unreachable": [...]} where each action is
    {"target", "key", "from", "to"}. Targets with any violation are *blocked* (no actions);
    targets whose actual state is None are *unreachable* (no actions). Only keys whose actual
    value differs from desired produce actions. Sorted by (target, key). A plan computed against
    a fleet that already matches desired state has no actions (idempotency).
    """
    # TODO: blocked = targets with violations; unreachable = actual is None; diff the rest key by key.
    raise NotImplementedError("compute_plan")


def apply_plan(fleet: SimFleet, plan: dict, *, dry_run: bool = True, max_targets: int | None = None,
               change_id: str = "UNSET", actor: str = "automation") -> dict:
    """Apply plan actions to ``fleet``, at most ``max_targets`` distinct targets per call.

    Targets are taken in sorted order. For each action an audit record is produced:
      {"seq", "change_id", "actor", "target", "key", "before", "after", "result", "dry_run"}
    where ``before`` is the value read from the fleet *at apply time* and ``result`` is
      "dry-run"  (dry_run=True, nothing written),
      "noop"     (fleet already holds the desired value, nothing written),
      "changed"  (value written).
    Returns {"applied_targets", "deferred_targets", "audit"}. Defaults to dry_run=True (safe default).
    """
    # TODO: respect max_targets (sorted targets), read 'before' at apply time, never write when
    #       dry_run=True or when the fleet already holds the desired value. Emit one audit record per action.
    raise NotImplementedError("apply_plan")


# --------------------------------------------------------------------------- Part 2

def _aggregate(values: list[float], how: str) -> float:
    if how == "median":
        return float(statistics.median(values))
    if how == "sum":
        return float(sum(values))
    if how == "max":
        return float(max(values))
    if how == "min":
        return float(min(values))
    raise ValueError(f"unknown aggregation {how}")


def check_condition(cond: dict, baseline: list[float], post: list[float]) -> str | None:
    """Return a human-readable breach reason (without node name) or None if not breached."""
    # TODO: implement relative_drop, relative_rise (with floor) and sum_gt using _aggregate().
    raise NotImplementedError("check_condition")


def evaluate_wave(wave: dict, conditions: dict) -> dict:
    """Decide what to do after one wave's bake.

    1. Precheck: nodes not drained or not health=='ok' are *skipped* (never changed, never evaluated).
    2. Bake: if any changed node has fewer than conditions['bake']['min_post_samples'] post samples,
       decision is "hold" (insufficient evidence; do not proceed, do not roll back yet).
    3. Abort: any condition breached on any changed node -> "abort". Reasons are strings starting
       with the condition ID and containing the node name.
    4. Otherwise "proceed".
    Returns {"wave", "decision", "changed_nodes", "skipped_nodes", "reasons"}.
    """
    # TODO: precheck -> bake sufficiency -> abort conditions -> proceed.
    raise NotImplementedError("evaluate_wave")


def run_rollout(rollout: dict, conditions: dict) -> dict:
    """Run waves in order until all succeed, one aborts, or one holds.

    Returns {"log": [evaluate_wave results...], "outcome": "completed"|"aborted"|"held",
             "rollback_nodes": sorted nodes to roll back (all changed nodes so far when
             rollback_scope == 'all_changed', else only the failing wave's), "not_started_waves",
             "deferred_nodes": nodes skipped by precheck}.
    """
    # TODO: iterate waves; stop on abort (compute rollback set per rollback_scope) or hold.
    raise NotImplementedError("run_rollout")


if __name__ == "__main__":
    data = Path(__file__).resolve().parents[1] / "data"
    d = load_json(data / "desired_state.json")
    a = load_json(data / "actual_state.json")["state"]
    v = validate_desired(d)
    for x in v:
        print("VIOLATION", x)
    p = compute_plan(d, a, v)
    print(f"plan: {len(p['actions'])} actions, blocked={p['blocked']}, unreachable={p['unreachable']}")
    r = run_rollout(load_json(data / "rollout.json"), load_json(data / "abort_conditions.json"))
    for e in r["log"]:
        print(e["wave"], e["decision"], e["reasons"])
    print(r["outcome"], r["rollback_nodes"], r["not_started_waves"])
