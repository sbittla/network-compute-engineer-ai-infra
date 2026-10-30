#!/usr/bin/env python3
"""Print a Markdown acceptance / lifecycle / upgrade report from your implementation (lab Task 5).

    python report.py > acceptance_report.md            # uses starter/ (your code)
    python report.py --impl solution                   # instructor reference

Add your own analysis (root cause and remediation per node) below the generated tables.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
IMPLS = {"starter": HERE / "starter" / "fleet_lifecycle.py",
         "solution": HERE.parent / "solutions" / "lab" / "fleet_lifecycle.py"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--impl", choices=sorted(IMPLS), default="starter")
    ap.add_argument("--target", default="B-2026.10", help="upgrade target bundle id")
    args = ap.parse_args()
    spec = importlib.util.spec_from_file_location("fleet_lifecycle_report", IMPLS[args.impl])
    m = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(m)
    d = HERE / "data"
    policy, matrix = m.load_yaml(d / "acceptance_policy.yaml"), m.load_yaml(d / "compat_matrix.yaml")
    try:
        verdicts = m.evaluate_fleet(m.load_json(d / "acceptance_results.json"), policy, matrix)
        nodes, audit = m.replay(m.load_json(d / "inventory.json"), m.load_json(d / "lifecycle_events.json"), matrix)
        plan = m.plan_upgrade_waves(m.load_json(d / "inventory.json"), matrix, args.target)
    except NotImplementedError as e:
        print(f"Cannot build report yet: {e} is not implemented.", file=sys.stderr)
        return 1

    print(f"# ORION acceptance and lifecycle report (policy {policy['policy_version']})\n")
    counts = {k: sum(v["verdict"] == k for v in verdicts) for k in ("PASS", "WARN", "FAIL")}
    print(f"Verdicts: {counts}\n\n| Node | Verdict | Codes | Warnings | Details |\n|---|---|---|---|---|")
    for v in verdicts:
        if v["verdict"] != "PASS":
            print(f"| {v['node']} | {v['verdict']} | {', '.join(v['codes'])} | {', '.join(v['warnings'])} "
                  f"| {'; '.join(v['details'])} |")
    print("\n## Rejected lifecycle events\n\n| Seq | Node | Event | Actor | From | Reason |\n|---|---|---|---|---|---|")
    for a in audit:
        if a["result"] == "rejected":
            print(f"| {a['seq']} | {a['node']} | {a['event']} | {a['actor']} | {a['from_state']} | {a['reason_code']} |")
    print("\n## Final non-schedulable nodes\n")
    for n, rec in sorted(nodes.items()):
        if rec["state"] != "schedulable":
            print(f"- {n}: {rec['state']}")
    print(f"\n## Upgrade plan to {plan['target']}\n\n- Canary: {', '.join(plan['canary'])}")
    for i, w in enumerate(plan["waves"], 1):
        print(f"- Wave {i}: {', '.join(w)}")
    print("- Excluded: " + ", ".join(f"{k} ({v})" for k, v in plan["excluded"].items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
