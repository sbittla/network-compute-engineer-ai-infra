#!/usr/bin/env python3
"""Step 5b (GPU): pinned versus pageable host memory for the copy to the GPU (Section 3.4).

Times host-to-device (H2D) and device-to-host (D2H) copies of one buffer from pageable and from pinned
memory with CUDA events (median of N after warm-up), records how long the CPU is blocked by a
`non_blocking=True` copy, and reads VmLck/VmPin from /proc/self/status before and after pinning, so you
can see how the CUDA driver pins memory on this platform.

    python pinned_copy.py --mib 256 --reps 10 > pinned_copy.json
"""
from __future__ import annotations

import argparse
import json
import statistics
import time

import torch


def status_kib() -> dict:
    out = {}
    with open("/proc/self/status") as f:
        for line in f:
            k = line.split(":")[0]
            if k in ("VmLck", "VmPin", "VmRSS"):
                out[k] = int(line.split()[1])
    return out


def time_copy(src: torch.Tensor, dst: torch.Tensor, reps: int) -> dict:
    s, e = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
    for _ in range(3):
        dst.copy_(src, non_blocking=True)
    torch.cuda.synchronize()
    ms, host_block = [], []
    for _ in range(reps):
        torch.cuda.synchronize()
        s.record()
        t0 = time.perf_counter()
        dst.copy_(src, non_blocking=True)
        host_block.append((time.perf_counter() - t0) * 1e3)   # how long the CPU was held by the call
        e.record()
        torch.cuda.synchronize()
        ms.append(s.elapsed_time(e))
    med = statistics.median(ms)
    return {"ms": [round(x, 3) for x in ms], "median_ms": round(med, 3),
            "gb_per_s": round(src.numel() * src.element_size() / (med / 1e3) / 1e9, 2),
            "host_blocked_median_ms": round(statistics.median(host_block), 3)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mib", type=int, default=256)
    ap.add_argument("--reps", type=int, default=10)
    a = ap.parse_args()
    n = a.mib << 20
    dev = torch.empty(n, dtype=torch.uint8, device="cuda")
    pageable = torch.ones(n, dtype=torch.uint8)
    st0 = status_kib()
    t0 = time.perf_counter()
    pinned = torch.ones(n, dtype=torch.uint8).pin_memory()
    pin_ms = (time.perf_counter() - t0) * 1e3
    st1 = status_kib()
    res = {
        "gpu": torch.cuda.get_device_name(0), "torch": torch.__version__, "mib": a.mib, "reps": a.reps,
        "proc_status_kib_before_pin": st0, "proc_status_kib_after_pin": st1, "pin_memory_call_ms": round(pin_ms, 1),
        "h2d_pageable": time_copy(pageable, dev, a.reps), "h2d_pinned": time_copy(pinned, dev, a.reps),
        "d2h_pageable": time_copy(dev, pageable, a.reps), "d2h_pinned": time_copy(dev, pinned, a.reps),
    }
    res["h2d_pinned_over_pageable"] = round(res["h2d_pinned"]["gb_per_s"] / res["h2d_pageable"]["gb_per_s"], 2)
    print(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
