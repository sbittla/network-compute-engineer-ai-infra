"""Chapter 20 lab - safe-change automation for ORION (REFERENCE SOLUTION, instructor only).

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
    out: dict[str, dict] = {}
    for kind, names in desired["targets"].items():
        for name in names:
            cfg = copy.deepcopy(desired["defaults"][kind])
            cfg.update(copy.deepcopy(desired.get("overrides", {}).get(name, {})))
            out[name] = cfg
    return out


def _schema_violations(target: str, cfg: dict) -> list[dict]:
    """SCHEMA rule for one resolved target: unknown keys, missing keys, wrong types, trust_mode enum.

    Returns violations {"rule": "SCHEMA", "target", "key", "message"}.
    """
    schema = LEAF_SCHEMA if target_kind(target) == "leaf" else NODE_SCHEMA
    out = []
    for key in sorted(set(schema) | set(cfg)):
        if key not in schema:
            out.append({"rule": "SCHEMA", "target": target, "key": key, "message": "unknown key"})
        elif key not in cfg:
            out.append({"rule": "SCHEMA", "target": target, "key": key, "message": "missing key"})
        else:
            want = schema[key]
            val = cfg[key]
            # bool is a subclass of int: reject bools where ints are required.
            bad = not isinstance(val, want) or (want is int and isinstance(val, bool))
            if bad:
                out.append({"rule": "SCHEMA", "target": target, "key": key,
                            "message": f"expected {want.__name__}, got {type(val).__name__} {val!r}"})
    if target_kind(target) == "node" and cfg.get("trust_mode") not in TRUST_MODES:
        out.append({"rule": "SCHEMA", "target": target, "key": "trust_mode",
                    "message": f"trust_mode must be one of {sorted(TRUST_MODES)}"})
    return out


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
    pol = desired["policy"]
    resolved = resolve_desired(desired)
    fleet_node = desired["defaults"]["node"]
    violations: list[dict] = []
    schema_bad: set[str] = set()
    for t, cfg in resolved.items():
        sv = _schema_violations(t, cfg)
        if sv:
            schema_bad.add(t)
            violations.extend(sv)

    leaf_mtus = [cfg["port_mtu"] for t, cfg in resolved.items()
                 if target_kind(t) == "leaf" and t not in schema_bad]
    min_leaf_mtu = min(leaf_mtus) if leaf_mtus else None

    for t, cfg in resolved.items():
        if t in schema_bad:
            continue
        if target_kind(t) == "node":
            if cfg["rdma_path_mtu"] not in pol["allowed_rdma_path_mtu"]:
                violations.append({"rule": "POL-MTU-RDMA", "target": t, "key": "rdma_path_mtu",
                                   "message": f"{cfg['rdma_path_mtu']} not an allowed RDMA MTU"})
            elif cfg["rdma_path_mtu"] + pol["roce_header_budget_bytes"] > cfg["host_mtu"]:
                violations.append({"rule": "POL-MTU-RDMA", "target": t, "key": "rdma_path_mtu",
                                   "message": f"rdma_path_mtu {cfg['rdma_path_mtu']} + "
                                              f"{pol['roce_header_budget_bytes']} > host_mtu {cfg['host_mtu']}"})
            if min_leaf_mtu is not None and cfg["host_mtu"] + pol["l2_overhead_bytes"] > min_leaf_mtu:
                violations.append({"rule": "POL-MTU-FABRIC", "target": t, "key": "host_mtu",
                                   "message": f"host_mtu {cfg['host_mtu']} + {pol['l2_overhead_bytes']} = "
                                              f"{cfg['host_mtu'] + pol['l2_overhead_bytes']} > leaf port_mtu "
                                              f"{min_leaf_mtu}"})
            if sorted(cfg["pfc_priorities"]) != [cfg["roce_priority"]]:
                violations.append({"rule": "POL-PFC", "target": t, "key": "pfc_priorities",
                                   "message": f"PFC on {cfg['pfc_priorities']} but RoCE priority is "
                                              f"{cfg['roce_priority']}"})
            if cfg["cnp_dscp"] == cfg["roce_dscp"]:
                violations.append({"rule": "POL-CNP", "target": t, "key": "cnp_dscp",
                                   "message": "CNP DSCP must differ from RoCE data DSCP"})
            if cfg["nic_firmware"] not in pol["approved_nic_firmware"]:
                violations.append({"rule": "POL-FW", "target": t, "key": "nic_firmware",
                                   "message": f"{cfg['nic_firmware']} not in approved list "
                                              f"{pol['approved_nic_firmware']}"})
        else:
            rp = fleet_node["roce_priority"]
            if sorted(cfg["pfc_priorities"]) != [rp]:
                violations.append({"rule": "POL-PFC", "target": t, "key": "pfc_priorities",
                                   "message": f"leaf PFC on {cfg['pfc_priorities']} but fleet RoCE "
                                              f"priority is {rp}"})
            m = cfg["dscp_to_tc"]
            if m.get(str(fleet_node["roce_dscp"])) != rp:
                violations.append({"rule": "POL-PFC", "target": t, "key": "dscp_to_tc",
                                   "message": f"DSCP {fleet_node['roce_dscp']} must map to TC {rp}"})
            cnp_tc = m.get(str(fleet_node["cnp_dscp"]))
            if cnp_tc not in cfg["strict_priority_tc"] or cnp_tc in cfg["pfc_priorities"]:
                violations.append({"rule": "POL-PFC", "target": t, "key": "dscp_to_tc",
                                   "message": f"CNP DSCP {fleet_node['cnp_dscp']} must map to a strict, "
                                              f"non-PFC TC (got {cnp_tc})"})
    return sorted(violations, key=lambda v: (v["target"], v["rule"], v["key"]))


def compute_plan(desired: dict, actual: dict[str, dict | None], violations: list[dict]) -> dict:
    """Diff resolved desired state against actual state.

    Returns {"actions": [...], "blocked": [...], "unreachable": [...]} where each action is
    {"target", "key", "from", "to"}. Targets with any violation are *blocked* (no actions);
    targets whose actual state is None are *unreachable* (no actions). Only keys whose actual
    value differs from desired produce actions. Sorted by (target, key). A plan computed against
    a fleet that already matches desired state has no actions (idempotency).
    """
    resolved = resolve_desired(desired)
    blocked = sorted({v["target"] for v in violations})
    unreachable = sorted(t for t in resolved if actual.get(t) is None and t not in blocked)
    actions = []
    for t in sorted(resolved):
        if t in blocked or t in unreachable:
            continue
        cur = actual[t]
        for key in sorted(resolved[t]):
            if cur.get(key) != resolved[t][key]:
                actions.append({"target": t, "key": key, "from": copy.deepcopy(cur.get(key)),
                                "to": copy.deepcopy(resolved[t][key])})
    return {"actions": actions, "blocked": blocked, "unreachable": unreachable}


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
    targets = sorted({a["target"] for a in plan["actions"]})
    cap = len(targets) if max_targets is None else max(0, max_targets)
    now, later = targets[:cap], targets[cap:]
    audit = []
    seq = 0
    for a in plan["actions"]:
        if a["target"] not in now:
            continue
        cur = fleet.get(a["target"])
        before = None if cur is None else copy.deepcopy(cur.get(a["key"]))
        if dry_run:
            result = "dry-run"
        elif before == a["to"]:
            result = "noop"
        else:
            fleet.set(a["target"], a["key"], a["to"])
            result = "changed"
        seq += 1
        audit.append({"seq": seq, "change_id": change_id, "actor": actor, "target": a["target"],
                      "key": a["key"], "before": before, "after": copy.deepcopy(a["to"]),
                      "result": result, "dry_run": dry_run})
    return {"applied_targets": now, "deferred_targets": later, "audit": audit}


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
    agg = cond["aggregation"]
    p = _aggregate(post, agg)
    if cond["type"] == "relative_drop":
        b = _aggregate(baseline, agg)
        drop = (b - p) / b if b else 0.0
        if drop > cond["threshold"]:
            return (f"{cond['id']} {cond['metric']} {agg} {p:.2f} vs baseline {b:.2f} "
                    f"(-{drop * 100:.1f}% > {cond['threshold'] * 100:.0f}%)")
    elif cond["type"] == "relative_rise":
        b = _aggregate(baseline, agg)
        if p > cond["threshold"] * b and p > cond.get("floor", 0.0):
            return (f"{cond['id']} {cond['metric']} {agg} {p:.1f} > {cond['threshold']}x baseline {b:.1f} "
                    f"and > floor {cond.get('floor', 0.0):.0f}")
    elif cond["type"] == "sum_gt":
        if p > cond["threshold"]:
            return f"{cond['id']} {cond['metric']} sum {p:.0f} > {cond['threshold']}"
    else:
        raise ValueError(f"unknown condition type {cond['type']}")
    return None


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
    pre = conditions["precheck"]
    changed, skipped, reasons = [], [], []
    for n in wave["nodes"]:
        pc = n["precheck"]
        ok = (pc.get("drained") or not pre["require_drained"]) and pc.get("health") == pre["require_health"]
        if not ok:
            skipped.append(n["node"])
            reasons.append(f"PRECHECK {n['node']} skipped: drained={pc.get('drained')} "
                           f"health={pc.get('health')}")
        else:
            changed.append(n)
    need = conditions["bake"]["min_post_samples"]
    short = [n["node"] for n in changed if min(len(v) for v in n["post"].values()) < need]
    if short:
        for s in short:
            reasons.append(f"BAKE {s} has fewer than {need} post-change samples")
        decision = "hold"
    else:
        breaches = []
        for n in changed:
            for c in conditions["conditions"]:
                r = check_condition(c, n["baseline"][c["metric"]], n["post"][c["metric"]])
                if r:
                    breaches.append(f"{r} on {n['node']}")
        reasons.extend(breaches)
        decision = "abort" if breaches else "proceed"
    return {"wave": wave["wave"], "decision": decision, "changed_nodes": [n["node"] for n in changed],
            "skipped_nodes": skipped, "reasons": reasons}


def run_rollout(rollout: dict, conditions: dict) -> dict:
    """Run waves in order until all succeed, one aborts, or one holds.

    Returns {"log": [evaluate_wave results...], "outcome": "completed"|"aborted"|"held",
             "rollback_nodes": sorted nodes to roll back (all changed nodes so far when
             rollback_scope == 'all_changed', else only the failing wave's), "not_started_waves",
             "deferred_nodes": nodes skipped by precheck}.
    """
    log, changed_so_far, deferred = [], [], []
    outcome, rollback = "completed", []
    waves = sorted(rollout["waves"], key=lambda w: w["wave"])
    not_started: list[int] = []
    for i, w in enumerate(waves):
        ev = evaluate_wave(w, conditions)
        log.append(ev)
        changed_so_far.extend(ev["changed_nodes"])
        deferred.extend(ev["skipped_nodes"])
        if ev["decision"] == "abort":
            outcome = "aborted"
            rollback = (changed_so_far if rollout.get("rollback_scope") == "all_changed"
                        else ev["changed_nodes"])
            not_started = [x["wave"] for x in waves[i + 1:]]
            break
        if ev["decision"] == "hold":
            outcome = "held"
            not_started = [x["wave"] for x in waves[i + 1:]]
            break
    return {"log": log, "outcome": outcome, "rollback_nodes": sorted(rollback),
            "not_started_waves": not_started, "deferred_nodes": sorted(deferred)}


if __name__ == "__main__":
    data = Path(__file__).resolve().parents[2] / "lab" / "data"
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
