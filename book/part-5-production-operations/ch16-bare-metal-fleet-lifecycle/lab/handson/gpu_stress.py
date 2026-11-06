#!/usr/bin/env python3
"""Chapter 16 hands-on lab: GPU acceptance steps (identity, memory pattern, numerics, stress + telemetry).

    python gpu_stress.py --out results/<run-id> [--seconds 120]

Run it under the GPU lock (run.sh does). Writes <out>/raw/gpu_stress.json, <out>/raw/telemetry.csv
(nvidia-smi sampled every 500 ms during the stress), and <out>/raw/clock_event_counters_{before,after}.csv.
Tolerances are fixed here, before anything runs:
  FP32 GEMM (TF32 off) vs a float64 CPU reference: max |err| / (|A| |B| row-col bound) <= 1e-5
  FP16 GEMM (FP32 accumulate) vs a float32 CPU reference of the same FP16 inputs: same bound <= 2e-3
  The stress GEMM's golden check: the same inputs must give bit-identical outputs every time.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path

import torch

FIELDS = ("timestamp,temperature.gpu,power.draw,enforced.power.limit,clocks.sm,clocks.max.sm,clocks.mem,"
          "pcie.link.gen.current,pcie.link.gen.max,pcie.link.width.current,pcie.link.width.max,"
          "utilization.gpu,memory.used,clocks_event_reasons.active")
COUNTERS = ("clocks_event_reasons_counters.sw_power_cap,clocks_event_reasons_counters.sw_thermal_slowdown,"
            "clocks_event_reasons_counters.hw_thermal_slowdown,clocks_event_reasons_counters.hw_power_brake_slowdown")
TOL_FP32, TOL_FP16 = 1e-5, 2e-3


def smi(query: str, out: Path) -> str:
    r = subprocess.run(["nvidia-smi", f"--query-gpu={query}", "--format=csv"], capture_output=True, text=True, timeout=30)
    out.write_text(r.stdout + r.stderr)
    return r.stdout


def gemm_error(a: torch.Tensor, b: torch.Tensor, dtype: torch.dtype, ref_dtype: torch.dtype) -> float:
    """Max error of a GPU GEMM against a CPU reference, scaled by |A||B| (the rounding-error bound's shape)."""
    ga, gb = a.to("cuda", dtype), b.to("cuda", dtype)
    out = (ga @ gb).float().cpu().double()
    ca, cb = ga.cpu().to(ref_dtype), gb.cpu().to(ref_dtype)  # the same rounded inputs the GPU saw
    ref = (ca @ cb).double()
    bound = (ca.abs().double() @ cb.abs().double())
    return float(((out - ref).abs() / bound.clamp_min(1e-30)).max())


def pattern_test(nbytes: int) -> dict:
    """Write/verify patterns over a large device buffer; count mismatching 32-bit words."""
    n = nbytes // 4
    buf = torch.empty(n, dtype=torch.int32, device="cuda")
    mismatches, t_fill = 0, 0.0
    pats = {"0x00000000": 0, "0xFFFFFFFF": -1, "0x55555555": 0x55555555, "0xAAAAAAAA": -0x55555556}
    for _, v in pats.items():
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        buf.fill_(v)
        torch.cuda.synchronize()
        t_fill += time.perf_counter() - t0
        mismatches += int((buf != v).sum())
    # address-in-address: each word holds its own index, catches aliasing between addresses
    idx = torch.arange(n, dtype=torch.int32, device="cuda")
    buf.copy_(idx)
    mismatches += int((buf != idx).sum())
    del buf, idx
    torch.cuda.empty_cache()
    return {"bytes": nbytes, "patterns": len(pats) + 1, "mismatched_words": mismatches,
            "fill_GBps": len(pats) * nbytes / t_fill / 1e9}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--seconds", type=float, default=120.0)
    ap.add_argument("--n", type=int, default=4096, help="stress GEMM size (FP16, n x n x n)")
    a = ap.parse_args()
    raw = a.out / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    assert torch.cuda.is_available(), "no CUDA device"
    torch.backends.cuda.matmul.allow_tf32 = False
    p = torch.cuda.get_device_properties(0)
    res: dict = {"torch": torch.__version__, "cuda": torch.version.cuda,
                 "identity": {"name": p.name, "total_memory_bytes": p.total_memory, "sm_count": p.multi_processor_count,
                              "capability": f"{p.major}.{p.minor}"},
                 "tolerances": {"fp32_vs_fp64": TOL_FP32, "fp16_vs_fp32": TOL_FP16, "golden": "bit-identical"}}

    # 1. device memory: write/verify half of what is free, capped at 1.5 GiB (the card is shared)
    free, _ = torch.cuda.mem_get_info()
    res["memory_pattern"] = pattern_test(min(int(1.5 * 2**30), int(free * 0.5)) // 4 * 4)
    print(f"memory pattern: {res['memory_pattern']['bytes'] / 2**30:.2f} GiB, "
          f"{res['memory_pattern']['mismatched_words']} mismatched words", flush=True)

    # 2. numerics, cold
    g = torch.Generator().manual_seed(16)
    A, B = torch.randn(2048, 2048, generator=g), torch.randn(2048, 2048, generator=g)
    num = {"cold": {"fp32_err": gemm_error(A, B, torch.float32, torch.float64),
                    "fp16_err": gemm_error(A, B, torch.float16, torch.float32)}}
    print(f"numerics cold: fp32 {num['cold']['fp32_err']:.2e}, fp16 {num['cold']['fp16_err']:.2e}", flush=True)

    # 3. stress with telemetry; golden bitwise check every ~2 s
    x = torch.randn(a.n, a.n, device="cuda", dtype=torch.float16)
    y = torch.randn(a.n, a.n, device="cuda", dtype=torch.float16)
    golden_out = (x @ y).clone()
    smi(COUNTERS, raw / "clock_event_counters_before.csv")
    tele = open(raw / "telemetry.csv", "w")
    mon = subprocess.Popen(["nvidia-smi", f"--query-gpu={FIELDS}", "--format=csv", "-lms", "500"], stdout=tele,
                           stderr=subprocess.STDOUT)
    time.sleep(1.5)
    flop = 2 * a.n ** 3
    windows, golden_checks, golden_bad = [], 0, 0
    t_start = time.perf_counter()
    t_win, n_win, t_gold = t_start, 0, t_start
    try:
        while True:
            for _ in range(10):            # short bursts, then synchronize: wall-clock windows stay honest
                z = x @ y
            torch.cuda.synchronize()
            n_win += 10
            now = time.perf_counter()
            if now - t_win >= 1.0 or now - t_start >= a.seconds:
                windows.append({"t_s": round(now - t_start, 2), "tflops": n_win * flop / (now - t_win) / 1e12})
                t_win, n_win = now, 0
                if now - t_gold >= 2.0:
                    golden_checks += 1
                    golden_bad += int(not torch.equal(z, golden_out))
                    t_gold = now
                if now - t_start >= a.seconds:
                    break
        # 4. numerics again, hot (straight after the stress)
        num["hot"] = {"fp32_err": gemm_error(A, B, torch.float32, torch.float64),
                      "fp16_err": gemm_error(A, B, torch.float16, torch.float32)}
    finally:
        time.sleep(1.0)
        mon.terminate()
        try:
            mon.wait(timeout=10)
        except subprocess.TimeoutExpired:
            mon.kill()
        tele.close()
    smi(COUNTERS, raw / "clock_event_counters_after.csv")
    print(f"numerics hot: fp32 {num['hot']['fp32_err']:.2e}, fp16 {num['hot']['fp16_err']:.2e}", flush=True)
    res["numerics"] = num
    res["stress"] = {"seconds": a.seconds, "gemm": f"FP16 {a.n}^3, FP32 accumulate", "windows": windows,
                     "golden_checks": golden_checks, "golden_mismatches": golden_bad,
                     "gpu_mem_peak_bytes": torch.cuda.max_memory_allocated()}
    tf = sorted(w["tflops"] for w in windows)
    print(f"stress: {a.seconds:.0f} s, median {tf[len(tf) // 2]:.1f} TFLOP/s, golden {golden_bad}/{golden_checks} mismatched",
          flush=True)
    (raw / "gpu_stress.json").write_text(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
