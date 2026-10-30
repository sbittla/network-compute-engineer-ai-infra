#!/usr/bin/env python3
"""Generate the Chapter 20 lab datasets (deterministic, seeded).

Outputs (all in ../data/):
  desired_state.json     Desired RoCE/MTU/QoS configuration for ORION nodes and rail leaves
  actual_state.json      Simulated "observed" state of the ORION fleet (with drift)
  rollout.json           Per-wave canary rollout evidence (baseline + post-change samples)
  abort_conditions.json  Pre-declared abort conditions for the rollout controller
  unsafe_change_plan.md  A change plan to review (Part 3)
  gap_catalog.json       Catalogue of change-plan gap categories (with fix keywords)
  review_rubric.json     Hashed expected gap IDs and pass thresholds used by check.py

Regenerating must produce byte-identical files:
    python tools/generate_data.py && git diff --exit-code data/

All values are [ILLUSTRATIVE] and modeled on ORION-256 (docs/REFERENCE_CLUSTER.md).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path

SEED = 20
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

NODES = [f"orion-n{i:02d}" for i in range(1, 33)]
LEAVES = [f"orion-be-leaf-r{r}" for r in range(8)]


def rack_of(node: str) -> int:
    """Rack number 1..8 (4 nodes per rack: n01-n04 in rack-01, ...)."""
    return (int(node.split("n")[-1]) - 1) // 4 + 1


# ----------------------------------------------------------------------------- Part 1
NODE_DEFAULT = {
    "host_mtu": 9000,
    "rdma_path_mtu": 4096,
    "trust_mode": "dscp",
    "roce_dscp": 26,
    "roce_priority": 3,
    "pfc_priorities": [3],
    "ecn_enabled": True,
    "cnp_dscp": 48,
    "nic_firmware": "28.42.1000",
}
LEAF_DEFAULT = {
    "port_mtu": 9216,
    "pfc_priorities": [3],
    "ecn_queues": [3],
    "dscp_to_tc": {"26": 3, "48": 6},
    "strict_priority_tc": [6],
}


def desired_state() -> dict:
    return {
        "change_id": "CHG-2026-1103-RDMA-MTU",
        "description": "Raise RDMA path MTU 1024 -> 4096 on ORION backend NICs; enforce RoCE QoS baseline.",
        "policy": {
            "approved_nic_firmware": ["28.42.1000", "28.43.1014"],
            "allowed_rdma_path_mtu": [256, 512, 1024, 2048, 4096],
            "roce_header_budget_bytes": 64,
            "l2_overhead_bytes": 22,
        },
        "defaults": {"node": NODE_DEFAULT, "leaf": LEAF_DEFAULT},
        "targets": {"node": NODES, "leaf": LEAVES},
        "overrides": {
            "orion-n10": {"host_mtu": 9216},
            "orion-n22": {"nic_firmware": "28.44.0500"},
            "orion-n25": {"ecn_enabled": "yes"},
            "orion-be-leaf-r5": {"pfc_priorities": [4]},
        },
    }


def actual_state() -> dict:
    state: dict[str, dict | None] = {}
    for n in NODES:
        cfg = json.loads(json.dumps(NODE_DEFAULT))
        cfg["rdma_path_mtu"] = 4096 if rack_of(n) <= 2 else 1024  # racks 1-2 already migrated
        state[n] = cfg
    state["orion-n06"]["host_mtu"] = 1500          # drift: NIC reverted after reimage
    state["orion-n06"]["rdma_path_mtu"] = 1024     # consequence: largest IB MTU under a 1500-byte netdev MTU
    state["orion-n13"]["pfc_priorities"] = []      # drift: PFC config lost
    state["orion-n18"] = None                      # unreachable (BMC/agent timeout)
    for leaf in LEAVES:
        state[leaf] = json.loads(json.dumps(LEAF_DEFAULT))
    state["orion-be-leaf-r2"]["dscp_to_tc"] = {"26": 3}     # drift: CNP mapping missing
    return {"collected_at": "2026-11-03T09:00:00Z", "state": state}


# ----------------------------------------------------------------------------- Part 2
WAVE_SIZES = [2, 3, 4, 8, 8, 7]
BASE_SAMPLES = 6
POST_SAMPLES = 12


def wave_order() -> list[str]:
    """Slot-major order so every wave has at most one node per rack."""
    order = []
    for slot in range(4):
        for rack in range(1, 9):
            order.append(f"orion-n{(rack - 1) * 4 + slot + 1:02d}")
    return order


def samples(rng: random.Random, mean: float, sd: float, k: int, lo: float = 0.0) -> list[float]:
    return [round(max(lo, rng.gauss(mean, sd)), 2) for _ in range(k)]


def rollout(rng: random.Random) -> dict:
    order = wave_order()
    waves = []
    idx = 0
    for w, size in enumerate(WAVE_SIZES):
        nodes = []
        for node in order[idx: idx + size]:
            busbw_base = 44.0 + rng.uniform(-0.6, 0.6)
            cnp_base = 220.0 + rng.uniform(-30, 30)
            pfc_base = 40.0 + rng.uniform(-8, 8)
            entry = {
                "node": node,
                "rack": f"rack-{rack_of(node):02d}",
                "precheck": {"drained": True, "health": "ok", "fw_before": "28.42.1000"},
                "baseline": {
                    "busbw_GBps": samples(rng, busbw_base, 0.25, BASE_SAMPLES),
                    "cnp_rx_per_s": samples(rng, cnp_base, 20, BASE_SAMPLES),
                    "pfc_pause_rx_per_s": samples(rng, pfc_base, 6, BASE_SAMPLES),
                    "xid_events": [0] * BASE_SAMPLES,
                    "link_flaps": [0] * BASE_SAMPLES,
                },
                "post": {
                    "busbw_GBps": samples(rng, busbw_base, 0.25, POST_SAMPLES),
                    "cnp_rx_per_s": samples(rng, cnp_base, 20, POST_SAMPLES),
                    "pfc_pause_rx_per_s": samples(rng, pfc_base, 6, POST_SAMPLES),
                    "xid_events": [0] * POST_SAMPLES,
                    "link_flaps": [0] * POST_SAMPLES,
                },
            }
            # Plant A: pre-existing degraded node (failing precheck, flapping before and after).
            if node == "orion-n13":
                entry["precheck"]["health"] = "degraded"
                entry["precheck"]["note"] = "orion-be-leaf-r3 port flapping since 2026-11-01 (ticket FAB-4471)"
                entry["baseline"]["link_flaps"] = [0, 1, 0, 0, 1, 0]
                entry["post"]["link_flaps"] = [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1]
            # Plant B: single-sample transient dip (median-robust; must NOT abort).
            if node == "orion-n09":
                entry["post"]["busbw_GBps"][4] = round(busbw_base * 0.93, 2)
            # Plant C: wave-2 regression on two nodes.
            if node in ("orion-n25", "orion-n29"):
                entry["post"]["busbw_GBps"] = samples(rng, busbw_base * 0.90, 0.3, POST_SAMPLES)
                entry["post"]["cnp_rx_per_s"] = samples(rng, cnp_base * 5.0, 60, POST_SAMPLES)
                entry["post"]["pfc_pause_rx_per_s"] = samples(rng, pfc_base * 1.6, 8, POST_SAMPLES)
            nodes.append(entry)
        waves.append({"wave": w, "nodes": nodes})
        idx += size
    return {
        "change_id": "CHG-2026-1110-NICFW",
        "description": "NIC firmware 28.42.1000 -> 28.43.1014 on ORION backend NICs (validated bundle B-2026.10).",
        "bake_samples_required": POST_SAMPLES,
        "sample_interval_minutes": 5,
        "rollback_scope": "all_changed",
        "metric_definitions": {
            "busbw_GBps": "per-rail bus bandwidth, GB/s: 2-node (16-GPU, all 8 rails) all_reduce_perf busbw at 8 GiB divided by 8, compared with the 50 GB/s per-rail line rate; pair test with a fixed reference node",
            "cnp_rx_per_s": "RoCE congestion notification packets received per second, summed over 8 backend NICs",
            "pfc_pause_rx_per_s": "PFC pause frames received on priority 3 per second, summed over 8 backend NICs",
            "xid_events": "GPU Xid events in the sample interval",
            "link_flaps": "backend link down/up transitions in the sample interval",
        },
        "waves": waves,
    }


ABORT_CONDITIONS = {
    "conditions": [
        {"id": "AC1", "metric": "busbw_GBps", "type": "relative_drop", "aggregation": "median",
         "threshold": 0.05, "action": "abort",
         "rationale": "Median post-change busbw more than 5% below the node's own baseline median."},
        {"id": "AC2", "metric": "cnp_rx_per_s", "type": "relative_rise", "aggregation": "median",
         "threshold": 3.0, "floor": 500.0, "action": "abort",
         "rationale": "Median CNP rate above 3x baseline median AND above an absolute floor of 500/s."},
        {"id": "AC3", "metric": "pfc_pause_rx_per_s", "type": "relative_rise", "aggregation": "median",
         "threshold": 3.0, "floor": 150.0, "action": "abort",
         "rationale": "Median PFC pause rate above 3x baseline median AND above 150/s."},
        {"id": "AC4", "metric": "xid_events", "type": "sum_gt", "aggregation": "sum",
         "threshold": 0, "action": "abort", "rationale": "Any GPU Xid during bake."},
        {"id": "AC5", "metric": "link_flaps", "type": "sum_gt", "aggregation": "sum",
         "threshold": 0, "action": "abort", "rationale": "Any backend link flap during bake."},
    ],
    "precheck": {"require_drained": True, "require_health": "ok"},
    "bake": {"min_post_samples": POST_SAMPLES},
}


# ----------------------------------------------------------------------------- Part 3
UNSAFE_PLAN = """# CHG-2026-1107 - Enable 4096 RDMA MTU, new RoCE QoS profile, and NIC firmware on ORION

Owner: J. Rivera (Fabric team)
Ticket: CHG-2026-1107, approved by the Change Advisory Board on 2026-11-03
Window: Friday 2026-11-06, 16:30-17:00 local time
Communication: Training Infra, Platform, and SRE on-call notified 48 h ahead in #orion-ops; status-page notice posted

## Summary

Raise the RDMA path MTU from 1024 to 4096 on all 32 HX8 nodes and push the new RoCE QoS profile
(DSCP 26 -> TC 3 lossless with PFC, CNP DSCP 48 -> TC 6 strict priority) to all 8 rail leaves.
Also upgrade NIC firmware to 28.43.1014 at the same time, since the nodes are being touched anyway.

## Procedure

1. SSH to each rail leaf and paste the new QoS profile from the wiki page (it takes effect immediately).
2. From the jump host, run:
   for n in $(cat all_nodes.txt); do ssh $n 'sudo ./set_mtu.sh 4096 && sudo ./fw_update.sh 28.43.1014 && sudo reboot' & done
3. Wait for the nodes to come back.
4. Start a training job and check that the dashboards look good.

## Rollback

If something goes wrong, revert the switch config by hand and re-image the affected nodes.

## Risk

Low. The same change was tried on a lab node last month.
"""

GAP_CATALOG = [
    ("G-DRYRUN", "No dry-run or diff preview of the exact changes before they are applied.",
     ["dry-run", "dry run", "diff", "preview", "plan output"]),
    ("G-CANARY", "No canary: the change is applied to the whole population at once.",
     ["canary", "wave", "first node", "two nodes", "small subset"]),
    ("G-BLAST-RADIUS", "No blast-radius cap: too many failure domains (racks, rails, leaves) changed at once.",
     ["blast radius", "blast-radius", "per rack", "one rail", "failure domain", "cap"]),
    ("G-RATE-LIMIT", "Unbounded parallelism: no concurrency or rate limit on the automation.",
     ["rate limit", "rate-limit", "concurrency", "parallelism", "batch size", "serial"]),
    ("G-BUNDLED", "Unrelated changes bundled together, so a regression cannot be attributed.",
     ["separate", "unbundle", "one change", "split", "independent change"]),
    ("G-ORDERING", "Unsafe ordering / inconsistent intermediate state between dependent components.",
     ["order", "sequence", "consistent", "intermediate state", "host before", "switch before"]),
    ("G-DRAIN", "Running workloads are not drained or coordinated before disruptive steps.",
     ["drain", "cordon", "maintenance reservation", "no running jobs", "reservation"]),
    ("G-PRECHECK", "No prechecks of current health, baseline, or compatibility before changing.",
     ["precheck", "pre-check", "baseline", "health check", "compatibility matrix", "validated bundle"]),
    ("G-SUCCESS-CRITERIA", "Success criteria are vague or not measurable.",
     ["success criteria", "measurable", "threshold", "busbw", "all_reduce_perf", "acceptance"]),
    ("G-ABORT", "No pre-declared abort conditions.",
     ["abort", "stop condition", "halt", "abort condition"]),
    ("G-BAKE", "No bake time between stages to observe the change under load.",
     ["bake", "soak", "observation period", "wait period"]),
    ("G-ROLLBACK", "Rollback is undefined, untested, or not actually a rollback.",
     ["rollback", "roll back", "downgrade", "revert tested", "backout"]),
    ("G-AUDIT", "No capture of before-state or audit evidence.",
     ["audit", "before-state", "before state", "snapshot", "evidence", "record"]),
    ("G-REVIEW-VCS", "Configuration is applied by hand from an unreviewed, unversioned source.",
     ["version control", "git", "pull request", "peer review", "gitops", "schema", "validated config"]),
    ("G-WINDOW", "Change window is inappropriate or too short for the work.",
     ["window", "friday", "weekday", "staffed", "duration"]),
    ("G-KILL-SWITCH", "No way to stop the automation once it has started.",
     ["kill switch", "kill-switch", "stop", "pause", "circuit breaker"]),
    ("G-OOB-ACCESS", "No verification of out-of-band/console access before a change that can cut in-band access.",
     ["out-of-band", "oob", "console", "bmc", "serial"]),
    ("G-OWNER", "No named owner for the change.", ["owner", "accountable"]),
    ("G-APPROVAL", "No change ticket or approval.", ["ticket", "approval", "cab"]),
    ("G-COMMS", "Affected teams are not notified.", ["notify", "communication", "status page"]),
]
EXPECTED_GAPS = [g[0] for g in GAP_CATALOG[:17]]
SALT = "ch20-review:"


def gap_catalog() -> dict:
    return {"gaps": [{"id": i, "description": d, "fix_keywords": k} for i, d, k in sorted(GAP_CATALOG)]}


def review_rubric() -> dict:
    return {
        "hash_scheme": "sha256(salt + gap_id)",
        "salt": SALT,
        "expected_sha256": sorted(hashlib.sha256((SALT + g).encode()).hexdigest() for g in EXPECTED_GAPS),
        "min_expected_found": 13,
        "max_false_positives": 1,
    }


# ----------------------------------------------------------------------------- main
def write_json(path: Path, obj: object) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, indent=1, sort_keys=True)
        fh.write("\n")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=DATA_DIR)
    args = ap.parse_args()
    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    write_json(out / "desired_state.json", desired_state())
    write_json(out / "actual_state.json", actual_state())
    write_json(out / "rollout.json", rollout(rng))
    write_json(out / "abort_conditions.json", ABORT_CONDITIONS)
    write_json(out / "gap_catalog.json", gap_catalog())
    write_json(out / "review_rubric.json", review_rubric())
    with open(out / "unsafe_change_plan.md", "w", encoding="utf-8", newline="\n") as fh:
        fh.write(UNSAFE_PLAN)
    print(f"wrote 7 files to {out}")


if __name__ == "__main__":
    main()
