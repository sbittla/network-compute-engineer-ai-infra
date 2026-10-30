#!/usr/bin/env python3
"""Generate the Capstone G incident dataset (ORION-XL, 512 HX8 nodes, one 480-node training job).

Deterministic: the same seed produces byte-identical files. All identifiers, log formats and
values are [ILLUSTRATIVE] / [SIMULATED]; log lines imitate the *shape* of real kernel, DCGM, NIC,
switch and PyTorch messages but are not captured from real systems.

Outputs (--out, default ../data):
    inventory.csv          4,096 rows: node, gpu index, rank, GPU UUID/BDF, NUMA, HCA, rail, leaf, port (LLDP-observed)
    cabling_plan.csv       planned cable map from the DCIM database (node, hca -> leaf, port)
    clock_offsets.csv      chrony-reported offset per host (host clock minus true time, seconds)
    events.jsonl           kernel / DCGM / NIC / switch / job / scheduler events with HOST timestamps
    progress.csv           per-rank last completed step, last enqueued collective sequence, host timestamp
    step_times.csv         global step durations for the last 600 steps before the fault
    checkpoints.json       checkpoint catalogue (async, sharded; one shard per node)
    quarantine_db.csv      health database before the incident
    spares.csv             spare / maintenance pool state
    ops_log.jsonl          what the recovery automation did (controller UTC clock)
    loss_pre.csv           loss, grad norm and data-loader sample index before the fault
    resume_validated.csv   loss after the restart from the selected checkpoint
    resume_unvalidated.csv loss from an earlier drill that restored the newest-looking checkpoint
    resume_dataloader_not_restored.csv  a restore whose data-loader/RNG state was not restored
    config.yaml            job and target parameters
"""
from __future__ import annotations

import argparse
import csv
import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import yaml

SEED = 22
T0 = datetime(2026, 11, 12, 3, 14, 7, tzinfo=timezone.utc)  # true time of the GPU fault
N_NODES, JOB_NODES = 512, 480
GPU_BDF = ["0000:18:00.0", "0000:2a:00.0", "0000:3a:00.0", "0000:5d:00.0",
           "0000:9a:00.0", "0000:ab:00.0", "0000:ba:00.0", "0000:db:00.0"]
NIC_BDF = ["0000:19:00.0", "0000:2b:00.0", "0000:3b:00.0", "0000:5e:00.0",
           "0000:9b:00.0", "0000:ac:00.0", "0000:bb:00.0", "0000:dc:00.0"]
STEP_S = 4.35
LAST_STEP = 51797
CKPT_STEPS = [51474, 51612, 51750]
FAULT_NODE, FAULT_GPU = "orionxl-n377", 5
FLAKY_NODE, FLAKY_RAIL = "orionxl-n213", 3
SWAP_NODE = "orionxl-n214"
SKEW_NODE, SKEW_S = "orionxl-n042", -180.0
CONFIG = {
    "cluster": "ORION-XL (512 x HX8) - SIMULATED incident dataset",
    "job": {"name": "w-train-xl", "nodes": JOB_NODES, "gpus": JOB_NODES * 8, "tp": 8, "pp": 8, "dp": 60,
            "step_s": STEP_S, "ckpt_interval_steps": 138, "ckpt_GB": 980.0, "collective_timeout_s": 600},
    "targets": {"detect_s": 120, "isolate_s": 600, "rto_s": 1800, "rpo_steps": 276},
    "scoring": {"quarantine_at": 60, "watch_at": 10},
}


def name(i: int) -> str:
    return f"orionxl-n{i:03d}"


def ts(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def leaf_port(idx: int, rail: int) -> tuple[str, int]:
    return f"orionxl-be-leaf-p{idx // 32:02d}-r{rail}", idx % 32 + 1


def build_inventory(rng: np.random.Generator) -> tuple[list[dict], list[dict]]:
    inv, plan = [], []
    for idx in range(N_NODES):
        node = name(idx + 1)
        for g in range(8):
            leaf, port = leaf_port(idx, g)
            plan.append({"node": node, "hca": f"mlx5_{g}", "leaf": leaf, "port": port})
            # Actual wiring (observed by LLDP) differs from the plan for one pair on rail 3.
            if g == FLAKY_RAIL and node == FLAKY_NODE:
                port += 1
            elif g == FLAKY_RAIL and node == SWAP_NODE:
                port -= 1
            rank = idx * 8 + g if idx < JOB_NODES else ""
            u = uuid.UUID(bytes=rng.bytes(16), version=4)
            inv.append({"node": node, "gpu": g, "rank": rank,
                        "tp_rank": g if rank != "" else "", "pp_stage": idx % 8 if rank != "" else "",
                        "dp_rank": idx // 8 if rank != "" else "",
                        "gpu_uuid": f"GPU-{u}", "gpu_bdf": GPU_BDF[g], "numa": 0 if g < 4 else 1,
                        "hca": f"mlx5_{g}", "nic_bdf": NIC_BDF[g], "rail": g, "leaf": leaf, "leaf_port": port})
    return inv, plan


def build_events(rng: np.random.Generator, inv: list[dict], offsets: dict[str, float]) -> list[dict]:
    ev: list[dict] = []

    def add(true_t: datetime, host: str, source: str, **kw: object) -> None:
        ev.append({"host_ts": ts(true_t + timedelta(seconds=offsets.get(host, 0.0))), "host": host,
                   "source": source, **kw})

    uuid_of = {(r["node"], r["gpu"]): r["gpu_uuid"] for r in inv}
    day0 = T0 - timedelta(hours=24)
    # Background correctable ECC (red herring): many GPUs with small single-bit counts.
    picks = rng.choice(N_NODES * 8, size=150, replace=False)
    for p in sorted(int(x) for x in picks):
        node, g = name(p // 8 + 1), p % 8
        add(day0 + timedelta(seconds=int(rng.integers(0, 86000))), node, "dcgm", gpu_uuid=uuid_of[(node, g)],
            field="DCGM_FI_DEV_ECC_SBE_VOL_TOTAL", value=int(rng.integers(1, 41)))
    # Watch item: one GPU with a high correctable rate.
    add(T0 - timedelta(minutes=30), "orionxl-n101", "dcgm", gpu_uuid=uuid_of[("orionxl-n101", 2)],
        field="DCGM_FI_DEV_ECC_SBE_VOL_TOTAL", value=2400)
    # Watch item: corrected PCIe AER burst on orionxl-n099 GPU2.
    for k in range(30):
        add(day0 + timedelta(minutes=40 * k + int(rng.integers(0, 30))), "orionxl-n099", "kernel",
            msg=f"pcieport 0000:29:01.0: AER: Corrected error received: {GPU_BDF[2]}")
    # Flaky HCA: four short link flaps on orionxl-n213 mlx5_3 before the fault.
    nic = NIC_BDF[FLAKY_RAIL]
    cum_flaps, crc = 0, 0
    flap_times = [T0 - timedelta(minutes=m) for m in (40, 31, 22, 9)]
    for ft in flap_times:
        add(ft, FLAKY_NODE, "kernel", msg=f"mlx5_core {nic} ens{FLAKY_RAIL}np0: Link down")
        add(ft + timedelta(milliseconds=640), FLAKY_NODE, "kernel", msg=f"mlx5_core {nic} ens{FLAKY_RAIL}np0: Link up")
    actual_leaf, actual_port = next((r["leaf"], r["leaf_port"]) for r in inv
                                    if r["node"] == FLAKY_NODE and r["gpu"] == FLAKY_RAIL)
    for m in range(60, -10, -5):
        t = T0 - timedelta(minutes=m)
        cum_flaps = sum(1 for ft in flap_times if ft <= t)
        crc = int(cum_flaps * 1400 + rng.integers(0, 50)) if cum_flaps else int(rng.integers(0, 3))
        add(t, FLAKY_NODE, "nic", hca=f"mlx5_{FLAKY_RAIL}", counter="link_down_events_phy", value=cum_flaps)
        add(t, FLAKY_NODE, "nic", hca=f"mlx5_{FLAKY_RAIL}", counter="rx_crc_errors_phy", value=crc)
        add(t, actual_leaf, "switch", port=actual_port, counter="link_flaps", value=cum_flaps)
        add(t, actual_leaf, "switch", port=actual_port, counter="fec_uncorrectable_codewords",
            value=int(cum_flaps * 900 + rng.integers(0, 40)) if cum_flaps else 0)
    # The GPU fault: uncorrectable ECC, contained error, process killed, row remap pending.
    gbdf = GPU_BDF[FAULT_GPU]
    pci = gbdf[:-2]  # Xid lines print the BDF without the function
    add(T0, FAULT_NODE, "kernel", msg=f"NVRM: Xid (PCI:{pci}): 94, pid=48211, name=python, Contained ECC error")
    add(T0 + timedelta(milliseconds=400), FAULT_NODE, "job",
        msg=f"[rank {376 * 8 + FAULT_GPU}] RuntimeError: CUDA error: uncorrectable ECC error encountered")
    add(T0 + timedelta(seconds=5), FAULT_NODE, "dcgm", gpu_uuid=uuid_of[(FAULT_NODE, FAULT_GPU)],
        field="DCGM_FI_DEV_ECC_DBE_VOL_TOTAL", value=1)
    add(T0 + timedelta(seconds=5), FAULT_NODE, "dcgm", gpu_uuid=uuid_of[(FAULT_NODE, FAULT_GPU)],
        field="DCGM_FI_DEV_ROW_REMAP_PENDING", value=1)
    add(T0 + timedelta(seconds=6), FAULT_NODE, "kernel",
        msg=f"NVRM: Xid (PCI:{pci}): 63, pid=48211, name=python, Row Remapper: New row marked for remapping, reset gpu to activate.")
    # Collective watchdog timeouts on a sample of ranks (all orionxl-n042 ranks included; its clock is behind).
    timeout_ranks = sorted(set(int(x) for x in rng.choice(JOB_NODES * 8, size=392, replace=False))
                           | {41 * 8 + g for g in range(8)})
    timeout_ranks = [r for r in timeout_ranks if r // 8 != 376]
    for r in timeout_ranks:
        node = name(r // 8 + 1)
        add(T0 + timedelta(seconds=600 + float(rng.uniform(0.0, 4.0))), node, "job",
            msg=(f"[rank {r}] Watchdog caught collective operation timeout: WorkNCCL(SeqNum=1203456, "
                 f"OpType=ALLREDUCE, Timeout(ms)=600000) ran for {600000 + int(rng.integers(5, 4000))} "
                 f"milliseconds before timing out."))
    add(T0 + timedelta(seconds=97), "slurmctld", "scheduler", msg=f"update_node: node {FAULT_NODE} state set to DRAINED")
    add(T0 + timedelta(seconds=242), "slurmctld", "scheduler", msg=f"update_node: node {FLAKY_NODE} state set to DRAINED")
    ev.sort(key=lambda e: (e["host_ts"], e["host"], e["source"]))
    return ev


def build_progress(rng: np.random.Generator, offsets: dict[str, float]) -> list[dict]:
    rows = []
    for r in range(JOB_NODES * 8):
        node = name(r // 8 + 1)
        t = T0 - timedelta(seconds=float(rng.uniform(2.9, 3.6)))
        seq = 1203456
        if r == 376 * 8 + FAULT_GPU:
            seq = 1203455          # never enqueued the collective the others are waiting in
            t = T0 - timedelta(seconds=3.2)
        rows.append({"rank": r, "node": node, "last_completed_step": LAST_STEP, "last_collective_seq": seq,
                     "last_progress_host_ts": ts(t + timedelta(seconds=offsets[node]))})
    return rows


def loss_at(step: int) -> float:
    return 1.90 - 0.00005 * (step - 51000) + 0.01 * np.sin(step * 0.37) * np.cos(step * 0.011)


def gnorm_at(step: int) -> float:
    return 0.42 + 0.02 * np.sin(step * 0.13)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parent.parent / "data")
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args()
    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    def wcsv(fname: str, rows: list[dict]) -> None:
        with open(out / fname, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
            w.writeheader()
            w.writerows(rows)

    def wtext(fname: str, text: str) -> None:
        with open(out / fname, "w", newline="\n", encoding="utf-8") as fh:
            fh.write(text)

    inv, plan = build_inventory(rng)
    wcsv("inventory.csv", inv)
    wcsv("cabling_plan.csv", plan)
    offsets = {name(i + 1): round(float(rng.normal(0, 0.02)), 3) for i in range(N_NODES)}
    offsets[SKEW_NODE] = SKEW_S
    for i in range(16):
        for rail in range(8):
            offsets[f"orionxl-be-leaf-p{i:02d}-r{rail}"] = 0.0
    offsets["slurmctld"] = 0.0
    wcsv("clock_offsets.csv", [{"host": h, "offset_s": o} for h, o in offsets.items()])
    events = build_events(rng, inv, offsets)
    wtext("events.jsonl", "".join(json.dumps(e) + "\n" for e in events))
    wcsv("progress.csv", build_progress(rng, offsets))

    flaps = [T0 - timedelta(minutes=m) for m in (40, 31, 22, 9)]
    steps, t = [], T0 - timedelta(seconds=3.2)
    rows = []
    for s in range(LAST_STEP, LAST_STEP - 600, -1):
        d = STEP_S * (1 + float(rng.normal(0, 0.004)))
        if any(abs((t - f).total_seconds()) < STEP_S for f in flaps):
            d += float(rng.uniform(5.0, 8.0))   # transport retries during the flap
        rows.append({"step": s, "end_utc": ts(t), "duration_s": round(d, 3)})
        t -= timedelta(seconds=d)
    wcsv("step_times.csv", sorted(rows, key=lambda r: r["step"]))

    ckpts = []
    for s in CKPT_STEPS:
        start = T0 - timedelta(seconds=(LAST_STEP - s) * STEP_S + 3.2)
        shards = [{"shard": i, "node": name(i + 1), "present": True, "checksum_ok": True} for i in range(JOB_NODES)]
        committed = True
        if s == 51612:
            shards[232]["checksum_ok"] = False        # silent corruption on one shard
        if s == 51750:
            for i in range(JOB_NODES):
                shards[i]["present"] = i < 446         # rate-limited upload still in flight at the fault
            committed = False
        ckpts.append({"step": s, "started_utc": ts(start), "kind": "async-sharded", "expected_shards": JOB_NODES,
                      "metadata_committed": committed,
                      "missing_shards": [x["shard"] for x in shards if not x["present"]],
                      "checksum_failures": [x["shard"] for x in shards if x["present"] and not x["checksum_ok"]]})
    wtext("checkpoints.json", json.dumps(ckpts, indent=1) + "\n")

    wcsv("quarantine_db.csv", [
        {"component": "gpu:orionxl-n300:1", "state": "closed", "since_utc": "2026-10-28T11:02:00Z", "reason": "Xid 79; reseated, re-accepted"},
        {"component": "gpu:orionxl-n482:1", "state": "open", "since_utc": "2026-11-06T19:40:00Z", "reason": "row remap failure; RMA pending"},
        {"component": "hca:orionxl-n157:mlx5_6", "state": "closed", "since_utc": "2026-11-01T08:15:00Z", "reason": "optic replaced"},
    ])
    spares = []
    for i in range(JOB_NODES + 1, N_NODES + 1):
        n = name(i)
        st, acc = "idle", "passed"
        if n == "orionxl-n481":
            acc = "pending"
        if n == "orionxl-n497":
            st = "maint"
        spares.append({"node": n, "sched_state": st, "acceptance": acc})
    wcsv("spares.csv", spares)

    ops = [(38, "alert", "GpuUncorrectableEcc orionxl-n377 gpu5 (Xid 94)"),
           (95, "quarantine", "gpu:orionxl-n377:5"), (97, "drain", "orionxl-n377"),
           (110, "job_cancel", "fast-fail after confirmed GPU fault"),
           (240, "quarantine", "hca:orionxl-n213:mlx5_3"), (242, "drain", "orionxl-n213"),
           (300, "restart_submitted", "replacements orionxl-n377->orionxl-n483, orionxl-n213->orionxl-n484"),
           (655, "job_running", "3,840 ranks initialised"),
           (868, "checkpoint_loaded", "step 51474"), (912, "first_step", "step 51475 completed")]
    wtext("ops_log.jsonl", "".join(json.dumps({"utc": ts(T0 + timedelta(seconds=s)), "action": a, "detail": d}) + "\n"
                                    for s, a, d in ops))
    gbs = JOB_NODES * 8  # sequences per global batch (one per data-parallel rank slot)
    wcsv("loss_pre.csv", [{"step": s, "loss": round(float(loss_at(s)), 6), "grad_norm": round(float(gnorm_at(s)), 6),
                           "sample_idx": s * gbs} for s in range(51000, LAST_STEP + 1)])
    # Correct restore: same samples, same order; only non-deterministic-reduction noise (~2e-4 relative).
    wcsv("resume_validated.csv", [{"step": s, "loss": round(float(loss_at(s) * (1 + rng.normal(0, 0.0002))), 6),
                                   "grad_norm": round(float(gnorm_at(s) * (1 + rng.normal(0, 0.0002))), 6),
                                   "sample_idx": s * gbs} for s in range(51475, 52001)])
    # Subtle bug: weights restored correctly but the data-loader / RNG state was not, so the job
    # re-reads the dataset from its start. Loss differs by only ~0.1-0.3 %.
    wcsv("resume_dataloader_not_restored.csv",
         [{"step": s, "loss": round(float(loss_at(s) * (1 + 0.002 * np.sin(s * 0.7) + rng.normal(0, 0.0002))), 6),
           "grad_norm": round(float(gnorm_at(s) * (1 + 0.006 * np.cos(s * 0.5))), 6),
           "sample_idx": (s - 51474) * gbs} for s in range(51475, 52001)])
    bad = []
    for s in range(51613, 52001):
        v = loss_at(s) + 1.1 * np.exp(-(s - 51613) / 400.0)
        bad.append({"step": s, "loss": "nan" if s >= 51950 else round(float(v), 6),
                    "grad_norm": "nan" if s >= 51950 else round(float(gnorm_at(s) * 3.0), 6), "sample_idx": s * gbs})
    wcsv("resume_unvalidated.csv", bad)
    wtext("config.yaml", yaml.safe_dump(CONFIG, sort_keys=False))
    print(f"wrote dataset to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
