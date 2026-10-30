#!/usr/bin/env python3
"""Checker for the Capstone E starter kit (bare-metal GPU fleet lifecycle automation).

Usage:
    python check.py                    # check your starter/fleet.py (default)
    python check.py --impl solution    # instructor: check ../instructor/reference/fleet.py

Contract (docs/LAB_STANDARDS.md §4): one line per check (PASS/FAIL/TODO), never a traceback,
exit 0 only when every check passes. Pure Python, no network, no hardware, < 60 s.
"""
from __future__ import annotations

import argparse
import copy
import filecmp
import importlib.util
import math
import subprocess
import sys
import tempfile
from collections import deque
from pathlib import Path
from types import ModuleType
from typing import Callable

HERE = Path(__file__).resolve().parent
MODULE = "fleet"
DATA = HERE / "data"

# Expected acceptance verdicts for the nodes imaged this week (derived from the dataset design).
EXPECTED_ACCEPTANCE = {
    "orion-n33": ["dcgm_diag", "gpu_count", "xid_events"],
    "orion-n34": ["nic_pcie_link"],
    "orion-n35": ["nic_link_speed"],
    "orion-n36": ["thermal"],
    "orion-n37": ["evidence_freshness"],
    "orion-n38": [],
    "orion-n39": [],
    "orion-n40": [],
    "orion-n10": [],
    "orion-n23": [],
}
EXPECTED_FINAL = {
    "orion-n33": "retired", "orion-n34": "repair", "orion-n35": "repair", "orion-n36": "repair",
    "orion-n37": "repair", "orion-n38": "schedulable", "orion-n39": "schedulable",
    "orion-n40": "validated", "orion-n10": "validated", "orion-n23": "schedulable",
    "orion-n07": "repair", "orion-n20": "drained", "orion-n13": "schedulable", "orion-lab-n01": "retired",
    "orion-n30": "schedulable", "orion-n01": "schedulable",
}



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
    sys.path.insert(0, str(HERE))
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
    """Lazily computed shared inputs so one unimplemented function does not cascade."""

    def __init__(self, m: ModuleType) -> None:
        self.m = m
        self.d = m.load_dataset(DATA)

    def acceptance(self) -> dict:
        return {r["node"]: self.m.evaluate_acceptance(r, self.d["policy"]) for r in self.d["results"]}

    def compat(self) -> dict:
        return {r["node"]: self.m.check_compatibility(r, self.d["matrix"]) for r in self.d["inventory"]}

    def states(self) -> dict:
        return {r["node"]: r["state"] for r in self.d["inventory"]}

    def wave_nodes(self) -> list[dict]:
        comp = self.compat()
        return [{"node": r["node"], "rack": r["rack"], "partition": r["role"], "state": r["state"],
                 "compat_status": comp[r["node"]]["status"]} for r in self.d["inventory"]]


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
        size = sum(p.stat().st_size for p in DATA.iterdir())
        assert size < 2_000_000, f"data/ is {size} B (limit 2 MB)"
    return f"{len(files)} files byte-identical on regeneration, {size / 1024:.0f} KiB"


def _graph(spec: dict) -> dict[str, set[str]]:
    return {s: {t for ts in ev.values() for t in ts} for s, ev in spec["transitions"].items()}


def _reachable(g: dict[str, set[str]], start: str, banned: set[str]) -> set[str]:
    seen, q = {start}, deque([start])
    while q:
        for nxt in g.get(q.popleft(), set()):
            if nxt not in seen and nxt not in banned:
                seen.add(nxt)
                q.append(nxt)
    return seen


def c_spec_shape(c: Ctx) -> str:
    spec = c.m.lifecycle_spec()
    need = {"discovered", "imaged", "validated", "schedulable", "drained", "repair", "retired"}
    assert need <= set(spec["states"]), f"missing states: {sorted(need - set(spec['states']))}"
    assert spec["initial"] == "discovered", "initial state must be discovered"
    assert spec["terminal"] == ["retired"] and not spec["transitions"].get("retired"), "retired must be terminal"
    g = _graph(spec)
    unreachable = set(spec["states"]) - _reachable(g, "discovered", set())
    assert not unreachable, f"unreachable states: {sorted(unreachable)}"
    dead = [s for s in spec["states"] if s != "retired" and "retired" not in _reachable(g, s, set())]
    assert not dead, f"states that can never be retired: {dead}"
    return f"{len(spec['states'])} states, all reachable, every state can reach retired"


def c_spec_safety(c: Ctx) -> str:
    spec = c.m.lifecycle_spec()
    g = _graph(spec)
    for start in ("discovered", "repair", "imaged"):
        r = _reachable(g, start, banned={"validated"})
        assert "schedulable" not in r, f"{start} can reach schedulable without passing validated"
    sched = spec["transitions"].get("schedulable", {})
    bad = [e for e in sched if set(sched[e]) & {"repair", "retired"}]
    assert not bad, f"schedulable (jobs running) must be drained before {bad}"
    return "no path to schedulable bypasses validated; repair/retire require drain"


def c_acceptance_planted(c: Ctx) -> str:
    acc = c.acceptance()
    wrong = {n: acc[n]["failures"] for n, exp in EXPECTED_ACCEPTANCE.items() if acc[n]["failures"] != exp}
    assert not wrong, f"unexpected failure sets: {wrong}"
    assert all(acc[n]["passed"] == (not exp) for n, exp in EXPECTED_ACCEPTANCE.items()), "passed flag inconsistent"
    n_fail = sum(1 for e in EXPECTED_ACCEPTANCE.values() if e)
    return f"{n_fail} planted failures found exactly; {len(EXPECTED_ACCEPTANCE) - n_fail} nodes pass"


def c_acceptance_policy_driven(c: Ctx) -> str:
    pol = copy.deepcopy(c.d["policy"])
    pol["rdma_write_Gbps_min"] = 395.0
    pol["burn_in_hours_min"] = 12.5
    out = {r["node"]: c.m.evaluate_acceptance(r, pol) for r in c.d["results"]}
    assert all("rdma_bw" in v["failures"] for v in out.values()), "rdma threshold not read from policy"
    assert "burn_in_duration" in out["orion-n39"]["failures"], "burn-in threshold not read from policy"
    return "thresholds come from the policy, not the code"


def c_compat(c: Ctx) -> str:
    comp = c.compat()
    assert comp["orion-n10"]["status"] == "non_compliant" and "heterogeneous_vbios" in comp["orion-n10"]["reasons"], \
        f"orion-n10: {comp['orion-n10']}"
    for n in ("orion-n20", "orion-n30"):
        assert comp[n]["status"] == "blocked", f"{n}: {comp[n]}"
    assert comp["orion-n40"]["status"] == "unknown" and any(r.startswith("bios:") for r in comp["orion-n40"]["reasons"]), \
        f"orion-n40: {comp['orion-n40']}"
    assert all(comp[f"orion-n{24 + i:02d}"]["status"] == "deprecated" for i in range(1, 5)), "rack-07 should be deprecated"
    golden = sum(1 for v in comp.values() if v["status"] == "golden")
    assert golden == 32, f"expected 32 golden nodes, got {golden}"
    return "blocked x2, deprecated x5, non_compliant x1, unknown x1, golden x32"


def c_apply_rules(c: Ctx) -> str:
    ctx = {"acceptance": {}, "compat": {}}
    s, o, _ = c.m.apply_event("drained", "drain", "x", ctx)
    assert (s, o) == ("drained", "noop"), f"drain on drained -> {(s, o)}; expected noop"
    s, o, _ = c.m.apply_event("repair", "admit", "x", ctx)
    assert (s, o) == ("repair", "rejected"), f"admit from repair -> {(s, o)}"
    s, o, _ = c.m.apply_event("schedulable", "fault_confirmed", "x", ctx)
    assert (s, o) == ("schedulable", "rejected"), f"fault_confirmed on schedulable -> {(s, o)}"
    s, o, _ = c.m.apply_event("retired", "image_complete", "x", ctx)
    assert (s, o) == ("retired", "rejected"), f"image_complete on retired -> {(s, o)}"
    s, o, _ = c.m.apply_event("imaged", "acceptance_complete", "x", ctx)
    assert (s, o) == ("repair", "applied"), f"acceptance_complete without evidence -> {(s, o)}; expected repair"
    s, o, _ = c.m.apply_event("validated", "admit", "x",
                              {"acceptance": {"x": {"passed": True, "failures": []}},
                               "compat": {"x": {"status": "canary", "bundle": "B", "reasons": []}}})
    assert o == "rejected", "admit must require a golden bundle"
    return "noop / rejected / guard semantics correct"


def c_replay_states(c: Ctx) -> str:
    states = c.states()
    before = dict(states)
    final, journal = c.m.replay(states, c.d["events"], {"acceptance": c.acceptance(), "compat": c.compat()})
    assert states == before, "replay mutated its input"
    wrong = {n: (final.get(n), exp) for n, exp in EXPECTED_FINAL.items() if final.get(n) != exp}
    assert not wrong, f"final state (got, expected): {wrong}"
    return f"{len(EXPECTED_FINAL)} audited nodes end in the expected state"


def c_replay_delivery(c: Ctx) -> str:
    _, journal = c.m.replay(c.states(), c.d["events"], {"acceptance": c.acceptance(), "compat": c.compat()})
    assert len(journal) == len(c.d["events"]), "journal must have one entry per input event"
    dups = [j["event_id"] for j in journal if j["outcome"] == "duplicate"]
    assert dups == ["ev-0028"], f"duplicates detected: {dups}"
    order = [j["event_id"] for j in journal if j["node"] == "orion-n13"]
    assert order == ["ev-0033", "ev-0034"], f"orion-n13 processed as {order}; events must be time-ordered"
    return "at-most-once delivery and time ordering enforced"


def c_replay_gates(c: Ctx) -> str:
    acc, comp = c.acceptance(), c.compat()
    _, journal = c.m.replay(c.states(), c.d["events"], {"acceptance": acc, "compat": comp})
    admitted = [j["node"] for j in journal if j["event"] == "admit" and j["outcome"] == "applied"]
    bad = [n for n in admitted if not acc[n]["passed"] or comp[n]["status"] != "golden"]
    assert not bad, f"admitted without passing gates: {bad}"
    rej = {j["event_id"] for j in journal if j["outcome"] == "rejected"}
    need = {"ev-0023", "ev-0024", "ev-0026", "ev-0027", "ev-0032"}
    assert need <= rej, f"events that must be rejected but were not: {sorted(need - rej)}"
    return f"{len(admitted)} admissions, all gated; {len(rej)} unsafe events rejected"


def c_waves(c: Ctx) -> str:
    nodes = c.wave_nodes()
    cons = c.d["constraints"]
    waves = c.m.plan_waves(nodes, cons)
    good = set(cons["eligible_compat"])
    elig = sorted(n["node"] for n in nodes if n["state"] in cons["eligible_states"] and n["compat_status"] in good)
    flat = [x for w in waves for x in w]
    assert sorted(flat) == elig and len(flat) == len(set(flat)), "every eligible node exactly once, nothing else"
    info = {n["node"]: n for n in nodes}
    assert len(waves[0]) == cons["canary_size"] and len({info[x]["rack"] for x in waves[0]}) == len(waves[0]),         "wave 0 must be the canary on distinct racks"
    # Per-partition headroom: schedulable nodes that stay in service (non-compliant ones are drained by T7).
    floors = cons["partition_floors"]
    stay: dict = {}
    for n in nodes:
        if n["state"] == "schedulable" and n["compat_status"] in good:
            stay[n["partition"]] = stay.get(n["partition"], 0) + 1
    head = {p: stay[p] - floors[p] for p in floors}
    total_cap = math.floor(cons["max_wave_fraction"] * len(elig))
    for i, w in enumerate(waves):
        assert len(w) <= total_cap, f"wave {i} has {len(w)} nodes > {total_cap}"
        racks = [info[x]["rack"] for x in w]
        assert max(racks.count(r) for r in set(racks)) <= cons["max_nodes_per_rack_per_wave"], f"wave {i} rack cap"
        for p in floors:
            k = sum(1 for x in w if info[x]["partition"] == p)
            assert k <= head[p], f"wave {i} takes {k} {p} nodes: {p} would fall below its floor of {floors[p]}"
    # Minimum possible number of waves given the rack and partition limits.
    can = {p: sum(1 for x in waves[0] if info[x]["partition"] == p) for p in floors}
    lb = max([1 + math.ceil((sum(1 for x in elig if info[x]["partition"] == p) - can[p]) / head[p]) for p in floors]
             + [max(sum(1 for x in elig if info[x]["rack"] == r) for r in {info[x]["rack"] for x in elig})])
    assert len(waves) == lb, f"{len(waves)} waves; the limits allow {lb}"
    dep = [x for x in elig if info[x]["compat_status"] in cons.get("prefer_first", [])]
    pos = {x: i for i, w in enumerate(waves) for x in w}
    others = [pos[x] for x in elig if x not in dep and info[x]["partition"] == "inference"]
    assert all(pos[d] <= min(others) for d in dep if info[d]["partition"] == "inference") if others else True,         "expiring-bundle nodes must be upgraded before golden nodes in the same partition"
    return (f"{len(elig)} eligible nodes in {len(waves)} waves (minimum); headroom per wave "
            f"training {head['training']}, inference {head['inference']}; expiring bundle first")


def c_waves_refuse(c: Ctx) -> str:
    cons = copy.deepcopy(c.d["constraints"])
    cons["partition_floors"]["inference"] = 7   # orion-n30 is about to be drained: only 7 inference nodes stay
    try:
        c.m.plan_waves(c.wave_nodes(), cons)
    except ValueError:
        return "refuses when a partition floor leaves no headroom (pending drain counted)"
    raise AssertionError("plan_waves must raise ValueError: inference keeps 7 compliant nodes, floor 7")


def c_canary(c: Ctx) -> str:
    th = c.d["constraints"]["canary_thresholds"]
    got = {s: c.m.canary_decision(g, th) for s, g in c.d["canary"].groupby("scenario")}
    exp = {"S1": "promote", "S2": "abort", "S3": "extend", "S4": "abort"}
    wrong = {s: got[s][0] for s in exp if got[s][0] != exp[s]}
    assert not wrong, f"decisions {wrong}; expected {exp}"
    assert any("orion-n01" in r for r in got["S2"][1]), "S2 reason must name the regressed canary"
    assert any("orion-n25" in r for r in got["S4"][1]), "S4 reason must name the canary with the Xid"
    return "S1 promote, S2 abort (worst canary), S3 extend, S4 abort (Xid)"


def c_remediation(c: Ctx) -> str:
    plan = c.m.plan_remediation(c.d["inventory"], c.d["matrix"], "B-2026.07")
    assert plan == c.m.plan_remediation(c.d["inventory"], c.d["matrix"], "B-2026.07"), "not deterministic"
    by = {}
    for a in plan:
        by.setdefault(a["node"], []).append((a["step"], a["action"]))
    assert by.get("orion-n30") == [(1, "drain"), (2, "reimage")], f"orion-n30: {by.get('orion-n30')}"
    assert by.get("orion-n20") == [(1, "reimage")], f"orion-n20 (already drained): {by.get('orion-n20')}"
    for i in range(1, 5):
        assert by.get(f"orion-n{24 + i:02d}") == [(1, "schedule_upgrade")], f"orion-n{24 + i:02d}: {by.get(f'orion-n{24 + i:02d}')}"
    extra = set(by) - {"orion-n30", "orion-n20"} - {f"orion-n{24 + i:02d}" for i in range(1, 5)}
    assert not extra, f"unexpected actions for {sorted(extra)} (repair/discovered/retired nodes belong to the lifecycle flow)"
    return f"{len(plan)} actions; blocked node drained before reimage"


def c_converged(c: Ctx) -> str:
    golden = next(b for b in c.d["matrix"] if b["status"] == "golden")
    inv = copy.deepcopy(c.d["inventory"])
    for r in inv:
        for f in c.m.BUNDLE_FIELDS:
            r[f] = golden[f]
        r["gpu_vbios"] = ";".join([golden["gpu_vbios"]] * 8)
    plan = c.m.plan_remediation(inv, c.d["matrix"], golden["bundle_id"])
    assert plan == [], f"converged fleet must produce an empty plan, got {len(plan)} actions"
    return "converged fleet -> empty plan (idempotent)"


def c_audit_planted(c: Ctx) -> str:
    bad = c.m.audit_verify(c.d["audit"])
    assert bad == 23, f"expected first broken record seq 23, got {bad}"
    return "tampered record seq 23 detected"


def c_audit_roundtrip(c: Ctx) -> str:
    chain: list = []
    for i in range(5):
        entry = {"utc": f"2026-10-29T0{i}:00:00Z", "actor": "fleet-bot", "node": "orion-n01",
                 "event": "drain", "from_state": "schedulable", "to_state": "drained", "ticket": f"CHG-{i}"}
        snapshot = dict(entry)
        new = c.m.audit_append(chain, entry)
        assert entry == snapshot and len(chain) == i, "audit_append mutated its inputs"
        chain = new
    assert c.m.audit_verify(chain) is None, "fresh chain should verify"
    t = copy.deepcopy(chain)
    t[2]["to_state"] = "repair"
    assert c.m.audit_verify(t) == 3, "edited record not detected"
    d = chain[:2] + chain[3:]
    assert c.m.audit_verify(d) == 4, "deleted record not detected"
    # Rebuilding the untampered prefix of the exported log must reproduce its hashes.
    rebuilt: list = []
    for rec in c.d["audit"][:22]:
        rebuilt = c.m.audit_append(rebuilt, {k: v for k, v in rec.items() if k not in ("seq", "prev_hash", "hash")})
    assert [r["hash"] for r in rebuilt] == [r["hash"] for r in c.d["audit"][:22]], "hash format differs from controller"
    return "append/verify detect edits and deletions; hashes match the controller export"


CHECKS: list[tuple[str, Callable[[Ctx], str]]] = [
    ("dataset deterministic", c_data),
    ("T1 state machine shape", c_spec_shape),
    ("T1 state machine safety", c_spec_safety),
    ("T2 acceptance: planted failures", c_acceptance_planted),
    ("T2 acceptance: policy-driven thresholds", c_acceptance_policy_driven),
    ("T3 compatibility classification", c_compat),
    ("T4 event rules (noop/reject/guards)", c_apply_rules),
    ("T4 replay: final states", c_replay_states),
    ("T4 replay: duplicates and ordering", c_replay_delivery),
    ("T4 replay: admission gates", c_replay_gates),
    ("T5 rollout waves", c_waves),
    ("T5 rollout refuses unsafe constraints", c_waves_refuse),
    ("T6 canary gate", c_canary),
    ("T7 remediation plan", c_remediation),
    ("T7 remediation idempotent", c_converged),
    ("T8 audit: planted tamper", c_audit_planted),
    ("T8 audit: append/verify", c_audit_roundtrip),
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
        print(f"FAIL  load_dataset -- {type(exc).__name__}: {exc}")
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
