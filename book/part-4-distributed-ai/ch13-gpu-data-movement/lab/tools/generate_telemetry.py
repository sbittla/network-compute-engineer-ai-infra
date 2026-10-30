#!/usr/bin/env python3
"""Generate the Chapter 13 per-rank, per-step telemetry bundle (deterministic).

Job: a 64-rank (8 HX8 nodes x 8 GPUs) synchronous data-parallel training job on ORION, 60 steps.
Rank r runs on node r // 8 (hosts orion-n17 .. orion-n24) as local rank r % 8, which uses GPU (r % 8)
and NIC (r % 8) on rail (r % 8).

Per step and rank the bundle records (all [SIMULATED]):
  tokens             tokens processed by the rank this step
  dataloader_wait_ms time the training loop blocked waiting for the next batch
  compute_ms         forward + backward kernel time
  wait_ms            time inside the gradient all-reduce before the last rank arrived (sync skew)
  comm_ms            all-reduce duration after the last rank arrived (data movement)
  step_ms            wall-clock step time (identical for all ranks in a synchronous job)
  gpu_util_pct       nvidia-smi style utilization: % of time *any* kernel ran (NCCL kernels count)
  sm_active_pct      DCGM-profiling style SM activity: fraction of SM cycles busy
  sm_clock_mhz, gpu_temp_c, power_w, clocks_event_reason
  nic_tx_gbps, nic_rx_gbps   step-averaged NIC throughput (Gb/s)
  nic_retx           RDMA retransmission-type events this step (delta of NIC counters)

The planted causes are documented only in solutions/. Usage:
    python tools/generate_telemetry.py     # writes ../data/telemetry.csv and ../data/job_manifest.yaml
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

SEED = 13
RANKS, STEPS, GPN = 64, 60, 8
BASE_TOKENS = 16384
MS_PER_TOKEN = 0.0366          # compute ms per token at full clock [ILLUSTRATIVE]
MAX_CLOCK = 1980.0             # MHz, H100-SXM-class max boost [VENDOR-SPEC class]
BASE_COMM_MS = 120.0           # all-reduce data movement after the last arrival
OPT_MS = 25.0                  # optimizer step
GRAD_BYTES_SENT = 5.4e9        # bytes each rank's NIC sends per step


def generate() -> tuple[pd.DataFrame, dict]:
    rng = np.random.default_rng(SEED)
    ranks = np.arange(RANKS)
    rows = []
    for step in range(STEPS):
        tokens = np.round(BASE_TOKENS * rng.normal(1.0, 0.02, RANKS)).astype(int)
        tokens[12] = int(round(BASE_TOKENS * 1.30 * rng.normal(1.0, 0.02)))
        clock = np.clip(rng.normal(1974.0, 4.0, RANKS), 1950, MAX_CLOCK)
        temp = rng.normal(68.0, 2.0, RANKS)
        power = rng.normal(640.0, 15.0, RANKS)
        reason = np.array(["none"] * RANKS, dtype=object)
        temp[51] = rng.normal(84.0, 0.8)                          # hot but within limits
        if step >= 20:
            ramp = min(1.0, (step - 19) / 3.0)
            clock[37] = MAX_CLOCK - ramp * (MAX_CLOCK - rng.normal(1530.0, 15.0))
            temp[37] = 74.0 + ramp * (rng.normal(89.0, 0.6) - 74.0)
            power[37] = rng.normal(575.0, 10.0)
            reason[37] = "sw_thermal_slowdown"
        compute = MS_PER_TOKEN * tokens * (MAX_CLOCK / clock) ** 0.9 * rng.normal(1.0, 0.008, RANKS)
        dl = np.abs(rng.normal(2.0, 0.5, RANKS))
        arrive = dl + compute
        last = arrive.max()
        wait = last - arrive
        degraded = step >= 30
        comm_base = BASE_COMM_MS * (1.65 if degraded else 1.0) * rng.normal(1.0, 0.01)
        comm = comm_base * rng.normal(1.0, 0.004, RANKS)
        step_ms = last + comm_base + OPT_MS
        retx = rng.poisson(1.0, RANKS)
        extra = np.ones(RANKS)
        if degraded:
            rail2 = ranks % GPN == 2
            retx[rail2] = rng.poisson(3200.0, rail2.sum())
            extra[rail2] = 1.12
        tx = GRAD_BYTES_SENT * extra * 8 / (step_ms / 1e3) / 1e9 * rng.normal(1.0, 0.005, RANKS)
        rx = GRAD_BYTES_SENT * 8 / (step_ms / 1e3) / 1e9 * rng.normal(1.0, 0.005, RANKS)
        busy = compute + wait + comm                               # NCCL kernels spin while waiting
        gpu_util = np.minimum(100.0, 100.0 * (busy + OPT_MS) / step_ms * rng.normal(1.0, 0.003, RANKS))
        sm_active = 100.0 * (0.82 * compute + 0.10 * (wait + comm) + 0.6 * OPT_MS) / step_ms
        for r in ranks:
            rows.append({
                "step": step, "rank": int(r), "host": f"orion-n{17 + r // GPN:02d}", "local_rank": int(r % GPN),
                "tokens": int(tokens[r]), "dataloader_wait_ms": round(float(dl[r]), 2),
                "compute_ms": round(float(compute[r]), 2), "wait_ms": round(float(wait[r]), 2),
                "comm_ms": round(float(comm[r]), 2), "step_ms": round(float(step_ms), 2),
                "gpu_util_pct": round(float(gpu_util[r]), 1), "sm_active_pct": round(float(sm_active[r]), 1),
                "sm_clock_mhz": int(round(clock[r])), "gpu_temp_c": round(float(temp[r]), 1),
                "power_w": round(float(power[r]), 1), "clocks_event_reason": reason[r],
                "nic_tx_gbps": round(float(tx[r]), 2), "nic_rx_gbps": round(float(rx[r]), 2),
                "nic_retx": int(retx[r]),
            })
    manifest = {
        "job": "w-dp64-telemetry", "ranks": RANKS, "gpus_per_node": GPN, "steps": STEPS,
        "hosts": [f"orion-n{17 + n:02d}" for n in range(RANKS // GPN)],
        "rank_mapping": "rank r -> host index r // 8, local_rank = GPU index = NIC index = rail = r % 8",
        "collective": "gradient all-reduce once per step, after backward (no overlap in this job)",
        "evidence_class": "SIMULATED",
        "columns": {
            "step": "optimizer step index (0-59)",
            "rank": "global rank (0-63)",
            "host": "node hostname (orion-n17 .. orion-n24)",
            "local_rank": "GPU index = NIC index = rail (0-7)",
            "tokens": "tokens processed by this rank in this step",
            "dataloader_wait_ms": "ms the training loop blocked waiting for the next batch",
            "compute_ms": "ms of forward + backward kernels",
            "wait_ms": "ms inside the gradient all-reduce before the last rank arrived (synchronization skew)",
            "comm_ms": "ms of all-reduce data movement after the last rank arrived",
            "step_ms": "wall-clock step time, identical for all ranks; step_ms - (dataloader_wait_ms + compute_ms + wait_ms + comm_ms) is about 25 ms of optimizer step (plus noise)",
            "gpu_util_pct": "% of time any kernel ran (nvidia-smi utilization.gpu style; NCCL kernels count while spinning)",
            "sm_active_pct": "% of SM cycles active (DCGM profiling SM-active style)",
            "sm_clock_mhz": "SM clock, MHz",
            "gpu_temp_c": "GPU temperature, degrees C",
            "power_w": "GPU board power, W",
            "clocks_event_reason": "active clocks-event reason ('none' or e.g. 'sw_thermal_slowdown')",
            "nic_tx_gbps": "NIC transmit rate averaged over the step, Gb/s",
            "nic_rx_gbps": "NIC receive rate averaged over the step, Gb/s",
            "nic_retx": "per-step delta of packet_seq_err + local_ack_timeout_err (sender) + out_of_sequence (receiver) on this rank's NIC",
        },
    }
    return pd.DataFrame(rows), manifest


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parents[1] / "data")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    df, manifest = generate()
    df.to_csv(args.out / "telemetry.csv", index=False, lineterminator="\n")
    with open(args.out / "job_manifest.yaml", "w", encoding="utf-8", newline="\n") as fh:
        yaml.safe_dump(manifest, fh, sort_keys=False)
    print(f"wrote {len(df)} rows to {args.out / 'telemetry.csv'}")


if __name__ == "__main__":
    main()
