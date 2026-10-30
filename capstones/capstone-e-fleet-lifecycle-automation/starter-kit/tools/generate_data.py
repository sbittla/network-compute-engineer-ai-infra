#!/usr/bin/env python3
"""Generate the Capstone E fleet dataset (ORION-256 plus an 8-node expansion).

Every output is deterministic: the same seed produces byte-identical files.

Outputs (written to --out, default ../data):
    inventory.csv           41 nodes: 32 ORION nodes, 8 expansion nodes, 1 retired lab node
    compat_matrix.csv       validated software/firmware bundles and their status
    acceptance_policy.yaml  thresholds for the node acceptance test
    acceptance_results.json acceptance-test evidence for nodes that were (re)imaged this week
    events.jsonl            lifecycle events to replay through the state machine (deliberately unsorted)
    rollout_constraints.yaml canary and wave constraints for the next bundle rollout
    canary_metrics.csv      soak metrics for four canary scenarios
    audit_log.jsonl         a hash-chained audit trail exported from the lifecycle controller

All version strings and measurements are [ILLUSTRATIVE] teaching values, not statements about any
vendor's real compatibility matrix.

Usage:
    python generate_data.py                 # writes ../data
    python generate_data.py --out /tmp/x    # writes elsewhere (determinism check)
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import yaml

SEED = 16
T0 = datetime(2026, 10, 19, 6, 0, tzinfo=timezone.utc)  # Monday of the bring-up week

BUNDLE_FIELDS = ["os_image", "kernel", "gpu_driver", "gpu_vbios", "nic_fw", "rdma_stack", "bios", "bmc_fw"]

BUNDLES = [
    {"bundle_id": "B-2026.04", "status": "deprecated", "os_image": "hx8-ubuntu22.04-2026.04",
     "kernel": "5.15.0-105-generic", "gpu_driver": "535.161.08", "cuda_max": "12.2",
     "gpu_vbios": "96.00.89.00.01", "nic_fw": "28.39.1002", "rdma_stack": "doca-host-2.5",
     "bios": "1.8.2", "bmc_fw": "2.14", "validated_on": "2026-04-02", "expires": "2026-12-31",
     "notes": "Previous golden. Allowed in service until expiry; no new admissions."},
    {"bundle_id": "B-2026.07", "status": "golden", "os_image": "hx8-ubuntu22.04-2026.07",
     "kernel": "5.15.0-117-generic", "gpu_driver": "550.90.07", "cuda_max": "12.4",
     "gpu_vbios": "96.00.99.00.01", "nic_fw": "28.41.1000", "rdma_stack": "doca-host-2.7",
     "bios": "1.9.0", "bmc_fw": "2.16", "validated_on": "2026-07-14", "expires": "2027-06-30",
     "notes": "Current golden bundle for training and inference partitions."},
    {"bundle_id": "B-2026.10", "status": "canary", "os_image": "hx8-ubuntu24.04-2026.10",
     "kernel": "6.8.0-45-generic", "gpu_driver": "570.86.15", "cuda_max": "12.8",
     "gpu_vbios": "96.00.99.00.01", "nic_fw": "28.43.1014", "rdma_stack": "doca-host-2.9",
     "bios": "1.9.0", "bmc_fw": "2.18", "validated_on": "2026-10-12", "expires": "2027-12-31",
     "notes": "Candidate bundle; canary only until the soak gate is met."},
    {"bundle_id": "BLK-0001", "status": "blocked", "os_image": "hx8-ubuntu22.04-2026.07",
     "kernel": "5.15.0-117-generic", "gpu_driver": "570.86.15", "cuda_max": "12.8",
     "gpu_vbios": "96.00.99.00.01", "nic_fw": "28.41.1000", "rdma_stack": "doca-host-2.7",
     "bios": "1.9.0", "bmc_fw": "2.16", "validated_on": "2026-10-05", "expires": "",
     "notes": "Driver upgraded in place without matching RDMA stack: GPUDirect RDMA peer-memory "
              "registration fails; NCCL falls back to host staging. Never admit."},
]


def ts(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def bundle(bid: str) -> dict:
    return next(b for b in BUNDLES if b["bundle_id"] == bid)


def node_names() -> list[tuple[str, int]]:
    out = []
    for rack in range(1, 11):
        for n in range(1, 5):
            out.append((f"orion-n{(rack - 1) * 4 + n:02d}", rack))
    return out


def build_inventory(rng: np.random.Generator) -> list[dict]:
    rows = []
    for name, rack in node_names():
        b = bundle("B-2026.07")
        state = "schedulable"
        role = "training"
        if rack >= 9:
            state, role = "discovered", "expansion"
        if rack in (7,):
            b = bundle("B-2026.04")
        row = {"node": name, "serial": f"HX8{rng.integers(10_000_000, 99_999_999)}", "rack": f"rack-{rack:02d}",
               "role": role, "state": state}
        for f in BUNDLE_FIELDS:
            row[f] = b[f]
        row["gpu_vbios"] = ";".join([b["gpu_vbios"]] * 8)
        row["last_transition_utc"] = ts(T0 - timedelta(days=int(rng.integers(5, 60))))
        rows.append(row)
    by = {r["node"]: r for r in rows}
    # Default ORION split (REFERENCE_CLUSTER.md): training n01-n24 (rack-01..06), inference n25-n32 (rack-07..08).
    for n in range(25, 33):
        by[f"orion-n{n:02d}"]["role"] = "inference"
    # Planted: GPU swapped from spares with old VBIOS; node is in repair, reimaged this week.
    by["orion-n10"]["state"] = "repair"
    v = [bundle("B-2026.07")["gpu_vbios"]] * 8
    v[5] = bundle("B-2026.04")["gpu_vbios"]
    by["orion-n10"]["gpu_vbios"] = ";".join(v)
    # Clean repair (DIMM replacement) returning this week.
    by["orion-n23"]["state"] = "repair"
    # Planted: hand-upgraded driver (blocked combination); one drained, one silently schedulable.
    for name, st in (("orion-n20", "drained"), ("orion-n30", "schedulable")):
        by[name]["gpu_driver"] = bundle("BLK-0001")["gpu_driver"]
        by[name]["state"] = st
    # Planted: vendor shipped an expansion node with a newer BIOS than any validated bundle.
    by["orion-n40"]["bios"] = "2.0.1"
    # Retired pre-production node.
    lab = {"node": "orion-lab-n01", "serial": "HX800000001", "rack": "lab", "role": "lab", "state": "retired"}
    old = bundle("B-2026.04")
    for f in BUNDLE_FIELDS:
        lab[f] = old[f]
    lab["gpu_vbios"] = ";".join([old["gpu_vbios"]] * 8)
    lab["last_transition_utc"] = ts(T0 - timedelta(days=90))
    rows.append(lab)
    return rows


POLICY = {
    "policy_version": "acceptance-2026.10",
    "evidence_label": "ILLUSTRATIVE thresholds for an H100-class HX8 node; calibrate on your own golden nodes",
    "expected_gpus": 8,
    "expected_nics": 8,
    "pcie_min_gen": 5,
    "pcie_min_width": 16,
    "nic_link_gbps": 400,
    "ecc_uncorrected_volatile_max": 0,
    "row_remap_pending_max": 0,
    "row_remap_failure_max": 0,
    "dcgm_diag_required": "pass",
    "nvlink_p2p_GBps_min": 340.0,
    "h2d_GBps_min": 45.0,
    "rdma_write_Gbps_min": 370.0,
    "storage_read_GBps_min": 10.0,
    "burn_in_hours_min": 12.0,
    "gpu_temp_max_c": 85.0,
    "xid_events_max": 0,
}


def healthy_result(rng: np.random.Generator, node: str, image_done: datetime) -> dict:
    start = image_done + timedelta(minutes=int(rng.integers(20, 90)))
    burn = 12.0 + float(rng.integers(0, 5))
    return {
        "node": node,
        "image_completed_utc": ts(image_done),
        "started_utc": ts(start),
        "completed_utc": ts(start + timedelta(hours=burn + 1.5)),
        "tests": {
            "gpu_count": 8,
            "gpu_pcie": [{"gpu": i, "gen": 5, "width": 16} for i in range(8)],
            "nic_pcie": [{"nic": i, "gen": 5, "width": 16} for i in range(8)],
            "nic_link_gbps": [400] * 8,
            "ecc_uncorrected_volatile": [0] * 8,
            "ecc_corrected_volatile": [int(x) for x in rng.integers(0, 3, 8)],
            "row_remap_pending": [0] * 8,
            "row_remap_failure": [0] * 8,
            "dcgm_diag_level3": "pass",
            "nvlink_p2p_GBps_min": round(float(rng.uniform(362, 378)), 1),
            "h2d_GBps_min": round(float(rng.uniform(49, 53)), 1),
            "rdma_write_Gbps_min": round(float(rng.uniform(378, 392)), 1),
            "storage_read_GBps": round(float(rng.uniform(13, 18)), 1),
            "burn_in_hours": burn,
            "gpu_temp_max_c": round(float(rng.uniform(70, 80)), 1),
            "xid_events": [],
        },
    }


def build_acceptance(rng: np.random.Generator) -> tuple[list[dict], dict[str, datetime]]:
    image_times: dict[str, datetime] = {}
    nodes = [f"orion-n{32 + n:02d}" for n in range(1, 5)] + [f"orion-n{36 + n:02d}" for n in range(1, 5)] + [
        "orion-n10", "orion-n23"]
    results = []
    for i, node in enumerate(nodes):
        image_done = T0 + timedelta(hours=2 + i, minutes=int(rng.integers(0, 50)))
        image_times[node] = image_done
        results.append(healthy_result(rng, node, image_done))
    r = {x["node"]: x for x in results}
    # Planted acceptance failures (documented in instructor/GRADING_GUIDE.md only).
    r["orion-n33"]["tests"]["gpu_count"] = 7
    r["orion-n33"]["tests"]["gpu_pcie"] = r["orion-n33"]["tests"]["gpu_pcie"][:7]
    r["orion-n33"]["tests"]["xid_events"] = [{"gpu": 6, "xid": 79, "utc": r["orion-n33"]["started_utc"]}]
    r["orion-n33"]["tests"]["dcgm_diag_level3"] = "fail"
    r["orion-n34"]["tests"]["nic_pcie"][3]["width"] = 8
    r["orion-n35"]["tests"]["nic_link_gbps"][5] = 200
    r["orion-n36"]["tests"]["gpu_temp_max_c"] = 89.0
    # Stale evidence: results belong to a factory run before this week's reimage.
    stale = r["orion-n37"]
    stale["started_utc"] = ts(image_times["orion-n37"] - timedelta(days=9))
    stale["completed_utc"] = ts(image_times["orion-n37"] - timedelta(days=8, hours=10))
    # Red herring: a burst of correctable ECC, zero uncorrectable, no pending remaps -> still passes.
    r["orion-n38"]["tests"]["ecc_corrected_volatile"][3] = 1423
    # Boundary: exactly the minimum burn-in duration passes.
    r["orion-n39"]["tests"]["burn_in_hours"] = 12.0
    return results, image_times


def build_events(image_times: dict[str, datetime]) -> list[dict]:
    ev: list[dict] = []

    def add(t: datetime, node: str, event: str, actor: str, ticket: str = "") -> None:
        ev.append({"event_id": f"ev-{len(ev) + 1:04d}", "utc": ts(t), "node": node, "event": event,
                   "actor": actor, "ticket": ticket})

    for node, t in image_times.items():
        add(t, node, "image_complete", "provisioner")
    day2 = T0 + timedelta(days=1, hours=8)
    for i, node in enumerate(image_times):
        add(day2 + timedelta(minutes=10 * i), node, "acceptance_complete", "acceptance-runner")
    day3 = T0 + timedelta(days=2, hours=9)
    for i, node in enumerate(["orion-n38", "orion-n39", "orion-n40", "orion-n10", "orion-n23"]):
        add(day3 + timedelta(minutes=5 * i), node, "admit", "fleet-bot", "CHG-4410")
    # Illegal: admit a node that failed acceptance (it is in repair).
    add(day3 + timedelta(minutes=40), "orion-n33", "admit", "jdoe", "CHG-4410")
    # Illegal: confirm a fault on a node still running jobs (must drain first), then the correct sequence.
    add(day3 + timedelta(hours=2), "orion-n07", "fault_confirmed", "sre-oncall", "INC-2291")
    add(day3 + timedelta(hours=2, minutes=3), "orion-n07", "drain", "sre-oncall", "INC-2291")
    add(day3 + timedelta(hours=3), "orion-n07", "fault_confirmed", "sre-oncall", "INC-2291")
    # Terminal state must stay terminal.
    add(day3 + timedelta(hours=4), "orion-lab-n01", "retire", "fleet-bot", "CHG-4398")
    # Idempotent re-request: drain a node that is already drained -> noop, not an error.
    add(day3 + timedelta(hours=5), "orion-n20", "drain", "fleet-bot", "CHG-4415")
    # Guarded: undrain a node on a blocked bundle -> rejected.
    add(day3 + timedelta(hours=5, minutes=30), "orion-n20", "undrain", "jdoe", "CHG-4415")
    # Maintenance on orion-n13: drain then undrain (written to the file out of order below).
    add(day3 + timedelta(hours=6), "orion-n13", "drain", "fleet-bot", "CHG-4420")
    add(day3 + timedelta(hours=9), "orion-n13", "undrain", "fleet-bot", "CHG-4420")
    # Retire the orion-n33 chassis after vendor declares it unrepairable.
    add(day3 + timedelta(days=1), "orion-n33", "retire", "fleet-bot", "RMA-0773")
    # Duplicate delivery of an earlier message (same event_id) from an at-least-once queue.
    dup = dict(next(e for e in ev if e["node"] == "orion-n07" and e["event"] == "drain"))
    ev.append(dup)
    # Out-of-order delivery: move the orion-n13 undrain ahead of its drain in the file.
    i_drain = next(i for i, e in enumerate(ev) if e["node"] == "orion-n13" and e["event"] == "drain")
    i_undrain = next(i for i, e in enumerate(ev) if e["node"] == "orion-n13" and e["event"] == "undrain")
    ev[i_drain], ev[i_undrain] = ev[i_undrain], ev[i_drain]
    return ev


CONSTRAINTS = {
    "target_bundle": "B-2026.10",
    "canary_size": 2,
    "canary_distinct_racks": True,
    "max_nodes_per_rack_per_wave": 1,
    "max_wave_fraction": 0.25,
    "partition_floors": {"training": 16, "inference": 6},
    "prefer_first": ["deprecated"],
    "eligible_states": ["schedulable"],
    "eligible_compat": ["golden", "deprecated"],
    "canary_thresholds": {
        "min_soak_hours": 24,
        "max_xid_events": 0,
        "dcgm_diag_required": "pass",
        "max_busbw_regression_pct": 5.0,
        "max_ib_bw_regression_pct": 3.0,
        "max_step_time_regression_pct": 2.0,
        "max_tpot_regression_pct": 5.0,
    },
}


def build_canary(rng: np.random.Generator) -> list[dict]:
    rows = []
    base = {"nccl_busbw_GBps": 455.0, "ib_write_Gbps": 386.0, "step_time_s": 17.4, "tpot_p95_ms": 23.0}
    # Baselines per partition: the training canary is compared with training nodes on the golden
    # bundle (step time); the inference canary with inference nodes (serving TPOT p95).
    for scen in ("S1", "S2", "S3", "S4"):
        for role, part, node in (("baseline", "training", "orion-n17"), ("baseline", "training", "orion-n21"),
                                 ("baseline", "inference", "orion-n29"), ("baseline", "inference", "orion-n31"),
                                 ("canary", "training", "orion-n01"), ("canary", "inference", "orion-n25")):
            row = {"scenario": scen, "node": node, "partition": part, "role": role, "soak_hours": 24.0,
                   "dcgm_diag": "pass", "xid_events": 0,
                   "nccl_busbw_GBps": round(base["nccl_busbw_GBps"] * (1 + float(rng.uniform(-0.006, 0.006))), 1),
                   "ib_write_Gbps": round(base["ib_write_Gbps"] * (1 + float(rng.uniform(-0.004, 0.004))), 1),
                   "step_time_s": "", "tpot_p95_ms": ""}
            if part == "training":
                row["step_time_s"] = round(base["step_time_s"] * (1 + float(rng.uniform(-0.004, 0.004))), 2)
            else:
                row["tpot_p95_ms"] = round(base["tpot_p95_ms"] * (1 + float(rng.uniform(-0.01, 0.01))), 2)
            if role == "canary" and scen == "S3":
                row["soak_hours"] = 10.0
            rows.append(row)
    # S2: one canary regresses ~8.8 % on intra-node busbw; the canary MEAN is below the 5 % threshold.
    s2 = [r for r in rows if r["scenario"] == "S2" and r["role"] == "canary"]
    s2[0]["nccl_busbw_GBps"] = 415.0
    s2[1]["nccl_busbw_GBps"] = 452.0
    # S4: a canary logs Xid 79 (GPU fell off the bus) during soak even though throughput looks fine.
    s4 = [r for r in rows if r["scenario"] == "S4" and r["role"] == "canary"]
    s4[1]["xid_events"] = 1
    for r in rows:
        if r["role"] == "baseline":
            r["soak_hours"] = ""
    return rows


def canon(d: dict) -> str:
    return json.dumps(d, sort_keys=True, separators=(",", ":"))


def build_audit(rng: np.random.Generator) -> list[dict]:
    chain: list[dict] = []
    prev = "0" * 64
    actions = [("image_complete", "discovered", "imaged"), ("acceptance_complete", "imaged", "validated"),
               ("admit", "validated", "schedulable"), ("drain", "schedulable", "drained"),
               ("undrain", "drained", "schedulable")]
    names = [n for n, _ in node_names()[:32]]
    t = T0 - timedelta(days=7)
    for seq in range(1, 41):
        a, f, to = actions[int(rng.integers(0, len(actions)))]
        t = t + timedelta(minutes=int(rng.integers(5, 240)))
        rec = {"seq": seq, "utc": ts(t), "actor": "fleet-bot", "node": names[int(rng.integers(0, 32))],
               "event": a, "from_state": f, "to_state": to, "ticket": f"CHG-{4300 + seq}",
               "prev_hash": prev}
        rec["hash"] = hashlib.sha256(canon(rec).encode()).hexdigest()
        prev = rec["hash"]
        chain.append(rec)
    # Planted tamper: someone edited the actor on record 23 after the fact, without re-hashing.
    chain[22]["actor"] = "jdoe"
    return chain


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def write_text(path: Path, text: str) -> None:
    with open(path, "w", newline="\n", encoding="utf-8") as fh:
        fh.write(text)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parent.parent / "data")
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args()
    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    inv = build_inventory(rng)
    write_csv(out / "inventory.csv", inv,
              ["node", "serial", "rack", "role", "state", *BUNDLE_FIELDS, "last_transition_utc"])
    write_csv(out / "compat_matrix.csv", BUNDLES,
              ["bundle_id", "status", "os_image", "kernel", "gpu_driver", "cuda_max", "gpu_vbios", "nic_fw",
               "rdma_stack", "bios", "bmc_fw", "validated_on", "expires", "notes"])
    write_text(out / "acceptance_policy.yaml", yaml.safe_dump(POLICY, sort_keys=False))
    results, image_times = build_acceptance(rng)
    write_text(out / "acceptance_results.json", json.dumps(results, indent=1) + "\n")
    events = build_events(image_times)
    write_text(out / "events.jsonl", "".join(json.dumps(e) + "\n" for e in events))
    write_text(out / "rollout_constraints.yaml", yaml.safe_dump(CONSTRAINTS, sort_keys=False))
    write_csv(out / "canary_metrics.csv", build_canary(rng),
              ["scenario", "node", "partition", "role", "soak_hours", "dcgm_diag", "xid_events",
               "nccl_busbw_GBps", "ib_write_Gbps", "step_time_s", "tpot_p95_ms"])
    write_text(out / "audit_log.jsonl", "".join(canon(r) + "\n" for r in build_audit(rng)))
    print(f"wrote dataset to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
