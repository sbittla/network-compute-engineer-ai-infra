#!/usr/bin/env python3
"""Ch 6 hands-on, step 1: four ways to time the same BF16 GEMM, three of them wrong.

  A  host timer around the call, no synchronize        -> times the launch, not the GEMM
  B  host timer with synchronize, ONE call, cold         -> includes library initialisation and first-call costs
  C  mean of 20 synchronized calls including the first   -> the warm-up iteration drags the mean
  D  CUDA events, 5 warm-up calls discarded, median of 50 -> the protocol (Section 6.6)

Each method's implied TFLOP/s is printed next to the GPU's vendor-class BF16 peak, so an impossible number is
obvious. Prints one JSON line.
"""
from __future__ import annotations

import json
import statistics
import subprocess
import sys
import time

import torch

BF16_FLOP_PER_CLK_SM = {(8, 9): 512, (8, 6): 512, (8, 0): 2048, (9, 0): 4096}   # dense, NVIDIA whitepapers


def max_sm_clock_mhz() -> float:
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=clocks.max.sm", "--format=csv,noheader,nounits", "-i", "0"],
                             capture_output=True, text=True, timeout=20).stdout
        return float(out.strip().splitlines()[0])
    except Exception:  # noqa: BLE001
        return float("nan")


def main() -> int:
    n = 4096
    flop = 2 * n ** 3
    p = torch.cuda.get_device_properties(0)
    per_clk = BF16_FLOP_PER_CLK_SM.get((p.major, p.minor))
    clk = max_sm_clock_mhz()
    peak = p.multi_processor_count * per_clk * clk * 1e6 / 1e12 if per_clk else float("nan")
    a = torch.randn(n, n, device="cuda", dtype=torch.bfloat16)
    b = torch.randn_like(a)
    torch.cuda.synchronize()

    # B first, while the GEMM path is cold
    t0 = time.perf_counter()
    torch.matmul(a, b)
    torch.cuda.synchronize()
    cold_ms = (time.perf_counter() - t0) * 1e3

    # A: no synchronize (averaged over 20 calls, as a careless loop would)
    torch.cuda.synchronize()
    t0 = time.perf_counter()
    for _ in range(20):
        torch.matmul(a, b)
    nosync_ms = (time.perf_counter() - t0) * 1e3 / 20
    torch.cuda.synchronize()

    # C: mean of 20 synchronized calls whose first is the cold call measured in B
    c_ms = [cold_ms]
    for _ in range(19):
        t0 = time.perf_counter()
        torch.matmul(a, b)
        torch.cuda.synchronize()
        c_ms.append((time.perf_counter() - t0) * 1e3)

    # D: CUDA events, warm-up discarded, median
    ev = []
    for i in range(55):
        e0, e1 = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
        e0.record()
        torch.matmul(a, b)
        e1.record()
        e1.synchronize()
        if i >= 5:
            ev.append(e0.elapsed_time(e1))
    d_ms = statistics.median(ev)

    def tf(ms):
        return flop / (ms / 1e3) / 1e12
    out = {"n": n, "flop": flop, "gpu": p.name, "sm_count": p.multi_processor_count, "clocks_max_sm_mhz": clk,
           "bf16_peak_tflops_at_max_clock": peak,
           "A_nosync_ms": nosync_ms, "A_tflops": tf(nosync_ms),
           "B_cold_single_ms": cold_ms, "B_tflops": tf(cold_ms),
           "C_mean_with_first_ms": statistics.mean(c_ms), "C_tflops": tf(statistics.mean(c_ms)),
           "D_events_median_ms": d_ms, "D_tflops": tf(d_ms), "D_iqr_ms": statistics.quantiles(ev, n=4)[2] - statistics.quantiles(ev, n=4)[0]}
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
