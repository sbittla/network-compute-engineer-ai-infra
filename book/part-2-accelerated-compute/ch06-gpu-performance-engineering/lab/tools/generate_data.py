#!/usr/bin/env python3
"""Generate the Chapter 6 lab datasets (seed 6, byte-identical on regeneration).

    data/bench_baseline.csv      baseline kernel variant, 6 runs x 60 iterations
    data/bench_candidate_b.csv   candidate B (a real ~3 % improvement), 6 runs x 60 iterations
    data/bench_candidate_c.csv   candidate C (no real change), 6 runs, warm-up already stripped by its harness
    data/bench_aa.csv            A/A: baseline variant measured as two groups of 6 runs (noise floor)
    data/kernels.csv             per-kernel FLOP, DRAM bytes and measured time for roofline classification
    data/device.yaml             ORION H100-class ceilings

All benchmark values are [SIMULATED]: latency of one fused attention-block microbenchmark on an ORION
HX8 GPU, generated from a run-level + iteration-level noise model with planted traps (see solutions/).
Kernel rows are [SIMULATED] counter values chosen to exercise roofline reasoning.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np

SEED = 6
MAX_BOOST_SM_MHZ = 1980
SUSTAINED_SM_MHZ = 1830   # typical sustained SM clock under dense GEMM load on ORION [ILLUSTRATIVE]
BASE_MS = 4.000
WARMUP_FACTORS = [1.62, 1.31, 1.14, 1.05, 1.02]  # first 5 iterations: JIT/autotune, allocator, clock ramp
FIELDS = ["run_id", "iter", "latency_ms", "sm_clock_mhz", "gpu_temp_c", "power_w", "clocks_event_reasons",
          "driver", "cuda", "torch", "kernel_variant"]
SW = {"driver": "570.124.06", "cuda": "12.8", "torch": "2.4.0"}


def make_runs(rng, variant: str, true_ms: float, n_runs: int, n_iter: int, *, prefix: str,
              include_warmup: bool = True, version_override: dict | None = None,
              throttle_run: int | None = None) -> list[dict]:
    rows = []
    for r in range(1, n_runs + 1):
        run_id = f"{prefix}{r}"
        sw = dict(SW)
        speed = 1.0
        if version_override and r in version_override:
            sw.update(version_override[r]["sw"])
            speed = version_override[r]["speed"]
        run_offset = rng.normal(0.0, 0.004)
        throttled = throttle_run == r
        start = 0 if include_warmup else len(WARMUP_FACTORS)
        for it in range(start, start + n_iter):
            wf = WARMUP_FACTORS[it] if it < len(WARMUP_FACTORS) else 1.0
            lat = true_ms * speed * (1 + run_offset) * (1 + rng.normal(0.0, 0.008)) * wf
            if rng.random() < 0.02:  # occasional host-side hiccup (GC, interrupt) — a real outlier, kept
                lat *= 1 + abs(rng.normal(0.0, 0.06))
            clk = SUSTAINED_SM_MHZ - int(abs(rng.normal(0, 6)))
            temp = int(round(rng.normal(66, 1.5)))
            power = int(round(rng.normal(612, 12)))
            reasons = "none"
            if rng.random() < 0.03:  # routine power-cap clock events under heavy GEMMs: not a reason to exclude
                reasons = "sw_power_cap"
                clk -= 15
            if throttled and it < 12:  # poor airflow in this chassis slot: temperature climbs toward the limit
                temp = int(round(70 + 16 * it / 11 + rng.normal(0, 0.5)))
            if throttled and it >= 12:  # thermal ramp: starts clean, slows after ~12 iterations
                clk = 1452 - int(abs(rng.normal(0, 15)))
                temp = int(round(rng.normal(88, 0.8)))
                power = int(round(rng.normal(540, 10)))
                lat *= SUSTAINED_SM_MHZ / clk
                reasons = "sw_thermal_slowdown"
            rows.append({"run_id": run_id, "iter": it, "latency_ms": f"{lat:.4f}", "sm_clock_mhz": clk,
                         "gpu_temp_c": temp, "power_w": power, "clocks_event_reasons": reasons,
                         **sw, "kernel_variant": variant})
    return rows


KERNELS = [
    # name, precision, flop, dram_bytes, time_us
    ("gemm_bf16_8192x8192x8192", "bf16_tensor", 2 * 8192**3, 3 * 8192 * 8192 * 2, 1588.0),
    ("gemm_bf16_decode_m16", "bf16_tensor", 2 * 16 * 8192 * 8192, 8192 * 8192 * 2 + 2 * 16 * 8192 * 2, 47.3),
    ("layernorm_fwd_bf16", "bf16_tensor", 8 * 8192 * 8192, 3 * 8192 * 8192 * 2, 150.2),
    ("flash_attn_fwd_bf16", "bf16_tensor", 4 * 8 * 4096 * 4096 * 128 * 32, 4 * 8 * 4096 * 128 * 32 * 2, 4043.0),
    ("fp32_simt_stencil", "fp32_simt", 5.0e11, 1.0e9, 8780.0),
    ("bias_add_l2_resident", "bf16_tensor", 3.3e7, 100_663_296, 20.0),
    ("gemm_fp8_8192x8192x8192", "fp8_tensor", 2 * 8192**3, 3 * 8192 * 8192, 926.0),
    ("embedding_gather_bf16", "bf16_tensor", 0, 268_435_456, 160.0),
    ("gemm_bf16_4096x4096x512", "bf16_tensor", 2 * 4096 * 4096 * 512, (4096 * 512 * 2 + 512 * 4096 + 4096 * 4096) * 2, 61.0),
]


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="\n", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parent.parent / "data")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    base = make_runs(rng, "fused_attn_v1", BASE_MS, 6, 60, prefix="A",
                     version_override={3: {"sw": {"torch": "2.3.1"}, "speed": 0.97}})
    cand_b = make_runs(rng, "fused_attn_v2", BASE_MS * 0.970, 6, 60, prefix="B", throttle_run=4)
    cand_c = make_runs(rng, "fused_attn_v1_tuned", BASE_MS * 0.997, 6, 55, prefix="C", include_warmup=False)
    aa = make_runs(rng, "fused_attn_v1", BASE_MS, 6, 60, prefix="AA1-") + \
        make_runs(rng, "fused_attn_v1", BASE_MS, 6, 60, prefix="AA2-")
    write_csv(args.out / "bench_baseline.csv", base, FIELDS)
    write_csv(args.out / "bench_candidate_b.csv", cand_b, FIELDS)
    write_csv(args.out / "bench_candidate_c.csv", cand_c, FIELDS)
    write_csv(args.out / "bench_aa.csv", aa, FIELDS)
    krows = [{"name": n, "precision": p, "flop": f"{f:.6g}", "dram_bytes": int(b), "time_us": f"{t:.1f}"}
             for n, p, f, b, t in KERNELS]
    write_csv(args.out / "kernels.csv", krows, ["name", "precision", "flop", "dram_bytes", "time_us"])
    (args.out / "device.yaml").write_text(
        "# ORION HX8 GPU ceilings (H100-SXM-class). [VENDOR-SPEC, 2026-10] dense peaks; re-verify per SKU.\n"
        "name: H100-SXM-class\n"
        "peak_flops:\n"
        "  bf16_tensor: 989.0e12   # dense, no sparsity\n"
        "  fp8_tensor: 1979.0e12   # dense, no sparsity\n"
        "  fp32_simt: 67.0e12      # non-tensor FP32\n"
        "hbm_bytes_per_s: 3.35e12\n"
        "max_boost_sm_clock_mhz: 1980\n"
        "typical_sustained_sm_clock_mhz: 1830   # under dense load [ILLUSTRATIVE]; judge throttling against peers\n", encoding="utf-8", newline="\n")
    print(f"wrote datasets to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
