#!/usr/bin/env python3
"""Checker for the Capstone F starter kit (AI infrastructure reliability game day).

Usage:
    python check.py                    # check your starter/gameday.py (default)
    python check.py --impl solution    # instructor: check ../instructor/reference/gameday.py

Contract (docs/LAB_STANDARDS.md §4): one line per check (PASS/FAIL/TODO), never a traceback,
exit 0 only when every check passes. Pure Python, simulated cluster only, no network, < 60 s.
"""
from __future__ import annotations

import argparse
import filecmp
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Callable

HERE = Path(__file__).resolve().parent
MODULE = "gameday"
DATA = HERE / "data"
sys.path.insert(0, str(HERE))
from sim import cluster_sim  # noqa: E402  (given simulator)

# Canonical single-fault scenarios used to test YOUR alert rules (independent of your plan).
CANONICAL = {
    "node_loss": {"id": "C-node", "kind": "node_loss", "target": "orion-n09", "start_s": 5000},
    "link_down": {"id": "C-link", "kind": "link_down", "target": "orion-n06", "rail": 3, "start_s": 5000,
                  "duration_s": 600},
    "scheduler_outage": {"id": "C-sched", "kind": "scheduler_outage", "start_s": 5000, "duration_s": 900},
    "storage_slow": {"id": "C-stor", "kind": "storage_slow", "factor": 0.05, "start_s": 5000, "duration_s": 1800},
}
# Expected results on the RECORDED first game day (data/gameday1_*), which used the default rules.
EXPECTED_DETECT = {"F1": 30.0, "F2": None, "F3": 25.0, "F4": None, "F5": 30.0}
EXPECTED_LOST = {"F1": 94.4, "F2": 0.0, "F3": 167.8, "F4": 0.0, "F5": 307.9}



class Skip(Exception):
    """A check that cannot run in this copy (e.g. the instructor-only generator is absent)."""


def load(impl: str) -> ModuleType | None:
    path = (HERE / "starter" / f"{MODULE}.py") if impl == "starter" else (
        HERE.parent / "instructor" / "reference" / f"{MODULE}.py")
    if not path.exists():
        print(f"Implementation not found: {path}")
        if impl == "solution":
            print("(The instructor/ folder is removed from student releases; use --impl starter.)")
        return None
    spec = importlib.util.spec_from_file_location(f"{MODULE}_{impl}", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    try:
        spec.loader.exec_module(mod)
    except Exception as exc:  # noqa: BLE001 — syntax errors etc. in learner code
        print(f"FAIL  import -- {type(exc).__name__}: {exc}")
        return None
    return mod


class Ctx:
    def __init__(self, m: ModuleType) -> None:
        self.m = m
        self.d = m.load_inputs(DATA)
        self.cons = self.d["constraints"]
        self.rec = self.d["gameday1"]
        self.faults = {f["id"]: f for f in self.d["gameday1_plan"]["faults"]}


def _close(a: float | None, b: float | None, tol: float = 0.15) -> bool:
    if a is None or b is None:
        return a is b
    return abs(a - b) <= tol


# --------------------------------------------------------------------------- checks
def c_data(_: Ctx) -> str:
    if not (HERE / "tools" / "generate_data.py").exists():
        raise Skip("generator is instructor copy only (tools/ absent); data/ used as shipped")
    with tempfile.TemporaryDirectory() as tmp:
        proc = subprocess.run([sys.executable, str(HERE / "tools" / "generate_data.py"), "--out", tmp],
                              capture_output=True, text=True, timeout=60)
        assert proc.returncode == 0, f"generator failed: {proc.stderr.strip()[-200:]}"
        files = sorted(p.name for p in DATA.iterdir() if p.is_file())
        _, mismatch, errors = filecmp.cmpfiles(DATA, tmp, files, shallow=False)
        assert not mismatch and not errors, f"regenerated files differ: {mismatch + errors}"
    return f"{len(files)} files byte-identical on regeneration"


def c_sim_deterministic(_: Ctx) -> str:
    f = [CANONICAL["node_loss"]]
    a, b = cluster_sim.run(f, []), cluster_sim.run(f, [])
    assert a.events == b.events, "simulator is not deterministic"
    return f"{len(a.events)} events identical across two runs"


def c_plan_shape(c: Ctx) -> str:
    plan = c.m.fault_plan()
    assert len(plan) >= 5, f"need >= 5 scenarios, got {len(plan)}"
    kinds, combos, ids = set(), 0, set()
    prot = set(c.cons["protected_nodes"])
    for sc in plan:
        for key in ("id", "title", "faults", "hypothesis", "expected", "abort_conditions", "blast_radius", "rollback"):
            assert sc.get(key), f"{sc.get('id')}: missing or empty '{key}'"
        fs = sc["faults"]
        cluster_sim.validate_faults(fs, c.cons["horizon_s"])
        for f in fs:
            assert f["id"] not in ids, f"duplicate fault id {f['id']}"
            ids.add(f["id"])
            kinds.add(f["kind"])
            assert f.get("target") not in prot, f"{f['id']} targets protected node {f.get('target')}"
            assert f["start_s"] >= c.cons["warmup_s"], f"{f['id']} starts inside the warm-up"
            assert f["id"] in sc["expected"], f"{sc['id']}: no expected behaviour for {f['id']}"
        spans = [(f["start_s"], f["start_s"] + f.get("duration_s", c.cons["horizon_s"])) for f in fs]
        for t, _ in spans:
            active = sum(1 for s, e in spans if s <= t < e)
            assert active <= c.cons["max_concurrent_faults"], f"{sc['id']}: > max concurrent faults"
        if len(fs) >= 2 and any(s2 < e1 and s1 < e2 for i, (s1, e1) in enumerate(spans)
                                 for (s2, e2) in spans[i + 1:]):
            combos += 1
    missing = set(cluster_sim.FAULT_KINDS) - kinds
    assert not missing, f"fault kinds never injected: {sorted(missing)}"
    assert combos >= 1, "need at least one scenario with two overlapping faults"
    return f"{len(plan)} scenarios, all four kinds, {combos} combined, no protected targets"


def c_plan_runs(c: Ctx) -> str:
    plan, rules = c.m.fault_plan(), c.m.alert_rules()
    held = failed = 0
    for sc in plan:
        res = cluster_sim.run(sc["faults"], rules, {"horizon_s": c.cons["horizon_s"]})
        metrics = {f["id"]: c.m.recovery_metrics(res, f) for f in sc["faults"]}
        verdicts = c.m.evaluate_hypotheses(sc, metrics)
        assert set(verdicts) == set(sc["expected"]), f"{sc['id']}: verdicts missing"
        for v in verdicts.values():
            held += v["verdict"] == "held"
            failed += v["verdict"] == "failed"
    return f"plan executed: {held} hypotheses held, {failed} refuted (refutations are findings)"


def c_rules_quiet(c: Ctx) -> str:
    rules = c.m.alert_rules()
    for r in rules:
        for key in ("name", "metric", "op", "for_s", "severity", "detects"):
            assert key in r, f"rule {r.get('name')} missing '{key}'"
    res = cluster_sim.run([], rules, {"horizon_s": c.cons["horizon_s"]})
    n = len(res.alerts)
    names = sorted({a["rule"] for a in res.alerts})
    assert n <= c.cons["max_false_alerts_per_6h"], f"{n} alerts on a fault-free 6 h run (false positives): {names}"
    return "0 alerts on a fault-free 6 h run"


def c_rules_detect(c: Ctx) -> str:
    rules = c.m.alert_rules()
    targets = c.cons["detection_targets_s"]
    got = {}
    for kind, f in CANONICAL.items():
        res = cluster_sim.run([f], rules, {"horizon_s": c.cons["horizon_s"]})
        hung = {e["job"] for e in res.events if e["kind"] == "job_hung"
                and e.get("cause") == f"{kind} {f.get('target')}"}
        hits = [a["t_fire"] - f["start_s"] for a in res.alerts
                if kind in a.get("detects", []) and a["t_fire"] >= f["start_s"]
                and not ("node" in a["labels"] and f.get("target") and a["labels"]["node"] != f["target"])
                and not ("node" not in a["labels"] and "job" in a["labels"] and f.get("target")
                         and a["labels"]["job"] not in hung)]
        got[kind] = min(hits) if hits else None
    bad = {k: v for k, v in got.items() if v is None or v > targets[k]}
    assert not bad, f"missed or late (s): {bad}; targets {targets}"
    return ", ".join(f"{k} {v:.0f}s" for k, v in got.items())


def c_detect_recorded(c: Ctx) -> str:
    got = {fid: c.m.detection_time(c.rec, f) for fid, f in c.faults.items()}
    wrong = {k: (got[k], v) for k, v in EXPECTED_DETECT.items() if not _close(got[k], v)}
    assert not wrong, f"(got, expected): {wrong}"
    late = cluster_sim.SimResult(events=[], alerts=[
        {"rule": "Early", "labels": {}, "severity": "critical", "detects": ["scheduler_outage"], "t_fire": 90.0, "t_resolve": None},
        {"rule": "Late", "labels": {}, "severity": "critical", "detects": ["scheduler_outage"], "t_fire": 1100.0, "t_resolve": None}],
        config=c.rec.config)
    assert c.m.detection_time(late, {"id": "X", "kind": "scheduler_outage", "start_s": 100}) is None,         "alerts before onset or beyond 2x the detection target must not count as detections"
    return "F1 30s, F2 undetected, F3 25s, F4 undetected, F5 30s (default rules)"


def c_metrics_recorded(c: Ctx) -> str:
    got = {fid: c.m.recovery_metrics(c.rec, f) for fid, f in c.faults.items()}
    f3 = got["F3"]
    assert not (11 <= f3["lost_work_gpu_h"] <= 15), \
        "F3 lost work ~13 GPU-h: you restored from the last STARTED checkpoint; it was aborted (see ckpt_aborted)"
    wrong = {k: (got[k]["lost_gpu_h"], v) for k, v in EXPECTED_LOST.items() if not _close(got[k]["lost_gpu_h"], v, 0.2)}
    assert not wrong, f"lost_gpu_h (got, expected): {wrong}"
    assert got["F5"]["recovered"] is False and got["F5"]["recover_s"] is None, "F5 never recovered (spares exhausted)"
    assert _close(got["F5"]["mitigate_s"], 900.0), f"F5 mitigation waits for the scheduler: got {got['F5']['mitigate_s']}"
    assert _close(got["F1"]["recover_s"], 903.5, 0.2), f"F1 recover_s {got['F1']['recover_s']}"
    assert got["F4"]["recover_s"] == 1200 and got["F2"]["recover_s"] == 3600, "global faults recover at rollback"
    total = sum(v["lost_gpu_h"] for v in got.values())
    return f"total {total:.1f} GPU-h lost; F3 restored from durable step 414; F5 unrecovered"


def c_timeline(c: Ctx) -> str:
    tl = c.m.build_timeline(c.rec, c.d["gameday1_plan"]["t0_utc"])
    ts = [r["t_s"] for r in tl]
    assert ts == sorted(ts), "timeline not sorted"
    kinds = [r["event"] for r in tl]
    assert kinds.count("fault_start") == 5, "every fault injection must appear"
    assert "ckpt_started" not in kinds and "ckpt_durable" not in kinds, "routine checkpoint events are noise"
    for k in ("ckpt_aborted", "requeue_blocked", "drain_pending", "job_resumed"):
        assert k in kinds, f"timeline must include {k}"
    f1 = next(r for r in tl if r["event"] == "fault_start" and "F1" in r["detail"])
    assert f1["utc"] == "2026-11-05T14:45:00Z" and f1["offset"] == "T+00:45:00", f"F1 row: {f1}"
    sub = c.m.build_timeline(c.rec, c.d["gameday1_plan"]["t0_utc"], 10000, 13000)
    assert sub and all(10000 <= r["t_s"] <= 13000 for r in sub), "window filter not applied"
    return f"{len(tl)} rows, sorted, windowable, UTC and T+ offsets correct"


def c_hypotheses(c: Ctx) -> str:
    sc = {"expected": {"A": {"detect_within_s": 120, "max_lost_gpu_h": 100, "expect_recovered": True},
                       "B": {"detect_within_s": 120, "max_lost_gpu_h": 0, "expect_recovered": True},
                       "C": {"detect_within_s": 120, "max_lost_gpu_h": 500, "expect_recovered": True}}}
    m = {"A": {"detect_s": 60.0, "lost_gpu_h": 90.0, "recovered": True},
         "B": {"detect_s": None, "lost_gpu_h": 0.0, "recovered": True},
         "C": {"detect_s": 30.0, "lost_gpu_h": 313.2, "recovered": False}}
    v = c.m.evaluate_hypotheses(sc, m)
    assert v["A"]["verdict"] == "held", f"A: {v['A']}"
    assert v["B"]["verdict"] == "failed" and v["B"]["detect_ok"] is False, f"B (undetected): {v['B']}"
    assert v["C"]["verdict"] == "failed" and v["C"]["recovered_ok"] is False, f"C (unrecovered): {v['C']}"
    return "held / failed verdicts correct, undetected never ok"


def c_backlog(c: Ctx) -> str:
    ranked = c.m.prioritize_backlog(c.d["backlog"])
    order = [r["id"] for r in ranked]
    exp = ["RB-01", "RB-05", "RB-04", "RB-03", "RB-02", "RB-06"]
    assert order == exp, f"order {order}; expected {exp}"
    sc = {r["id"]: r["score"] for r in ranked}
    assert _close(sc["RB-05"], 12000.0) and _close(sc["RB-03"], 1972.8), f"scores {sc}"
    return "RB-01 (safety) > RB-05 > RB-04 > RB-03 > RB-02 > RB-06"


CHECKS: list[tuple[str, Callable[[Ctx], str]]] = [
    ("dataset deterministic", c_data),
    ("simulator deterministic", c_sim_deterministic),
    ("T1 fault plan: structure and safety", c_plan_shape),
    ("T1 fault plan: executes in the simulator", c_plan_runs),
    ("T2 alert rules: no false positives", c_rules_quiet),
    ("T2 alert rules: detection targets", c_rules_detect),
    ("T3 detection times on recorded game day", c_detect_recorded),
    ("T4 recovery metrics on recorded game day", c_metrics_recorded),
    ("T5 incident timeline", c_timeline),
    ("T6 hypothesis evaluation", c_hypotheses),
    ("T7 backlog prioritisation", c_backlog),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--impl", choices=["starter", "solution"], default="starter")
    args = ap.parse_args()
    mod = load(args.impl)
    if mod is None:
        return 2
    try:
        ctx = Ctx(mod)
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL  load_inputs -- {type(exc).__name__}: {exc}")
        return 1
    passed = 0
    for name, fn in CHECKS:
        try:
            detail = fn(ctx)
            print(f"PASS  {name} -- {detail}")
            passed += 1
        except Skip as exc:
            print(f"SKIP  {name} -- {exc}")
            passed += 1
        except NotImplementedError as exc:
            print(f"TODO  {name} -- not implemented: {exc}")
        except AssertionError as exc:
            print(f"FAIL  {name} -- {exc}")
        except Exception as exc:  # noqa: BLE001 — learner code may raise anything
            print(f"FAIL  {name} -- {type(exc).__name__}: {exc}")
    print(f"\n{passed}/{len(CHECKS)} checks passed ({args.impl})")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
