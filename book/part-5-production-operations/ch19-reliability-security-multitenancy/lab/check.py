#!/usr/bin/env python3
"""Checker for the Chapter 19 lab (ORION-XL incident: correlation, containment, recovery, FMEA, isolation).

Usage:
    python check.py                    # check your starter/ implementation (default)
    python check.py --impl solution    # check the reference implementation (instructors)

Prints one line per check (PASS / FAIL / TODO) and exits 0 only if every check passes.
Pure Python, no hardware, no network, < 60 s.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
FILES = ("rank_map.csv", "rank_progress.csv", "gpu_health.csv", "host_nic_snapshot.csv", "switch_port_counters.csv",
         "events.jsonl", "checkpoints.csv", "restart_history.csv", "spares.csv", "hypotheses.yaml", "fmea.csv",
         "tenants.yaml", "isolation_policy.yaml")


def T(hms: str) -> pd.Timestamp:
    return pd.Timestamp(f"2026-10-20T{hms}Z")


def load_impl(impl: str) -> ModuleType:
    path = HERE / "starter" / "incident_toolkit.py" if impl == "starter" else \
        HERE.parent / "solutions" / "lab" / "incident_toolkit.py"
    spec = importlib.util.spec_from_file_location(f"incident_toolkit_{impl}", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Ctx:
    def __init__(self, m: ModuleType) -> None:
        self.m = m
        self.b: dict[str, Any] = m.load_incident(DATA)


def check_reproducible(c: Ctx) -> tuple[bool | None, str]:
    if not (HERE / "tools" / "generate_data.py").exists():
        return None, "generator not shipped (instructor copy only); data integrity not re-checked"
    with tempfile.TemporaryDirectory() as td:
        subprocess.run([sys.executable, str(HERE / "tools" / "generate_data.py"), "--out", td],
                       check=True, capture_output=True)
        for n in FILES:
            if hashlib.sha256((DATA / n).read_bytes()).digest() != hashlib.sha256((Path(td) / n).read_bytes()).digest():
                return False, f"{n} differs from regenerated copy"
    size = sum((DATA / n).stat().st_size for n in FILES)
    return size < 2_000_000, f"generator reproduces committed data byte-for-byte ({size/1e6:.2f} MB)"


def check_parsers(c: Ctx) -> tuple[bool, str]:
    x = c.m.parse_xid("NVRM: Xid (PCI:0000:5D:00): 63, pid='<unknown>', name=<unknown>, Row remapping event")
    y = c.m.parse_netib("h:1:2 [5] NCCL WARN NET/IB : Got completion from peer 10.135.1.167<40685> with status=12 "
                        "opcode=0 len=0 vendor err 129 (Send) hca mlx5_5")
    none_ok = c.m.parse_xid("mlx5_core 0000:aa:00.0: Link down") is None and c.m.parse_netib("hello") is None
    ok = x == {"pci": "0000:5d:00", "xid": 63} and y == {"peer_ip": "10.135.1.167", "status": 12, "hca": "mlx5_5"} \
        and none_ok
    data_xids = [r for r in (c.m.parse_xid(m) for m in c.b["events"].message) if r]
    ok = ok and data_xids == [{"pci": "0000:5d:00", "xid": 63}]
    return ok, f"xid={x}; netib={y}; non-matching -> None: {none_ok}; Xids parsed from events.jsonl={data_xids}"


def check_mapping(c: Ctx) -> tuple[bool, str]:
    hw = c.m.rank_to_hardware(c.b["rank_map"], 1693)
    r = c.m.gpu_bdf_to_rank(c.b["rank_map"], "orionxl-n389", "0000:5d:00")
    ok = (hw["node"], hw["hca"], hw["leaf"], hw["leaf_port"], int(hw["numa"])) == \
        ("orionxl-n212", "mlx5_5", "orionxl-be-leaf-p06-r5", "Ethernet20/1", 1) and r == 3107
    return ok, f"rank 1693 -> {hw['node']} {hw['hca']} {hw['leaf']}:{hw['leaf_port']} NUMA {hw['numa']}; " \
               f"Xid PCI 0000:5d:00 on orionxl-n389 -> rank {r} (expect 3107)"


def check_stuck_group(c: Ctx) -> tuple[bool, str]:
    st = c.m.stuck_ranks(c.b["rank_progress"])
    hw = c.m.common_hardware(c.b["rank_map"], st)
    ok = len(st) == 64 and hw["rails"] == {5} and hw["pp_stages"] == {3} and hw["nodes"] == 64
    return ok, f"{len(st)} stuck ranks; rails={hw['rails']} pp_stages={hw['pp_stages']} leaves={sorted(hw['leaves'])}"


def check_implicate(c: Ctx) -> tuple[bool, str]:
    top = c.m.implicate_links(c.b["events"], c.b["rank_map"], job="900211")
    bp = c.m.bad_ports(c.b["switch_port_counters"])
    ok = top[0][:2] == ("orionxl-n212", "mlx5_5") and top[0][2] > top[1][2] and len(bp) == 1 \
        and bp.iloc[0]["peer_node"] == "orionxl-n212" and int(bp.iloc[0]["link_downs"]) == 4
    return ok, f"top endpoint {top[0]}; bad ports={list(zip(bp.switch, bp.port))} link_downs=" \
               f"{list(bp.link_downs) if len(bp) else []}"


def check_gpu_actions(c: Ctx) -> tuple[bool, str]:
    a = c.m.gpu_actions(c.b["gpu_health"])
    got = {(r.node, int(r.gpu), r.action) for r in a.itertuples()}
    exp = {("orionxl-n389", 3, "drain_reset_validate"), ("orionxl-n046", 6, "monitor"), ("orionxl-s00", 2, "quarantine_rma")}
    return got == exp, f"{sorted(got)}"


def check_hypotheses(c: Ctx) -> tuple[bool, str]:
    got = c.m.classify_hypotheses(c.b)
    exp = {"H1": "proven_cause", "H2": "real_fault_not_cause", "H3": "correlation_only",
           "H4": "correlation_only", "H5": "correlation_only", "H6": "refuted"}
    wrong = {k: v for k, v in got.items() if exp.get(k) != v}
    return not wrong and len(got) == 6, f"classification={got}" + (f"; WRONG {wrong}" if wrong else "")


def check_checkpoint(c: Ctx) -> tuple[bool, str]:
    ck = c.m.select_checkpoint(c.b["checkpoints"], T("03:41:02"))
    met = c.m.recovery_metrics(T("03:41:02"), T("03:10:00"), T("04:31:00"), 4096)
    ok = ck == "ckpt-0084" and abs(met["rpo_min"] - 31.03) < 0.1 and abs(met["rto_min"] - 49.97) < 0.1 \
        and abs(met["lost_gpu_hours"] - 5529.6) < 1
    return ok, f"checkpoint={ck} (ckpt-0085 lacks committed metadata); metrics={met}"


def check_retry_policy(c: Ctx) -> tuple[bool, str]:
    off = c.m.repeat_offenders(c.b["events"], c.b["rank_map"])
    dec = c.m.auto_restart_allowed(c.b["restart_history"], T("03:52:15"), off)
    dec2 = c.m.auto_restart_allowed(c.b["restart_history"], T("03:52:15"), set())
    ok = off == {"orionxl-n212"} and dec["allowed"] is False and dec2["allowed"] is True
    return ok, f"repeat offenders={off}; restart allowed with offender={dec['allowed']}, after exclusion={dec2['allowed']}"


def check_restart_plan(c: Ctx) -> tuple[bool, str]:
    p = c.m.restart_plan(c.b, ["orionxl-n212", "orionxl-n389"], "ckpt-0084")
    rm = c.b["rank_map"]
    moved = set(p["remapped_ranks"])
    exp_ranks = set(rm[rm.node.isin(["orionxl-n212", "orionxl-n389"])]["rank"])
    ok = p["node_map"] == {"orionxl-n212": "orionxl-s01", "orionxl-n389": "orionxl-s03"} and moved == exp_ranks \
        and p["checkpoint"] == "ckpt-0084"
    return ok, f"node_map={p['node_map']} (orionxl-s00 failed acceptance, orionxl-s02 in repair); {len(moved)} ranks remapped"


def check_fmea(c: Ctx) -> tuple[bool, str]:
    df = c.m.fmea_score(c.b["fmea"])
    issues = {r.id: r.issue for r in df.itertuples() if r.issue}
    act = set(df[df.action_required].id)
    ok = df.iloc[0]["id"] == "F03" and int(df.iloc[0]["rpn"]) == 336 and \
        issues == {"F07": "DETECTION_INCONSISTENT", "F11": "OUT_OF_RANGE"} and act == {"F03", "F06", "F07", "F12"}
    return ok, f"top={df.iloc[0]['id']} RPN {df.iloc[0]['rpn']}; issues={issues}; action_required={sorted(act)}"


def check_isolation(c: Ctx) -> tuple[bool, str]:
    got = c.m.check_isolation(c.b["tenants"], c.b["isolation_policy"])
    exp = {("acme-research", "RBAC_FORBIDDEN_ROLE"), ("acme-research", "SHARED_IB_PKEY"),
           ("borealis", "NO_SCRUB"), ("borealis", "SECRETS_SCOPE"), ("borealis", "SHARED_VNI"),
           ("borealis", "STORAGE_OVERLAP"), ("cobalt-inference", "AUDIT_RETENTION"),
           ("cobalt-inference", "GPU_SHARING_NOT_MIG"), ("cobalt-inference", "SHARED_IB_PKEY"),
           ("cobalt-inference", "SHARED_VNI")}
    return got == exp, f"{len(got)} violations; missing={sorted(exp - got)}; unexpected={sorted(got - exp)}"


CHECKS: list[tuple[str, Callable[[Ctx], tuple[bool | None, str]]]] = [
    ("dataset reproducible", check_reproducible),
    ("T1 log parsers", check_parsers),
    ("T1 rank -> hardware map", check_mapping),
    ("T2 stuck group localisation", check_stuck_group),
    ("T2 link implication + switch ports", check_implicate),
    ("T2 GPU health decisions", check_gpu_actions),
    ("T3 proven cause vs correlation", check_hypotheses),
    ("T4 checkpoint selection + RPO/RTO", check_checkpoint),
    ("T4 retry-loop policy", check_retry_policy),
    ("T4 restart plan + rank remap", check_restart_plan),
    ("T5 FMEA scorer", check_fmea),
    ("T6 tenant isolation checker", check_isolation),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--impl", choices=["starter", "solution"], default="starter")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    try:
        ctx = Ctx(load_impl(args.impl))
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL import/load: {exc!r}")
        return 1
    passed = 0
    for name, fn in CHECKS:
        try:
            ok, msg = fn(ctx)
            if ok is None:
                print(f"SKIP {name}: {msg}")
                passed += 1
                continue
            print(f"{'PASS' if ok else 'FAIL'} {name}: {msg}")
            passed += bool(ok)
        except NotImplementedError as exc:
            print(f"TODO {name}: implement {exc.args[0] if exc.args else 'function'}()")
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL {name}: {type(exc).__name__}: {exc}")
            if args.verbose:
                print(traceback.format_exc())
    print(f"\n{passed}/{len(CHECKS)} checks passed ({args.impl})")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
