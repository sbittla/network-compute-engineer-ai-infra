#!/usr/bin/env python3
"""Generate the Chapter 1 workload-profile dataset (deterministic, seeded).

Writes two files into ``lab/data/``:

* ``platform_orion.yaml``   -- ORION-256 / HX8 resource ceilings (ILLUSTRATIVE, H100-class).
* ``workload_profiles.csv`` -- per-GPU, per-step work profiles for example AI workloads.

Units (per row, per GPU, per step unless the column name says otherwise):

* ``tflop_per_gpu``          -- tera floating-point operations (10^12 FLOP)
* ``hbm_gb_per_gpu``         -- GB (10^9 B) read+written to GPU HBM
* ``nvlink_gb_per_gpu``      -- GB sent by this GPU over NVLink (one direction)
* ``net_value_per_gpu``      -- volume sent by this GPU through its backend NIC, in ``net_unit``
* ``io_read_gb_per_node``    -- GB read from shared storage by each node
* ``io_write_gb_per_node``   -- GB written to shared storage by each node
* ``observed_step_s``        -- wall-clock seconds per step reported by the workload owner

Profiles are ILLUSTRATIVE teaching values derived from the W-TRAIN / W-INFER workloads in
docs/REFERENCE_CLUSTER.md. The observed step times carry small seeded jitter (+/-2 %) to mimic
run-to-run variation. Regenerating with the same seed yields byte-identical files.

Usage:
    python tools/generate_profiles.py            # writes ../data/
    python tools/generate_profiles.py --out DIR  # writes DIR/
"""
from __future__ import annotations

import argparse
import csv
import io
import random
from pathlib import Path

SEED = 1101

COLUMNS = [
    "workload_id", "name", "phase", "declared_class", "gpus",
    "tflop_per_gpu", "hbm_gb_per_gpu", "nvlink_gb_per_gpu",
    "net_value_per_gpu", "net_unit",
    "io_read_gb_per_node", "io_write_gb_per_node",
    "observed_step_s", "notes",
]

# (id, name, phase, declared_class, gpus, tflop, hbm, nvlink, net, unit, io_r, io_w, observed, notes)
BASE_ROWS: list[tuple] = [
    ("W01", "llm70b-pretrain-step", "train", "compute", 256, 6875, 2100, 1202.6, 9.8, "GB", 0.0005, 0, 17.4,
     "W-TRAIN TP8 PP4 DP8; one optimizer step"),
    ("W02", "llm70b-decode-b32", "infer", "memory", 8, 0.56, 20.18, 0.147, 0, "GB", 0, 0, 0.0095,
     "W-INFER TP8 BF16; one decode step, batch 32, mean context 2048"),
    ("W03", "llm70b-prefill-2k", "infer", "compute", 8, 35.9, 40, 9.4, 0, "GB", 0, 0, 0.075,
     "W-INFER TP8 BF16; one 2048-token prompt"),
    ("W04", "llm7b-dp-finetune", "train", "compute", 64, 2752, 900, 6.0, 24.5, "GB", 0.002, 0, 3.6,
     "pure data parallel; 64k tokens/GPU/step"),
    ("W05", "moe-a2a-train-step", "train", "compute", 128, 480, 600, 30, 60, "GB", 0.001, 0, 1.7,
     "mixture-of-experts, expert parallel across nodes"),
    ("W06", "llm70b-checkpoint-save", "train", "io", 256, 0, 0, 0, 0, "GB", 0, 30.6, 13.0,
     "full W-TRAIN checkpoint (980 GB) written synchronously"),
    ("W07", "video-dataloader-train", "train", "io", 64, 1600, 500, 0, 3, "GB", 40, 0, 2.4,
     "decoded-frame pipeline reading from shared PFS"),
    ("W08", "llm8b-decode-b1-single", "infer", "memory", 1, 0.016, 16.1, 0, 0, "GB", 0, 0, 0.0062,
     "8B model, single GPU, batch 1"),
    ("W09", "tp16-cross-node-train", "train", "compute", 16, 260, 120, 0, 38, "GB", 0, 0, 1.05,
     "tensor parallel group spans two nodes"),
    ("W10", "rag-embedding-batch", "infer", "compute", 8, 120, 60, 0, 0, "GB", 1.0, 0, 0.16,
     "embedding encoder over document batch"),
    ("W11", "dp-allreduce-bench-16node", "other", "communication", 128, 0.01, 30, 10, 80, "Gb", 0, 0, 0.25,
     "all-reduce microbenchmark; NIC volume exported from switch dashboard"),
    ("W12", "kv-transfer-disagg", "infer", "communication", 16, 0.5, 10, 0, 40, "GB", 0, 0, 0.5,
     "prefill->decode KV transfer; NIC volume from host counters"),
    ("W13", "vision-train-vit", "train", "compute", 32, 900, "", 4, 2, "GB", 0.5, 0, 1.3,
     "profile exported from notebook"),
    ("W05", "moe-a2a-train-step-rerun", "train", "communication", 128, 480, 600, 30, 60, "GB", 0.001, 0, 1.72,
     "rerun of W05 pasted into sheet"),
    ("W15", "eval-harness", "infer", "compute", 8, 40, 20, 1, 0, "GB", -2, 0, 0.09,
     "offline evaluation sweep"),
    ("W16", "llm70b-decode-b1-eager", "infer", "memory", 8, 0.0175, 17.58, 0.0046, 0, "GB", 0, 0, 0.025,
     "W-INFER TP8, batch 1, eager mode (no CUDA graphs)"),
    ("W17", "recsys-embedding-a2a-infer", "infer", "communication", 16, 2, 20, 1, 0.6, "GB", 0, 0, 0.018,
     "sharded embedding tables, all-to-all lookups"),
    ("W18", "bert-serving", "infer", "compute", 8, 30, 15, 0.5, 25, "Gbps", 0, 0, 0.05,
     "network figure copied from NIC dashboard"),
]


def _fmt(v: object) -> str:
    """Format a value for CSV: floats with up to 6 significant decimals, no trailing zeros."""
    if isinstance(v, float):
        s = f"{v:.6f}".rstrip("0").rstrip(".")
        return s if s else "0"
    return str(v)


def build_csv(seed: int = SEED) -> str:
    """Return the CSV text for the profile dataset (deterministic for a given seed)."""
    rng = random.Random(seed)
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(COLUMNS)
    for row in BASE_ROWS:
        r = list(row)
        jitter = 1.0 + rng.uniform(-0.02, 0.02)
        r[12] = round(float(r[12]) * jitter, 6)
        w.writerow([_fmt(x) for x in r])
    return buf.getvalue()


PLATFORM_YAML = """\
# ORION-256 / HX8 resource ceilings used by the Chapter 1 workload model.
# All values ILLUSTRATIVE, H100-class (see docs/REFERENCE_CLUSTER.md). Peak values, not achievable ones.
platform: ORION-256 (HX8 nodes)
gpus_per_node: 8
gpu_dense_bf16_tflops: 989            # TFLOP/s per GPU, dense BF16 [VENDOR-SPEC class]
hbm_gb_per_s: 3350                    # GB/s per GPU
nvlink_gb_per_s_per_direction: 450    # GB/s per GPU per direction (900 GB/s total bidirectional)
nic_line_rate_gbit_per_s: 400         # Gb/s per backend NIC, one NIC per GPU (= 50 GB/s)
frontend_gbit_per_s_per_node: 400     # 2 x 200 Gb/s frontend/storage NICs per node
storage_read_gb_per_s_aggregate: 160  # parallel file system, whole cluster
storage_write_gb_per_s_aggregate: 80
latency_fraction_threshold: 0.25      # lower_bound / observed below this => latency/overhead flag
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parent.parent / "data")
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "workload_profiles.csv").write_bytes(build_csv(args.seed).encode("utf-8"))
    (args.out / "platform_orion.yaml").write_bytes(PLATFORM_YAML.encode("utf-8"))
    print(f"wrote {args.out / 'workload_profiles.csv'} and {args.out / 'platform_orion.yaml'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
