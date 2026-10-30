#!/usr/bin/env python3
"""Checker for the Chapter 17 lab (ORION gang scheduler simulator + pending-job diagnoser).

Usage:
    python check.py                    # check your starter/orion_sched.py (default)
    python check.py --impl solution    # check the reference implementation (instructor copy)

Prints one PASS/FAIL/TODO line per check. Exit code 0 only if every check passes.
Pure Python, no network, no GPU, deterministic, < 5 s.

Expected answers for the supplied datasets are stored as truncated SHA-256 digests so that the
checker can grade your output without revealing the planted answers.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
IMPLS = {
    "starter": HERE / "starter" / "orion_sched.py",
    "solution": HERE.parent / "solutions" / "lab" / "orion_sched.py",
}

EXPECTED_JOB = {
    "J10": "240f79badfc67f58", "J05": "f270a5de1f193072", "J12": "20bca4851eedaca1",
    "J02": "c7c875aede59c7e3", "J03": "7188734b689f464b", "J04": "aca5f35dbe353065",
    "J08": "55d9d0eabfe8b9f3", "J07": "d2d1ae86cf4d66ef", "J11": "c727bf5214f06a16",
    "J13": "a651cf42a027dfe7", "J01": "dd3e928da7636562", "J15": "b7bf6c0092a9f008",
    "J06": "90887d64ce5a3b93", "J14": "fedd130a941b3b4c", "J09": "3f1a38be46fa3b27",
}
EXPECTED_ORDER = "cec9dc4a929b93a5"
EXPECTED_USAGE = "6273d807f121be18"
EXPECTED_CASE = {
    "P01": "e2967f2af58dde75", "P02": "98e2af23c00792ad", "P03": "64e71613974f68b2",
    "P04": "f2c943e71d9586ab", "P05": "f1d413adcfe32d71", "P06": "b81d94282bfab4c6",
    "P07": "f955287d4535a279", "P08": "8bce2454716ed11e", "P09": "e0a9ea98e71267e3",
    "P10": "3bf19f85c203b8e8", "P11": "860ce31fa10c4858", "P12": "20715d90d6df35c0",
}


def h(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:16]


def load_impl(name: str):
    path = IMPLS[name]
    spec = importlib.util.spec_from_file_location(f"orion_sched_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def mk_node(name: str, rack: str = "rack-01", free=range(8), pool: str = "train", **kw) -> dict:
    node = {
        "name": name, "rack": rack, "lifecycle_state": "schedulable", "health": "ok",
        "labels": {"halcyon.ai/pool": pool, "nvidia.com/gpu.product": "NVIDIA-H100-80GB-HBM3"},
        "taints": [], "mig_enabled": False, "rails_up": list(range(8)), "free": set(free),
    }
    node.update(kw)
    return node


def mk_state(nodes: list[dict], quota: int = 1000, used: int = 0) -> dict:
    return {"nodes": {n["name"]: n for n in nodes}, "tenants": {"t": {"quota": quota, "used": used}}}


def mk_job(gpus: int, pool: str = "train", **kw) -> dict:
    job = {"job_id": "X", "tenant": "t", "pool": pool, "gpus": gpus, "priority": 50, "submit_time": 0,
           "node_selector": {}, "tolerations": []}
    job.update(kw)
    return job


# ------------------------------------------------------------------------------------------ checks
def check_tolerates(m) -> tuple[bool, str]:
    ded = [{"key": "halcyon.ai/dedicated", "value": "search", "effect": "NoSchedule"}]
    cases = [
        (ded, [], False),
        (ded, [{"key": "halcyon.ai/dedicated", "operator": "Equal", "value": "search", "effect": "NoSchedule"}], True),
        (ded, [{"key": "halcyon.ai/dedicated", "operator": "Exists"}], True),
        (ded, [{"key": "halcyon.ai/dedicated", "operator": "Equal", "value": "ads", "effect": "NoSchedule"}], False),
        (ded, [{"key": "halcyon.ai/dedicated", "operator": "Equal", "value": "search", "effect": "NoExecute"}], False),
        ([{"key": "a", "value": "b", "effect": "PreferNoSchedule"}], [], True),
        ([], [], True),
    ]
    for i, (taints, tols, want) in enumerate(cases):
        got = m.tolerates(taints, tols)
        if got != want:
            return False, f"case {i}: tolerates({taints}, {tols}) = {got}, expected {want}"
    return True, f"{len(cases)} taint/toleration cases correct (incl. Exists, effect mismatch, PreferNoSchedule)"


def check_node_filter(m) -> tuple[bool, str]:
    job = mk_job(8)
    cases = [
        (mk_node("a", lifecycle_state="draining"), job, False, "NotSchedulable"),
        (mk_node("a", lifecycle_state="repair", health="failed"), job, False, "NotSchedulable"),
        (mk_node("a", health="failed"), job, False, "Unhealthy"),
        (mk_node("a", pool="infer"), job, False, "PoolMismatch"),
        (mk_node("a"), mk_job(8, node_selector={"nvidia.com/gpu.product": "NVIDIA-H100-SXM5-80GB"}), False,
         "SelectorMismatch"),
        (mk_node("a", taints=[{"key": "k", "value": "v", "effect": "NoSchedule"}]), job, False, "UntoleratedTaint"),
        (mk_node("a", mig_enabled=True), job, False, "MIGEnabled"),
        (mk_node("a", rails_up=[0, 1, 2, 4, 5, 6, 7]), mk_job(16), True, "RailIncomplete"),
        (mk_node("a", rails_up=[0, 1, 2, 4, 5, 6, 7]), job, False, None),
        (mk_node("a", health="degraded"), job, False, None),
    ]
    for i, (node, j, multi, want) in enumerate(cases):
        got = m.node_filter(node, j, multi)
        if got != want:
            return False, f"case {i}: expected {want!r}, got {got!r}"
    return True, f"{len(cases)} filter cases correct (order and codes)"


def check_select_gpus(m) -> tuple[bool, str]:
    cases = [
        (range(8), 8, (list(range(8)), True)),
        ({2, 3, 5, 6, 7}, 2, ([2, 3], True)),        # best-fit socket (socket 0 has exactly 2)
        ({2, 3, 5, 6, 7}, 3, ([5, 6, 7], True)),
        ({0, 1, 2, 3, 4, 5, 6, 7}, 4, ([0, 1, 2, 3], True)),
        ({1, 2, 5, 6}, 4, ([1, 2, 5, 6], False)),    # cannot align -> split
        ({0, 1, 2, 3, 6, 7}, 6, ([0, 1, 2, 3, 6, 7], True)),
        ({0, 1}, 4, None),
    ]
    for i, (free, n, want) in enumerate(cases):
        got = m.select_gpus(set(free), n)
        got_n = None if got is None else (list(got[0]), bool(got[1]))
        if got_n != want:
            return False, f"case {i}: select_gpus({sorted(free)}, {n}) = {got_n}, expected {want}"
    return True, f"{len(cases)} GPU-selection cases correct (socket best-fit)"


def check_place_single(m) -> tuple[bool, str]:
    # Best-fit + prefer rail-degraded node for single-node work.
    st = mk_state([mk_node("n-a"), mk_node("n-b", rails_up=[0, 1, 2, 4, 5, 6, 7]),
                   mk_node("n-c", free={4, 5, 6, 7})])
    r = m.place_job(st, mk_job(8))
    if r.get("status") != "placed" or list(r["nodes"]) != ["n-b"]:
        return False, f"8-GPU single-node job should prefer the rail-degraded node n-b, got {r}"
    r = m.place_job(st, mk_job(4))
    if r.get("status") != "placed" or r["nodes"] != {"n-c": [4, 5, 6, 7]}:
        return False, f"4-GPU job should best-fit onto n-c [4,5,6,7], got {r}"
    if st["tenants"]["t"]["used"] != 12 or st["nodes"]["n-c"]["free"]:
        return False, "state not updated after placement (tenant used / node free)"
    r = m.place_job(st, mk_job(12))
    if r != {"status": "pending", "reason": "InvalidRequest"}:
        return False, f"12-GPU request must be InvalidRequest, got {r}"
    st2 = mk_state([mk_node("n-a")], quota=8, used=4)
    r = m.place_job(st2, mk_job(8))
    if r != {"status": "pending", "reason": "QuotaExceeded"}:
        return False, f"quota 8 with 4 used must reject an 8-GPU job, got {r}"
    return True, "best-fit, rail-preference, state update, InvalidRequest, QuotaExceeded"


def check_place_gang(m) -> tuple[bool, str]:
    nodes = [mk_node("n01", "rack-01"), mk_node("n05", "rack-02"), mk_node("n06", "rack-02"),
             mk_node("n09", "rack-03", free={0, 1, 2, 3}), mk_node("n10", "rack-03", free={4, 5, 6, 7})]
    st = mk_state(nodes)
    before = copy.deepcopy({k: sorted(v["free"]) for k, v in st["nodes"].items()})
    r = m.place_job(st, mk_job(32))
    after = {k: sorted(v["free"]) for k, v in st["nodes"].items()}
    if r != {"status": "pending", "reason": "Fragmentation"}:
        return False, f"32-GPU gang with 3 whole nodes + 8 scattered GPUs must be Fragmentation, got {r}"
    if before != after or st["tenants"]["t"]["used"] != 0:
        return False, "a pending gang job must not consume any GPUs (all-or-nothing)"
    r = m.place_job(st, mk_job(16))
    if r.get("status") != "placed" or sorted(r["nodes"]) != ["n05", "n06"]:
        return False, f"16-GPU gang should be rack-compact on rack-02 (n05, n06), got {r}"
    r = m.place_job(st, mk_job(16))
    if r != {"status": "pending", "reason": "Fragmentation"}:
        return False, f"16-GPU gang with 16 free GPUs but only 1 whole node must be Fragmentation, got {r}"
    r = m.place_job(st, mk_job(24))
    if r != {"status": "pending", "reason": "InsufficientCapacity"}:
        return False, f"24-GPU gang with only 16 free GPUs must be InsufficientCapacity, got {r}"
    return True, "all-or-nothing, Fragmentation vs InsufficientCapacity, rack-compact selection"


def run_schedule(m):
    cluster = m.load_json(DATA / "cluster_state.json")
    jobs = m.load_json(DATA / "job_queue.json")
    return cluster, jobs, m.schedule(cluster, jobs)


def check_schedule_invariants(m) -> tuple[bool, str]:
    cluster, jobs, out = run_schedule(m)
    nodes = {n["name"]: n for n in cluster["nodes"]}
    used = {n: set(v["gpus_allocated"]) for n, v in nodes.items()}
    jobs_by_id = {j["job_id"]: j for j in jobs}
    if sorted(out["results"]) != sorted(jobs_by_id):
        return False, "results must contain every job exactly once"
    for jid, r in out["results"].items():
        if r["status"] != "placed":
            continue
        j = jobs_by_id[jid]
        got = sum(len(v) for v in r["nodes"].values())
        if got != j["gpus"]:
            return False, f"{jid}: placed {got} GPUs, requested {j['gpus']} (gang must be exact)"
        for n, idx in r["nodes"].items():
            node = nodes[n]
            if node["lifecycle_state"] != "schedulable":
                return False, f"{jid}: placed on {n} in lifecycle state {node['lifecycle_state']}"
            if node["labels"]["halcyon.ai/pool"] != j["pool"]:
                return False, f"{jid}: placed on {n} outside its pool"
            if node["mig_enabled"]:
                return False, f"{jid}: whole-GPU job placed on MIG node {n}"
            if j["gpus"] > 8 and len(node["rails_up"]) < 8:
                return False, f"{jid}: multi-node job placed on rail-incomplete node {n}"
            if used[n] & set(idx):
                return False, f"{jid}: GPU(s) {sorted(used[n] & set(idx))} on {n} double-allocated"
            used[n] |= set(idx)
    for t, u in out["tenant_used"].items():
        if u > cluster["tenants"][t]["gpu_quota"]:
            return False, f"tenant {t} over quota: {u} > {cluster['tenants'][t]['gpu_quota']}"
    placed = sum(1 for r in out["results"].values() if r["status"] == "placed")
    return True, f"{placed}/{len(jobs)} placed; no overcommit, gangs exact, eligibility and quotas respected"


def check_schedule_exact(m) -> tuple[bool, str]:
    _, _, out = run_schedule(m)
    wrong = [jid for jid, want in EXPECTED_JOB.items()
             if h(jid + "|" + json.dumps(out["results"].get(jid), sort_keys=True)) != want]
    if wrong:
        return False, f"{len(EXPECTED_JOB) - len(wrong)}/{len(EXPECTED_JOB)} jobs match the reference; " \
                      f"differences in: {', '.join(sorted(wrong))}"
    return True, f"all {len(EXPECTED_JOB)} placements/pending reasons match the reference"


def check_schedule_order(m) -> tuple[bool, str]:
    _, _, out = run_schedule(m)
    if h("|".join(out["order"])) != EXPECTED_ORDER:
        return False, f"attempt order differs from the priority + dynamic fair-share spec; yours: {out['order']}"
    if h(json.dumps(out["tenant_used"], sort_keys=True)) != EXPECTED_USAGE:
        return False, f"final tenant usage differs from the reference: {out['tenant_used']}"
    return True, "attempt order and final tenant usage match"


def check_diagnoser(m) -> tuple[bool, str]:
    cases = m.load_json(DATA / "pending_cases.json")
    wrong = []
    for case in cases:
        got = m.diagnose_pending(copy.deepcopy(case))
        if h(case["case_id"] + "|" + ",".join(got)) != EXPECTED_CASE[case["case_id"]]:
            wrong.append(case["case_id"])
    if wrong:
        return False, f"{len(cases) - len(wrong)}/{len(cases)} cases correct; revisit: {', '.join(sorted(wrong))}"
    return True, f"all {len(cases)} pending-job evidence bundles diagnosed correctly"


CHECKS = [
    ("T1 tolerates", check_tolerates),
    ("T2 node_filter", check_node_filter),
    ("T3 select_gpus", check_select_gpus),
    ("T4 place_job single-node", check_place_single),
    ("T4 place_job gang", check_place_gang),
    ("T5 schedule invariants", check_schedule_invariants),
    ("T5 schedule exact match", check_schedule_exact),
    ("T5 schedule order/fairness", check_schedule_order),
    ("T6 diagnose_pending", check_diagnoser),
]


def main() -> int:
    ap = argparse.ArgumentParser(description="Chapter 17 lab checker")
    ap.add_argument("--impl", choices=sorted(IMPLS), default="starter")
    args = ap.parse_args()
    try:
        mod = load_impl(args.impl)
    except Exception as exc:  # syntax error etc. in learner code
        print(f"FAIL import {IMPLS[args.impl].name}: {type(exc).__name__}: {exc}")
        return 2
    passed = 0
    for name, fn in CHECKS:
        try:
            ok, msg = fn(mod)
            status = "PASS" if ok else "FAIL"
        except NotImplementedError as exc:
            ok, status, msg = False, "TODO", str(exc) or "not implemented yet"
        except Exception as exc:  # report learner bugs without a traceback
            ok, status, msg = False, "FAIL", f"{type(exc).__name__}: {exc}"
        passed += ok
        print(f"{status:4s}  {name:30s} {msg}")
    print(f"\n{passed}/{len(CHECKS)} checks passed ({args.impl})")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
