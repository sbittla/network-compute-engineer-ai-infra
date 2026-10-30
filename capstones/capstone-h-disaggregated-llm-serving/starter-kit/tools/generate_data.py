#!/usr/bin/env python3
"""Generate the Capstone H dataset: a seeded request trace, accelerator and link profiles, the
proposed network QoS mapping, SLOs and deployment candidates.

Deterministic (byte-identical on regeneration). All values are [ILLUSTRATIVE]; the two non-H100
accelerator classes are HYPOTHETICAL teaching profiles, not real products.

Usage:
    python generate_data.py                 # writes ../data
    python generate_data.py --out /tmp/x
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np
import yaml

SEED = 15
DURATION_S = 300.0
BASE_RPS = 30.0
BURST = (120.0, 150.0, 2.5)      # start, end, rate multiplier

HARDWARE = [
    {"name": "h100-class", "gpus_per_instance": 8, "peak_TFLOPs": 989, "hbm_TBps": 3.35, "hbm_GB": 80,
     "usd_per_gpu_hour": 4.00, "note": "ORION HX8 GPU; VENDOR-SPEC class values, ILLUSTRATIVE price"},
    {"name": "compute-dense-class", "gpus_per_instance": 8, "peak_TFLOPs": 1400, "hbm_TBps": 2.0, "hbm_GB": 48,
     "usd_per_gpu_hour": 3.20, "note": "HYPOTHETICAL prefill-oriented accelerator"},
    {"name": "hbm-rich-class", "gpus_per_instance": 8, "peak_TFLOPs": 800, "hbm_TBps": 4.8, "hbm_GB": 141,
     "usd_per_gpu_hour": 4.50, "note": "HYPOTHETICAL decode-oriented accelerator"},
]

LINKS = [
    {"name": "rdma-400g-x8", "transport": "rdma", "line_rate": 400, "unit": "Gb/s", "nics": 8, "efficiency": 0.90,
     "overhead_ms": 0.05, "path": "backend RoCEv2, rail-aligned, GPUDirect RDMA"},
    {"name": "rdma-400g-x1", "transport": "rdma", "line_rate": 400, "unit": "Gb/s", "nics": 1, "efficiency": 0.90,
     "overhead_ms": 0.05, "path": "backend RoCEv2, single rail"},
    {"name": "tcp-200g-x2", "transport": "tcp", "line_rate": 200, "unit": "Gb/s", "nics": 2, "efficiency": 0.60,
     "overhead_ms": 0.50, "path": "frontend TCP, host-staged copies; frontend is 1.5:1 oversubscribed by bandwidth"},
    {"name": "tcp-200g-x1-ch15", "transport": "tcp", "line_rate": 200, "unit": "Gb/s", "nics": 1, "efficiency": 0.50,
     "overhead_ms": 0.50, "path": "Chapter 15 profile: one 200G frontend port at 50 % achievable (100 Gb/s)"},
    {"name": "rdma-400g-x8-vendor-sheet", "transport": "rdma", "line_rate": 400, "unit": "GB/s", "nics": 8,
     "efficiency": 0.90, "overhead_ms": 0.05, "path": "copied from a slide deck"},
]

QOS = {
    "fabric": "ORION backend (shared by training on rack-01..07 and inference on rack-08)",
    "classes": [
        {"name": "training-roce", "dscp": 26, "tc": 3, "pfc": True, "ecn": True},
        {"name": "cnp", "dscp": 48, "tc": 6, "strict_priority": True},
        {"name": "kv-transfer", "dscp": 26, "tc": 3, "pfc": True, "ecn": True},
        {"name": "best-effort", "dscp": 0, "tc": 0, "pfc": False, "ecn": True},
    ],
    "kv_path_crosses_tenant_boundary": True,
    "kv_encryption": "none",
}

SLO = {
    "ttft_p95_s": 0.8, "ttft_applies_to_prompt_tokens_max": 4096, "ttft_long_p95_s": 3.0,
    "tpot_p95_s": 0.050, "itl_p99_s": 0.100, "availability": 0.999, "target_rps": BASE_RPS, "max_reject_rate": 0.10,
}

CONFIG = {
    "model": "W-INFER 70B, BF16, TP=8 per HX8 instance",
    "kv_bytes_per_token": 327680,
    "rho_max": 0.7,
    "candidates": {
        "colocated": {"kind": "colocated", "instances": 7, "chunk_tokens": None},
        "colocated_chunked": {"kind": "colocated", "instances": 7, "chunk_tokens": 512},
        "disagg_rdma": {"kind": "disaggregated", "prefill": 5, "decode": 2, "link": "rdma-400g-x8"},
        "disagg_tcp": {"kind": "disaggregated", "prefill": 5, "decode": 2, "link": "tcp-200g-x2"},
    },
}


def build_trace(rng: np.random.Generator) -> list[dict]:
    t, rows, rid = 0.0, [], 0
    while True:
        rate = BASE_RPS * (BURST[2] if BURST[0] <= t < BURST[1] else 1.0)
        t += float(rng.exponential(1.0 / rate))
        if t >= DURATION_S:
            break
        prompt = int(np.clip(rng.lognormal(np.log(1800), 0.6), 64, 8192))
        if rng.random() < 0.01:
            prompt = 32768            # long-context requests (planted)
        out = int(np.clip(rng.lognormal(np.log(250), 0.5), 16, 1024))
        rows.append({"rid": rid, "arrival_s": round(t, 4), "prompt": prompt, "output": out})
        rid += 1
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parent.parent / "data")
    args = ap.parse_args()
    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)

    def wcsv(name: str, rows: list[dict]) -> None:
        with open(out / name, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
            w.writeheader()
            w.writerows(rows)

    def wyaml(name: str, obj: object) -> None:
        with open(out / name, "w", newline="\n", encoding="utf-8") as fh:
            fh.write(yaml.safe_dump(obj, sort_keys=False))

    wcsv("trace.csv", build_trace(rng))
    wcsv("hardware.csv", HARDWARE)
    wcsv("links.csv", LINKS)
    wyaml("qos_proposal.yaml", QOS)
    wyaml("slo.yaml", SLO)
    wyaml("config.yaml", CONFIG)
    print(f"wrote dataset to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
