#!/usr/bin/env python3
"""Ch 6 hands-on: an empirical roofline from one copy and a GEMM sweep (Section 6.3, "Empirical ceilings").

- Memory roof: device-to-device copy of a 256 MiB buffer (far larger than L2); bytes moved = read + write.
- Compute roof: square BF16 GEMMs, n = 4096 and 8192.
- The sweep: BF16 GEMM M = N = 4096 with K from 16 to 4096. Arithmetic intensity (AI) = 2MNK FLOP over the
  compulsory bytes 2(MK + KN + MN); small K is memory-bound, large K compute-bound, and the ridge point
  (compute roof / memory roof) is where the two meet.

Everything is timed with CUDA events after warm-up; median of 20. Prints one JSON line.
"""
from __future__ import annotations

import json
import statistics
import subprocess
import sys
import time

import torch

BF16_FLOP_PER_CLK_SM = {(8, 9): 512, (8, 6): 512, (8, 0): 2048, (9, 0): 4096}   # dense, NVIDIA whitepapers
BUS_BITS = {"rtx 4060 laptop": 128, "rtx 4060": 128, "rtx 4070 laptop": 128, "rtx 4090": 384, "rtx 3090": 384}


def smi(field: str) -> float:
    try:
        out = subprocess.run(["nvidia-smi", f"--query-gpu={field}", "--format=csv,noheader,nounits", "-i", "0"],
                             capture_output=True, text=True, timeout=20).stdout
        return float(out.strip().splitlines()[0])
    except Exception:  # noqa: BLE001
        return float("nan")


def timeit(fn, reps: int = 20, warm: int = 5) -> float:
    for _ in range(warm):
        fn()
    ts = []
    for _ in range(reps):
        e0, e1 = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
        e0.record()
        fn()
        e1.record()
        e1.synchronize()
        ts.append(e0.elapsed_time(e1))
    return statistics.median(ts)


def sustained(fn, flop: float, seconds: float = 4.0) -> dict:
    """Run fn back to back for ~seconds while nvidia-smi samples the SM clock and power every 100 ms.

    Returns the sustained rate over the whole window and the median SM clock and power of the busy samples,
    so the compute peak can be stated at the clock the GEMM actually ran at (Section 6.3)."""
    q = "clocks.sm,power.draw,utilization.gpu"
    proc = subprocess.Popen(["nvidia-smi", f"--query-gpu={q}", "--format=csv,noheader,nounits", "-lms", "100", "-i", "0"],
                            stdout=subprocess.PIPE, text=True)
    time.sleep(0.3)
    torch.cuda.synchronize()
    t0, n = time.perf_counter(), 0
    while time.perf_counter() - t0 < seconds:
        fn()
        n += 1
        if n % 4 == 0:
            torch.cuda.synchronize()                     # keep the queue short so the window is honest
    torch.cuda.synchronize()
    dt = time.perf_counter() - t0
    proc.terminate()
    out, _ = proc.communicate(timeout=10)
    rows = []
    for line in out.splitlines():
        try:
            c, w, u = (float(x) for x in line.split(","))
            rows.append((c, w, u))
        except ValueError:
            continue
    busy = [r for r in rows if r[2] >= 50] or rows
    return {"calls": n, "seconds": dt, "tflops": n * flop / dt / 1e12, "samples": len(busy),
            "sm_clock_mhz": statistics.median(r[0] for r in busy) if busy else float("nan"),
            "power_w": statistics.median(r[1] for r in busy) if busy else float("nan")}


def main() -> int:
    p = torch.cuda.get_device_properties(0)
    clk, mclk = smi("clocks.max.sm"), smi("clocks.max.memory")
    per_clk = BF16_FLOP_PER_CLK_SM.get((p.major, p.minor))
    bits = next((b for k, b in sorted(BUS_BITS.items(), key=lambda kv: -len(kv[0])) if k in p.name.lower()), None)
    spec_tflops = p.multi_processor_count * per_clk * clk * 1e6 / 1e12 if per_clk else None
    spec_gbs = mclk * 1e6 * 2 * bits / 8 / 1e9 if bits else None

    n_bytes = 256 * 2 ** 20
    src = torch.empty(n_bytes, dtype=torch.uint8, device="cuda").random_(0, 255)
    dst = torch.empty_like(src)
    copy_ms = timeit(lambda: dst.copy_(src))
    copy_gbs = 2 * n_bytes / (copy_ms / 1e3) / 1e9
    del src, dst

    square = {}
    for n in (4096, 8192):
        a = torch.randn(n, n, device="cuda", dtype=torch.bfloat16)
        b = torch.randn_like(a)
        ms = timeit(lambda: torch.matmul(a, b), reps=10)
        square[n] = {"ms": ms, "tflops": 2 * n ** 3 / (ms / 1e3) / 1e12}
        if n == 8192:
            square[n]["sustained"] = sustained(lambda: torch.matmul(a, b), 2 * n ** 3)
        del a, b
    sm_clock_after = smi("clocks.sm")

    sweep = []
    m = nn = 4096
    for k in (16, 32, 64, 128, 256, 512, 1024, 2048, 4096):
        a = torch.randn(m, k, device="cuda", dtype=torch.bfloat16)
        b = torch.randn(k, nn, device="cuda", dtype=torch.bfloat16)
        ms = timeit(lambda: torch.matmul(a, b))
        flop = 2 * m * nn * k
        byt = 2 * (m * k + k * nn + m * nn)
        sweep.append({"K": k, "ai_flop_per_byte": flop / byt, "ms": ms, "tflops": flop / (ms / 1e3) / 1e12,
                      "gbs": byt / (ms / 1e3) / 1e9})
        del a, b
    roof_t = max(x["tflops"] for x in square.values())
    st = square[8192]["sustained"]
    peak_sustained = p.multi_processor_count * per_clk * st["sm_clock_mhz"] * 1e6 / 1e12 if per_clk else None
    ridge = roof_t * 1e12 / (copy_gbs * 1e9)
    for x in sweep:
        x["bound"] = "memory" if x["ai_flop_per_byte"] < ridge else "compute"
        x["attainable_tflops"] = min(roof_t, x["ai_flop_per_byte"] * copy_gbs / 1e3)
        x["pct_of_attainable"] = 100 * x["tflops"] / x["attainable_tflops"]
    print(json.dumps({"gpu": p.name, "sm_count": p.multi_processor_count, "clocks_max_sm_mhz": clk,
                      "clocks_max_mem_mhz": mclk, "bus_bits": bits,
                      "spec_bf16_tflops_at_max_clock": spec_tflops, "spec_dram_gbs": spec_gbs,
                      "sustained_gemm_sm_clock_mhz": st["sm_clock_mhz"], "sustained_gemm_power_w": st["power_w"],
                      "sustained_gemm_tflops": st["tflops"], "bf16_tflops_at_sustained_clock": peak_sustained,
                      "measured_copy_gbs": copy_gbs, "copy_buffer_bytes": n_bytes, "square_gemm": square,
                      "measured_bf16_roof_tflops": roof_t, "measured_ridge_flop_per_byte": ridge,
                      "sm_clock_after_gemm_mhz": sm_clock_after, "sweep": sweep}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
