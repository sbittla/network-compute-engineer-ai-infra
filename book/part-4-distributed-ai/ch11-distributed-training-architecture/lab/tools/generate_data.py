#!/usr/bin/env python3
"""Generate the Chapter 11 lab inputs (deterministic).

Writes four files into ``lab/data/``:

* ``model_wtrain.yaml``      -- W-TRAIN model and batch definition (docs/REFERENCE_CLUSTER.md)
* ``cluster_orion.yaml``     -- ORION-256 hardware and *assumed* efficiency parameters
* ``candidates.csv``         -- candidate parallelism configurations to evaluate
* ``reliability_scenarios.csv`` -- inputs for the checkpoint-interval calculator

All efficiency values are [ILLUSTRATIVE] teaching assumptions, not measurements. The candidate list
is shuffled with a fixed seed so learners cannot rely on row order; regenerating produces
byte-identical files.

Usage:
    python tools/generate_data.py            # writes into ../data relative to this file
"""
from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path

import yaml

SEED = 11

MODEL = {
    "name": "W-TRAIN",
    "params": 70.0e9,            # parameters
    "layers": 80,
    "hidden": 8192,
    "query_heads": 64,
    "kv_heads": 8,              # grouped-query attention
    "head_dim": 128,
    "seq_len": 4096,            # tokens per sequence
    "global_batch_seqs": 1024,  # sequences per optimizer step
    "bytes_per_param_state": 16,  # 2 weights + 2 grads + 12 fp32 master/m/v (BF16 mixed precision, Adam)
    "act_bytes": 2,             # BF16 activations / communication payload
}

CLUSTER = {
    "name": "ORION-256",
    "gpus": 256,
    "gpus_per_node": 8,
    "hbm_gb": 80.0,                     # GB (1e9 B) per GPU, H100-SXM-class
    "hbm_headroom_fraction": 0.85,      # policy: plan to use at most 85 % of HBM
    "fixed_overhead_gb": 4.0,           # CUDA context, NCCL buffers, allocator fragmentation [ILLUSTRATIVE]
    "peak_bf16_tflops": 989.0,          # dense BF16 per GPU [VENDOR-SPEC class]
    "kernel_efficiency": 0.50,          # achieved fraction of peak in GEMM-dominated compute [ILLUSTRATIVE]
    "nvlink_busbw_gbs": 300.0,          # effective GB/s for TP collectives inside a node [ILLUSTRATIVE]
    "rail_busbw_gbs": 45.0,             # effective GB/s per GPU over its 400 Gb/s rail NIC [ILLUSTRATIVE]
    "nvlink_latency_us": 10.0,          # per-collective fixed cost inside a node [ILLUSTRATIVE]
    "internode_latency_us": 30.0,       # per-collective / per-message fixed cost across nodes [ILLUSTRATIVE]
    "overlap_tp": 0.25,                 # fraction of TP comm hidden behind compute [ILLUSTRATIVE]
    "backward_fraction": 0.667,         # share of a micro-batch's compute spent in backward (4 of 6 ND FLOP)
    "overlap_pp": 0.50,                 # fraction of PP send/recv hidden
    "full_recompute_factor": 1.333,     # extra forward pass: (6+2)/6 FLOP ratio
}

# name, tp, pp, dp, micro_batch, zero_stage, recompute
CANDIDATES = [
    ("A_baseline_tp8_pp4_dp8", 8, 4, 8, 1, 1, "selective"),
    ("B_tp8_pp2_dp16", 8, 2, 16, 1, 1, "selective"),
    ("C_tp8_pp8_dp4", 8, 8, 4, 1, 1, "selective"),
    ("D_tp4_pp8_dp8", 4, 8, 8, 1, 1, "selective"),
    ("E_tp16_pp2_dp8", 16, 2, 8, 1, 1, "selective"),
    ("F_fsdp_tp1_pp1_dp256", 1, 1, 256, 1, 3, "full"),
    ("G_tp1_pp4_dp64", 1, 4, 64, 1, 1, "selective"),
    ("H_tp8_pp1_dp32", 8, 1, 32, 1, 1, "selective"),
    ("I_tp8_pp4_dp8_mb4_zero0", 8, 4, 8, 4, 0, "selective"),
    ("J_tp2_pp8_dp16", 2, 8, 16, 1, 1, "selective"),
    ("K_tp8_pp4_dp8_fullrecomp", 8, 4, 8, 1, 1, "full"),
    ("L_tp8_pp4_dp8_mb2", 8, 4, 8, 2, 1, "selective"),
]

# name, gpus, job_mtbf_hours, checkpoint_blocking_s, restart_s
RELIABILITY = [
    ("orion256_sync_pfs", 256, 48.0, 45.0, 900.0),
    ("orion256_async_staged", 256, 48.0, 5.0, 900.0),
    ("orionxl4096_sync_pfs", 4096, 3.0, 45.0, 900.0),
    ("orionxl4096_async_staged", 4096, 3.0, 5.0, 900.0),
]


def write_all(out_dir: Path) -> None:
    """Write every dataset into ``out_dir`` (created if needed)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    with open(out_dir / "model_wtrain.yaml", "w", encoding="utf-8", newline="\n") as f:
        yaml.safe_dump(MODEL, f, sort_keys=False)
    with open(out_dir / "cluster_orion.yaml", "w", encoding="utf-8", newline="\n") as f:
        yaml.safe_dump(CLUSTER, f, sort_keys=False)
    rows = list(CANDIDATES)
    rng.shuffle(rows)
    with open(out_dir / "candidates.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["name", "tp", "pp", "dp", "micro_batch", "zero_stage", "recompute"])
        w.writerows(rows)
    with open(out_dir / "reliability_scenarios.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["name", "gpus", "job_mtbf_hours", "checkpoint_blocking_s", "restart_s"])
        w.writerows(RELIABILITY)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parents[1] / "data")
    args = parser.parse_args()
    write_all(args.out)
    print(f"wrote datasets to {args.out}")


if __name__ == "__main__":
    main()
