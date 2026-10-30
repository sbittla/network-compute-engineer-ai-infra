#!/usr/bin/env python3
"""Generate the Capstone F dataset: default alert rules, game-day constraints, the recorded first
game day (run with the *default* rules), and reliability backlog candidates.

Deterministic: the simulator is seeded, so regeneration is byte-identical.

Usage:
    python generate_data.py                 # writes ../data
    python generate_data.py --out /tmp/x    # writes elsewhere (determinism check)
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import yaml

KIT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KIT))
from sim import cluster_sim  # noqa: E402

DEFAULT_RULES = [
    {"name": "NodeDown", "metric": "sim_node_up", "op": "==", "threshold": 0, "for_s": 60,
     "severity": "critical", "detects": ["node_loss"]},
    {"name": "JobStalled", "metric": "sim_job_progress_age_seconds", "op": ">", "threshold": 30, "for_s": 0,
     "severity": "critical", "detects": ["link_down", "node_loss"]},
    {"name": "NicLinkDown", "metric": "sim_nic_link_up", "op": "==", "threshold": 0, "for_s": 300,
     "severity": "warning", "detects": ["link_down"]},
    {"name": "CheckpointStale", "metric": "sim_checkpoint_age_seconds", "op": ">", "threshold": 7200,
     "for_s": 300, "severity": "warning", "detects": ["storage_slow"]},
]

CONSTRAINTS = {
    "environment": "SIMULATED ORION-256 (starter-kit/sim/cluster_sim.py) - never a shared or production cluster",
    "horizon_s": 21600,
    "warmup_s": 1900,
    "max_concurrent_faults": 2,
    "protected_nodes": [f"orion-n{28 + n:02d}" for n in range(1, 5)],
    "protected_reason": "rack-08 serves the W-INFER customer-facing inference partition; out of scope for this game day",
    "detection_targets_s": {"node_loss": 120, "link_down": 120, "scheduler_outage": 120, "storage_slow": 300},
    "max_false_alerts_per_6h": 0,
    "game_day_t0_utc": "2026-11-05T14:00:00Z",
}

GAMEDAY1_PLAN = {
    "name": "ORION game day 1 (run with the default alert rules)",
    "t0_utc": "2026-11-05T14:00:00Z",
    "faults": [
        {"id": "F1", "kind": "link_down", "target": "orion-n07", "rail": 4, "start_s": 2700, "duration_s": 900},
        {"id": "F2", "kind": "storage_slow", "factor": 0.02, "start_s": 10200, "duration_s": 3600},
        {"id": "F3", "kind": "node_loss", "target": "orion-n18", "start_s": 11000},
        {"id": "F4", "kind": "scheduler_outage", "start_s": 16200, "duration_s": 1200},
        {"id": "F5", "kind": "link_down", "target": "orion-n13", "rail": 0, "start_s": 16500, "duration_s": 600},
    ],
}

BACKLOG = [
    {"id": "RB-01", "title": "Alert on scheduler heartbeat absence", "annual_events": 4, "gpu_h_per_event": 150,
     "expected_reduction": 0.5, "effort_weeks": 0.2, "safety_critical": "true"},
    {"id": "RB-02", "title": "Automated return-to-service for nodes whose fault cleared (re-accept, then undrain)",
     "annual_events": 50, "gpu_h_per_event": 120, "expected_reduction": 0.6, "effort_weeks": 3.0,
     "safety_critical": "false"},
    {"id": "RB-03", "title": "Fast-fail jobs on health-controller detection instead of waiting for the collective timeout",
     "annual_events": 137, "gpu_h_per_event": 28.8, "expected_reduction": 1.0, "effort_weeks": 2.0,
     "safety_critical": "false"},
    {"id": "RB-04", "title": "Checkpoint-staleness alert at 2x interval plus storage write-throughput alert",
     "annual_events": 6, "gpu_h_per_event": 300, "expected_reduction": 0.5, "effort_weeks": 0.2,
     "safety_critical": "false"},
    {"id": "RB-05", "title": "Grow spare pool from 2 to 4 nodes", "annual_events": 10, "gpu_h_per_event": 1500,
     "expected_reduction": 0.8, "effort_weeks": 1.0, "safety_critical": "false"},
    {"id": "RB-06", "title": "De-flap JobStalled (threshold above checkpoint stall, add for-duration)",
     "annual_events": 2000, "gpu_h_per_event": 0.0, "expected_reduction": 1.0, "effort_weeks": 0.1,
     "safety_critical": "false"},
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=KIT / "data")
    args = ap.parse_args()
    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)

    def dump(name: str, obj: object) -> None:
        with open(out / name, "w", newline="\n", encoding="utf-8") as fh:
            fh.write(yaml.safe_dump(obj, sort_keys=False))

    dump("default_alert_rules.yaml", DEFAULT_RULES)
    dump("gameday_constraints.yaml", CONSTRAINTS)
    dump("gameday1_plan.yaml", GAMEDAY1_PLAN)
    res = cluster_sim.run(GAMEDAY1_PLAN["faults"], DEFAULT_RULES, {"horizon_s": CONSTRAINTS["horizon_s"]})
    cluster_sim.save_result(res, out, "gameday1")
    with open(out / "backlog_candidates.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(BACKLOG[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(BACKLOG)
    print(f"wrote dataset to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
