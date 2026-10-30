#!/usr/bin/env python3
"""Checker for the Chapter 16 lab (bare-metal fleet lifecycle).

    python check.py                    # check your starter/ implementation (default)
    python check.py --impl solution    # check the instructor reference (exit 0 expected)

Prints one line per check: PASS / FAIL / TODO + name + reason. Exit code 0 only if all pass.
Fixture-based checks give you targeted feedback; dataset checks compare a SHA-256 digest of your
results so the expected answers are not revealed here.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Any, Callable

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
IMPLS = {"starter": HERE / "starter" / "fleet_lifecycle.py",
         "solution": HERE.parent / "solutions" / "lab" / "fleet_lifecycle.py"}

DIGEST_ACCEPTANCE = "d3f2cf5a04a138add20f384290d24d3c7d649368e808590056124bf6afabac92"
DIGEST_AUDIT = "d10c6e62ed09fea2706fea054232b2d0f91a64c58391d077d66d0a3506bc2587"
DIGEST_FINAL = "ffe10e738ac3d395a8daa99286cd24a18a0321684536846d3e52f3d60641cac9"
TARGET = "B-2026.10"


class CheckFail(Exception):
    pass


def expect(cond: bool, msg: str) -> None:
    if not cond:
        raise CheckFail(msg)


def sha(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load_impl(name: str):
    path = IMPLS[name]
    spec = importlib.util.spec_from_file_location(f"fleet_lifecycle_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--impl", choices=sorted(IMPLS), default="starter")
    args = ap.parse_args()
    t0 = time.perf_counter()
    m = load_impl(args.impl)

    policy = m.load_yaml(DATA / "acceptance_policy.yaml")
    matrix = m.load_yaml(DATA / "compat_matrix.yaml")
    results = m.load_json(DATA / "acceptance_results.json")
    inventory = m.load_json(DATA / "inventory.json")
    events = m.load_json(DATA / "lifecycle_events.json")
    bundles = {b["id"]: b for b in matrix["bundles"]}
    clean = copy.deepcopy(results[0])  # orion-n01 is a clean node

    checks: list[tuple[str, Callable[[], None]]] = []

    def check(name: str):
        def deco(fn):
            checks.append((name, fn))
            return fn
        return deco

    # ---------------- Task 1: compatibility matrix ----------------
    @check("T1.compat_exact_production")
    def _():
        r = m.check_compat(dict(bundles["B-2026.04"]["versions"]), matrix)
        expect(r["status"] == "OK" and r["bundle"] == "B-2026.04", f"got {r}")
        expect(r["mismatches"] == [] and r["blocked"] == [], f"got {r}")

    @check("T1.compat_deprecated")
    def _():
        r = m.check_compat(dict(bundles["B-2025.11"]["versions"]), matrix)
        expect(r["status"] == "DEPRECATED" and r["bundle"] == "B-2025.11", f"got {r}")

    @check("T1.compat_list_values_and_blocked")
    def _():
        fw = dict(bundles["B-2026.04"]["versions"])
        fw["nic_fw"] = ["28.41.1000"] * 7 + ["28.42.1000"]
        r = m.check_compat(fw, matrix)
        expect(r["status"] == "BLOCKED", f"one NIC on a blocked fw must give BLOCKED, got {r['status']}")
        expect(r["blocked"] == ["nic_fw=28.42.1000"], f"blocked list {r['blocked']}")
        expect(r["closest"] == "B-2026.04" and r["mismatches"] == ["nic_fw"], f"closest/mismatches {r}")

    @check("T1.compat_off_matrix_closest")
    def _():
        fw = dict(bundles["B-2026.10"]["versions"])
        fw["bios"] = "2.5.0"
        r = m.check_compat(fw, matrix)
        expect(r["status"] == "OFF_MATRIX" and r["bundle"] is None, f"got {r}")
        expect(r["closest"] == "B-2026.10" and r["mismatches"] == ["bios"], f"got {r}")

    # ---------------- Task 2: acceptance evaluator ----------------
    def ev(mutator: Callable[[dict], None] | None = None) -> dict:
        node = copy.deepcopy(clean)
        if mutator:
            mutator(node)
        return m.evaluate_node(node, policy, matrix)

    @check("T2.clean_node_passes")
    def _():
        r = ev()
        expect(r["verdict"] == "PASS" and r["codes"] == [], f"orion-n01 should PASS, got {r['verdict']} {r['codes']}")

    @check("T2.distractors_do_not_fail")
    def _():
        def mut(n):
            for g in n["gpus"]:
                g["pcie"]["gen_idle"] = 1
                g["burn_in"]["throttle_reasons"] = ["SW_POWER_CAP"]
        r = ev(mut)
        expect(r["verdict"] == "PASS", f"idle link down-training, SW_POWER_CAP and 200G frontend NICs are normal; got {r['codes']}")

    fixtures = {
        "GPU_COUNT": lambda n: n["gpus"].pop(),
        "PCIE_DEGRADED": lambda n: n["gpus"][2]["pcie"].__setitem__("width", 8),
        "NIC_SPEED": lambda n: n["nics"][3].__setitem__("speed_mbps", 200000),
        "FW_OFF_MATRIX": lambda n: n["nics"][0].__setitem__("fw", "28.40.9999"),
        "THERMAL_THROTTLE": lambda n: n["gpus"][5]["burn_in"].__setitem__("throttle_reasons", ["HW_THERMAL_SLOWDOWN"]),
        "HBM_ROW_REMAP_PENDING": lambda n: n["gpus"][1]["row_remap"].__setitem__("pending", True),
        "NVLINK_DOWN": lambda n: n["gpus"][0].__setitem__("nvlink_links_up", 17),
        "ECC_DBE": lambda n: n["gpus"][4]["ecc"].__setitem__("dbe_volatile", 1),
        "RDMA_PAIR_BW_LOW": lambda n: n["nics"][6].__setitem__("rdma_pair_bw_gbps", 300.0),
        "NCCL_BUSBW_LOW": lambda n: n["nccl_single_node"].__setitem__("busbw_gbs", 310.0),
        "NCCL_ALGO_UNRECORDED": lambda n: n["nccl_single_node"].pop("algorithm"),
        "NIC_MTU": lambda n: n["nics"][2].__setitem__("active_mtu", 1024),
    }
    for code, mut in fixtures.items():
        def _make(code=code, mut=mut):
            def fn():
                r = ev(mut)
                expect(r["verdict"] == "FAIL", f"verdict {r['verdict']}")
                expect(r["codes"] == [code], f"expected exactly [{code}], got {r['codes']}")
            return fn
        checks.append((f"T2.detects_{code}", _make()))

    @check("T2.nccl_floor_follows_algorithm")
    def _():
        def ring_ok(n):
            n["nccl_single_node"].update(algorithm="Ring", busbw_gbs=350.0)
        r = ev(ring_ok)
        expect(r["verdict"] == "PASS", f"350 GB/s with Ring is above the Ring baseline; got {r['codes']}")
        r = ev(lambda n: n["nccl_single_node"].update(algorithm="NVLS", busbw_gbs=350.0))
        expect(r["codes"] == ["NCCL_BUSBW_LOW"], f"350 GB/s with NVLS is below the NVLS baseline; got {r['codes']}")

    @check("T2.sbe_is_warning_not_failure")
    def _():
        r = ev(lambda n: n["gpus"][3]["ecc"].__setitem__("sbe_volatile", 25))
        expect(r["verdict"] == "WARN" and r["warnings"] == ["ECC_SBE_ELEVATED"] and r["codes"] == [], f"got {r}")

    @check("T2.fleet_verdict_counts")
    def _():
        out = m.evaluate_fleet(results, policy, matrix)
        counts = {k: sum(1 for r in out if r["verdict"] == k) for k in ("PASS", "WARN", "FAIL")}
        expect(len(out) == 32, f"{len(out)} results")
        expect(counts == {"PASS": 25, "WARN": 1, "FAIL": 6}, f"verdict counts {counts}")

    @check("T2.fleet_digest")
    def _():
        out = m.evaluate_fleet(results, policy, matrix)
        got = sha([[r["node"], r["verdict"], r["codes"], r["warnings"]] for r in out])
        expect(got == DIGEST_ACCEPTANCE, "per-node codes differ from reference (counts may match, codes do not)")

    # ---------------- Task 3: lifecycle state machine ----------------
    @check("T3.transition_table_shape")
    def _():
        t = m.transition_table()
        expect(len(t) == 13, f"{len(t)} transitions, expected 13")
        expect(not any(s == "retired" for s, _ in t), "retired must be terminal")
        expect(("schedulable", "send_to_repair") not in t, "schedulable nodes must drain before repair")
        into_sched = {s for (s, _), d in t.items() if d == "schedulable"}
        expect(into_sched == {"validated", "draining"}, f"only validated/draining may reach schedulable, got {into_sched}")
        expect(t.get(("imaged", "pass_acceptance")) == "validated", "imaged --pass_acceptance--> validated missing")

    @check("T3.guard_rejects_and_audits")
    def _():
        nodes = {"x": {"node": "x", "state": "draining", "drain": {"reason": "r", "category": "maintenance"},
                       "firmware": {}, "ticket": None}}
        audit: list = []
        ok = m.apply_event(nodes, {"seq": 1, "ts": "t", "node": "x", "event": "drain_complete",
                                   "actor": "a", "evidence": {"running_jobs": 3}}, audit, matrix)
        expect(ok is False and nodes["x"]["state"] == "draining", "drain_complete with running jobs must be rejected")
        expect(len(audit) == 1 and audit[0]["reason_code"] == "JOBS_STILL_RUNNING"
               and audit[0]["result"] == "rejected" and audit[0]["to_state"] is None, f"audit {audit}")
        ok = m.apply_event(nodes, {"seq": 2, "ts": "t", "node": "x", "event": "drain_complete",
                                   "actor": "a", "evidence": {"running_jobs": 0}}, audit, matrix)
        expect(ok is True and nodes["x"]["state"] == "drained" and audit[-1]["result"] == "applied", f"audit {audit[-1]}")
        keys = {"seq", "ts", "node", "event", "actor", "from_state", "to_state", "result", "reason_code"}
        expect(all(keys <= set(a) for a in audit), "audit records missing required keys")

    @check("T3.replay_does_not_mutate_input")
    def _():
        inv = copy.deepcopy(inventory)
        nodes, audit = m.replay(inv, events, matrix)
        expect(inv == inventory, "replay modified the input inventory")
        expect(len(audit) == len(events), f"{len(audit)} audit records for {len(events)} events")
        seqs = [a["seq"] for a in audit]
        expect(seqs == sorted(seqs), "audit log must be in seq order")

    @check("T3.replay_rejections")
    def _():
        _, audit = m.replay(inventory, events, matrix)
        rej = [a for a in audit if a["result"] == "rejected"]
        expect(len(rej) == 13, f"{len(rej)} rejected events, expected 13")
        got = sha([[a["seq"], a["result"], a["reason_code"], a["to_state"]] for a in audit])
        expect(got == DIGEST_AUDIT, "audit log (seq, result, reason_code, to_state) differs from reference")

    @check("T3.replay_final_states")
    def _():
        nodes, _ = m.replay(inventory, events, matrix)
        got = hashlib.sha256(json.dumps(sorted([n, v["state"]] for n, v in nodes.items()),
                                        separators=(",", ":")).encode()).hexdigest()
        expect(got == DIGEST_FINAL, "final node states differ from reference")

    @check("T3.invariant_no_shortcut_to_schedulable")
    def _():
        _, audit = m.replay(inventory, events, matrix)
        bad = [a for a in audit if a["result"] == "applied" and a["to_state"] == "schedulable"
               and a["from_state"] not in ("validated", "draining")]
        expect(not bad, f"nodes reached schedulable without validation: {bad}")

    # ---------------- Task 4: staged upgrade planner ----------------
    def expected_partition():
        tgt = bundles[TARGET]["versions"]
        excl, elig = {}, {}
        for r in inventory:
            if r["state"] != "schedulable":
                excl[r["node"]] = f"state:{r['state']}"
            elif all(r["firmware"].get(k) == v for k, v in tgt.items()):
                excl[r["node"]] = "already_on_target"
            else:
                elig[r["node"]] = r["rack"]
        return excl, elig

    def plan():
        return m.plan_upgrade_waves(copy.deepcopy(inventory), matrix, TARGET,
                                    canary_size=2, max_per_wave=4, max_per_rack_per_wave=1)

    @check("T4.excluded_nodes")
    def _():
        excl, _ = expected_partition()
        p = plan()
        expect(p["excluded"] == excl, f"excluded differs: got {sorted(p['excluded'].items())}")

    @check("T4.coverage_exactly_once")
    def _():
        _, elig = expected_partition()
        p = plan()
        placed = list(p["canary"]) + [n for w in p["waves"] for n in w]
        expect(len(placed) == len(set(placed)), "a node appears more than once")
        expect(set(placed) == set(elig), f"missing {sorted(set(elig) - set(placed))} extra {sorted(set(placed) - set(elig))}")

    @check("T4.canary_and_wave_limits")
    def _():
        _, elig = expected_partition()
        p = plan()
        expect(len(p["canary"]) == 2, f"canary size {len(p['canary'])}")
        expect(len({elig[n] for n in p["canary"]}) == 2, "canary nodes must be in different racks")
        for i, w in enumerate(p["waves"], 1):
            expect(len(w) <= 4, f"wave {i} has {len(w)} nodes (cap 4)")
            racks = [elig[n] for n in w]
            expect(len(racks) == len(set(racks)), f"wave {i} takes 2 nodes from one rack")

    @check("T4.minimal_wave_count")
    def _():
        _, elig = expected_partition()
        p = plan()
        rem: dict[str, int] = {}
        for n, rack in elig.items():
            if n not in p["canary"]:
                rem[rack] = rem.get(rack, 0) + 1
        lb = m.wave_lower_bound(rem, 4, 1)
        expect(len(p["waves"]) == lb, f"{len(p['waves'])} waves, lower bound {lb}")

    @check("T4.deterministic")
    def _():
        expect(plan() == plan(), "plan differs between identical calls")

    # ---------------- run ----------------
    passed = 0
    for name, fn in checks:
        try:
            fn()
            print(f"PASS {name}")
            passed += 1
        except NotImplementedError as e:
            print(f"TODO {name}: {e} not implemented")
        except CheckFail as e:
            print(f"FAIL {name}: {e}")
        except Exception as e:  # noqa: BLE001 -- learner code may raise anything; report, don't crash
            print(f"FAIL {name}: {type(e).__name__}: {e}")
    print(f"\n{passed}/{len(checks)} checks passed ({args.impl}) in {time.perf_counter() - t0:.2f}s")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
