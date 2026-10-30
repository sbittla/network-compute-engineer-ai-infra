#!/usr/bin/env python3
"""Chapter 20 lab checker - safe-change automation.

Usage:
    python check.py                    # check lab/starter/ (your work)
    python check.py --impl solution    # check the reference implementation (instructors)

Prints one PASS/FAIL/TODO line per check. Exit code 0 only if every check passes.
Pure Python, no network, no hardware; finishes in well under a second.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Callable

import yaml

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"

# Expected results for the committed dataset (seed 20).
EXP_VIOLATIONS = {("POL-PFC", "orion-be-leaf-r5"), ("POL-MTU-FABRIC", "orion-n10"),
                  ("POL-FW", "orion-n22"), ("SCHEMA", "orion-n25")}
EXP_BLOCKED = ["orion-be-leaf-r5", "orion-n10", "orion-n22", "orion-n25"]
EXP_UNREACHABLE = ["orion-n18"]
EXP_ACTIONS = 24
EXP_TARGETS = 22
EXP_DRIFT = {("orion-n06", "host_mtu", 1500, 9000), ("orion-n06", "rdma_path_mtu", 1024, 4096),
             ("orion-n13", "pfc_priorities", (), (3,)),
             ("orion-be-leaf-r2", "dscp_to_tc", None, None)}
EXP_ROLLBACK = ["orion-n01", "orion-n02", "orion-n05", "orion-n09", "orion-n17", "orion-n21",
                "orion-n25", "orion-n29"]
AUDIT_FIELDS = {"seq", "change_id", "actor", "target", "key", "before", "after", "result", "dry_run"}


def load_impl(impl: str):
    path = (HERE / "starter" if impl == "starter" else HERE.parent / "solutions" / "lab") / "safe_change.py"
    spec = importlib.util.spec_from_file_location(f"safe_change_{impl}", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod, path.parent


def jl(name: str) -> Any:
    with open(DATA / name, encoding="utf-8") as fh:
        return json.load(fh)


class Fail(Exception):
    pass


def need(cond: bool, msg: str) -> None:
    if not cond:
        raise Fail(msg)


# ----------------------------------------------------------------------------- Part 1 checks

def c_validate(m) -> str:
    v = m.validate_desired(jl("desired_state.json"))
    got = {(x["rule"], x["target"]) for x in v}
    need(all({"rule", "target", "key", "message"} <= set(x) for x in v), "violation records missing fields")
    missing, extra = EXP_VIOLATIONS - got, got - EXP_VIOLATIONS
    need(not missing, f"missed planted violations: {sorted(missing)}")
    need(not extra, f"false-positive violations: {sorted(extra)}")
    return f"{len(v)} violations, all planted ones found"


def c_validate_clean(m) -> str:
    d = jl("desired_state.json")
    d["overrides"] = {}
    v = m.validate_desired(d)
    need(v == [], f"fleet defaults should be valid, got {v[:2]}")
    d["defaults"]["node"]["cnp_dscp"] = 26
    v = m.validate_desired(d)
    need({x["rule"] for x in v} >= {"POL-CNP"}, "CNP DSCP == RoCE DSCP not flagged")
    return "clean desired state passes; injected CNP/RoCE DSCP clash is caught"


def _plan(m):
    d = jl("desired_state.json")
    a = jl("actual_state.json")["state"]
    return d, a, m.compute_plan(d, a, m.validate_desired(d))


def c_plan(m) -> str:
    _, _, p = _plan(m)
    need(p["blocked"] == EXP_BLOCKED, f"blocked={p['blocked']}")
    need(p["unreachable"] == EXP_UNREACHABLE, f"unreachable={p['unreachable']}")
    acts = p["actions"]
    tg = {a["target"] for a in acts}
    need(not tg & set(EXP_BLOCKED + EXP_UNREACHABLE), "plan touches blocked or unreachable targets")
    need(len(acts) == EXP_ACTIONS, f"expected {EXP_ACTIONS} actions, got {len(acts)}")
    need(len(tg) == EXP_TARGETS, f"expected {EXP_TARGETS} targets, got {len(tg)}")
    keyed = {(a["target"], a["key"]): a for a in acts}
    for t, k, f, to in EXP_DRIFT:
        need((t, k) in keyed, f"drift on {t}.{k} not in plan")
        if f is not None:
            got_f = keyed[(t, k)]["from"]
            got_t = keyed[(t, k)]["to"]
            norm = (lambda x: tuple(x) if isinstance(x, list) else x)
            need(norm(got_f) == f and norm(got_t) == to, f"{t}.{k}: {got_f} -> {got_t}")
    need(all(a["key"] == "rdma_path_mtu" for a in acts if a["target"] not in ("orion-n06", "orion-be-leaf-r2")
             and a["key"] != "pfc_priorities"), "unexpected keys in plan")
    return f"{len(acts)} actions on {len(tg)} targets; blocked and unreachable excluded"


def c_dry_run(m) -> str:
    d, a, p = _plan(m)
    fleet = m.SimFleet(a)
    before = fleet.snapshot()
    r = m.apply_plan(fleet, p, change_id="CHG-TEST")
    need(fleet.writes == 0 and fleet.snapshot() == before, "default (dry-run) apply mutated the fleet")
    need(r["audit"] and all(x["result"] == "dry-run" for x in r["audit"]), "dry-run audit records wrong")
    need(len(r["audit"]) == EXP_ACTIONS, "dry run should report every action")
    return "apply_plan defaults to dry-run; zero writes"


def c_cap_and_audit(m) -> str:
    d, a, p = _plan(m)
    fleet = m.SimFleet(a)
    r = m.apply_plan(fleet, p, dry_run=False, max_targets=8, change_id="CHG-TEST", actor="ch20-lab")
    need(len(r["applied_targets"]) == 8, f"applied {len(r['applied_targets'])} targets, cap is 8")
    need(len(r["deferred_targets"]) == EXP_TARGETS - 8, "deferred targets wrong")
    touched = {x["target"] for x in r["audit"]}
    need(touched == set(r["applied_targets"]), "audit targets differ from applied targets")
    need(all(AUDIT_FIELDS <= set(x) for x in r["audit"]), f"audit records need {sorted(AUDIT_FIELDS)}")
    need(all(x["change_id"] == "CHG-TEST" and x["actor"] == "ch20-lab" for x in r["audit"]),
         "audit records must carry change_id and actor")
    need(all(x["result"] == "changed" for x in r["audit"]), "first real apply should change values")
    need(fleet.writes == len(r["audit"]), "writes != audited changes")
    return "blast-radius cap respected (8 targets); audit records complete"


def c_idempotent(m) -> str:
    d, a, p = _plan(m)
    fleet = m.SimFleet(a)
    rounds = 0
    while True:
        r = m.apply_plan(fleet, p, dry_run=False, max_targets=8, change_id="CHG-TEST")
        rounds += 1
        if not r["deferred_targets"]:
            break
        p = {**p, "actions": [x for x in p["actions"] if x["target"] in r["deferred_targets"]]}
        need(rounds < 10, "apply loop does not converge")
    need(rounds == 3, f"22 targets with cap 8 should take 3 batches, took {rounds}")
    snap = fleet.snapshot()
    v = m.validate_desired(d)
    p2 = m.compute_plan(d, snap, v)
    need(p2["actions"] == [], f"re-plan after apply should be empty, got {len(p2['actions'])} actions")
    w = fleet.writes
    _, _, p_orig = _plan(m)
    r2 = m.apply_plan(fleet, p_orig, dry_run=False, change_id="CHG-TEST")
    need(fleet.writes == w, "re-applying the old plan wrote to the fleet")
    need(all(x["result"] == "noop" for x in r2["audit"]), "re-apply should record noop")
    need(snap["orion-n18"] is None, "unreachable node must remain untouched")
    return "3 capped batches converge; re-plan empty; re-apply is a recorded no-op"


# ----------------------------------------------------------------------------- Part 2 checks

def c_conditions(m) -> str:
    conds = {c["id"]: c for c in jl("abort_conditions.json")["conditions"]}
    need(m.check_condition(conds["AC1"], [44.0] * 6, [41.0] * 12) is not None, "6.8% busbw drop not caught")
    need(m.check_condition(conds["AC1"], [44.0] * 6, [43.0] * 11 + [30.0]) is None,
         "single-sample dip must not breach a median condition")
    need(m.check_condition(conds["AC2"], [100.0] * 6, [400.0] * 12) is None, "CNP below floor must not breach")
    need(m.check_condition(conds["AC2"], [200.0] * 6, [700.0] * 12) is not None, "CNP 3.5x above floor missed")
    need(m.check_condition(conds["AC4"], [0] * 6, [0] * 11 + [1]) is not None, "single Xid missed")
    r = m.check_condition(conds["AC1"], [44.0] * 6, [41.0] * 12)
    need(str(r).startswith("AC1"), "reason must start with the condition ID")
    return "relative_drop / relative_rise+floor / sum_gt behave correctly"


def c_waves(m) -> str:
    ro, ac = jl("rollout.json"), jl("abort_conditions.json")
    ev = [m.evaluate_wave(w, ac) for w in ro["waves"][:3]]
    need(ev[0]["decision"] == "proceed", f"wave 0: {ev[0]['decision']} {ev[0]['reasons']}")
    need(ev[1]["decision"] == "proceed",
         f"wave 1 should proceed (precheck + noise handling): {ev[1]['decision']} {ev[1]['reasons']}")
    need(ev[1]["skipped_nodes"] == ["orion-n13"], f"wave 1 skipped={ev[1]['skipped_nodes']}")
    need(ev[2]["decision"] == "abort", f"wave 2 should abort, got {ev[2]['decision']}")
    rs = " ".join(ev[2]["reasons"])
    for tok in ("AC1", "AC2", "orion-n25", "orion-n29"):
        need(tok in rs, f"wave 2 reasons should mention {tok}")
    need("orion-n21" not in rs, "wave 2 reasons blame a healthy node")
    return "wave0 proceed; wave1 proceed (degraded node skipped, transient dip ignored); wave2 abort"


def c_bake(m) -> str:
    ro, ac = jl("rollout.json"), jl("abort_conditions.json")
    w = copy.deepcopy(ro["waves"][0])
    for n in w["nodes"]:
        n["post"] = {k: v[:6] for k, v in n["post"].items()}
    e = m.evaluate_wave(w, ac)
    need(e["decision"] == "hold", f"insufficient bake should hold, got {e['decision']}")
    return "insufficient bake time -> hold"


def c_rollout(m) -> str:
    r = m.run_rollout(jl("rollout.json"), jl("abort_conditions.json"))
    need(r["outcome"] == "aborted", f"outcome {r['outcome']}")
    need([e["decision"] for e in r["log"]] == ["proceed", "proceed", "abort"],
         f"decisions {[e['decision'] for e in r['log']]}")
    need(r["rollback_nodes"] == EXP_ROLLBACK, f"rollback set {r['rollback_nodes']}")
    need(r["not_started_waves"] == [3, 4, 5], f"not started {r['not_started_waves']}")
    need(r["deferred_nodes"] == ["orion-n13"], f"deferred {r['deferred_nodes']}")
    return "abort at wave 2; roll back 8 changed nodes; waves 3-5 never start"


# ----------------------------------------------------------------------------- Part 3 checks

def _findings(impl_dir: Path) -> list[dict]:
    with open(impl_dir / "findings.yaml", encoding="utf-8") as fh:
        doc = yaml.safe_load(fh) or {}
    fs = doc.get("findings") or []
    if not fs or any(str(f.get("gap_id", "TODO")).upper() == "TODO" for f in fs):
        raise NotImplementedError("findings.yaml still has TODO entries")
    return fs


def _review_sets(fs: list[dict]) -> tuple[set[str], set[str], dict]:
    rub = jl("review_rubric.json")
    exp = set(rub["expected_sha256"])
    ids = {str(f["gap_id"]) for f in fs}
    h = {i: hashlib.sha256((rub["salt"] + i).encode()).hexdigest() for i in ids}
    found = {i for i in ids if h[i] in exp}
    return found, ids - found, rub


def c_review_coverage(m, impl_dir: Path) -> str:
    fs = _findings(impl_dir)
    found, _, rub = _review_sets(fs)
    n_exp = len(rub["expected_sha256"])
    need(len(found) >= rub["min_expected_found"],
         f"found {len(found)}/{n_exp} real gaps; need >= {rub['min_expected_found']}")
    return f"found {len(found)}/{n_exp} real gaps"


def c_review_precision(m, impl_dir: Path) -> str:
    fs = _findings(impl_dir)
    _, fp, rub = _review_sets(fs)
    catalog = {g["id"] for g in jl("gap_catalog.json")["gaps"]}
    unknown = {i for i in fp if i not in catalog}
    need(not unknown, f"gap IDs not in catalogue: {sorted(unknown)}")
    need(len(fp) <= rub["max_false_positives"],
         f"{len(fp)} cited gaps are already covered by the plan: {sorted(fp)}")
    return f"{len(fp)} false positive(s) (limit {rub['max_false_positives']})"


def c_review_evidence(m, impl_dir: Path) -> str:
    fs = _findings(impl_dir)
    n_lines = len((DATA / "unsafe_change_plan.md").read_text(encoding="utf-8").splitlines())
    kw = {g["id"]: [k.lower() for k in g["fix_keywords"]] for g in jl("gap_catalog.json")["gaps"]}
    for f in fs:
        lines = f.get("plan_lines") or []
        need(lines and all(isinstance(x, int) and 1 <= x <= n_lines for x in lines),
             f"{f.get('gap_id')}: plan_lines must cite lines 1..{n_lines}")
        fix = str(f.get("fix", "")).lower()
        need(any(k in fix for k in kw.get(str(f["gap_id"]), [])),
             f"{f['gap_id']}: fix does not name a concrete control (expected one of {kw.get(str(f['gap_id']))})")
        need(len(str(f.get("issue", ""))) >= 20, f"{f['gap_id']}: issue text too short")
    return f"{len(fs)} findings cite valid plan lines and concrete fixes"


CHECKS: list[tuple[str, Callable, bool]] = [
    ("p1.validate_planted_violations", c_validate, False),
    ("p1.validate_clean_and_cnp_rule", c_validate_clean, False),
    ("p1.plan_diff_blocked_unreachable", c_plan, False),
    ("p1.apply_default_is_dry_run", c_dry_run, False),
    ("p1.apply_cap_and_audit", c_cap_and_audit, False),
    ("p1.idempotent_converge_and_noop", c_idempotent, False),
    ("p2.condition_semantics", c_conditions, False),
    ("p2.wave_decisions", c_waves, False),
    ("p2.bake_insufficient_hold", c_bake, False),
    ("p2.rollout_abort_and_rollback", c_rollout, False),
    ("p3.review_coverage", c_review_coverage, True),
    ("p3.review_false_positives", c_review_precision, True),
    ("p3.review_evidence_quality", c_review_evidence, True),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--impl", choices=["starter", "solution"], default="starter")
    args = ap.parse_args()
    try:
        mod, impl_dir = load_impl(args.impl)
    except Exception as exc:  # noqa: BLE001 - report, do not crash
        print(f"FAIL import  could not import {args.impl} module: {exc!r}")
        return 2
    passed = 0
    for name, fn, needs_dir in CHECKS:
        try:
            msg = fn(mod, impl_dir) if needs_dir else fn(mod)
            print(f"PASS {name}  {msg}")
            passed += 1
        except NotImplementedError as exc:
            print(f"TODO {name}  not implemented yet ({exc})")
        except Fail as exc:
            print(f"FAIL {name}  {exc}")
        except Exception as exc:  # noqa: BLE001 - learner code may raise anything
            print(f"FAIL {name}  {type(exc).__name__}: {exc}")
    print(f"\n{passed}/{len(CHECKS)} checks passed ({args.impl})")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
