#!/usr/bin/env python3
"""Step 1: pinned versus pageable copies of batch-sized buffers, and what pinning costs.

For each size: H2D bandwidth from pageable and from pinned memory (CUDA events, median after warm-up);
how long the CPU is held by a `non_blocking=True` copy from each; and the cost of `tensor.pin_memory()`
on a fresh tensor (first call, and the median of five calls), which is what you pay if you pin every batch
instead of reusing a pinned pool.

    python copies.py > copies.json
"""
from __future__ import annotations

import json
import statistics
import time

import torch

MiB = 1 << 20


def timed(dst, src, reps=15):
    s, e = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
    for _ in range(3):
        dst.copy_(src, non_blocking=True)
    torch.cuda.synchronize()
    gpu_ms, cpu_ms = [], []
    for _ in range(reps):
        torch.cuda.synchronize()
        s.record()
        t0 = time.perf_counter()
        dst.copy_(src, non_blocking=True)
        cpu_ms.append((time.perf_counter() - t0) * 1e3)
        e.record()
        torch.cuda.synchronize()
        gpu_ms.append(s.elapsed_time(e))
    return statistics.median(gpu_ms), statistics.median(cpu_ms)


def main() -> int:
    rows = []
    for mib in (1, 8, 64):
        n = mib * MiB
        dev = torch.empty(n, dtype=torch.uint8, device="cuda")
        pageable = torch.ones(n, dtype=torch.uint8)
        pinned = torch.ones(n, dtype=torch.uint8).pin_memory()
        g_pg, c_pg = timed(dev, pageable)
        g_pn, c_pn = timed(dev, pinned)
        pin_ms = []
        for _ in range(5):
            fresh = torch.ones(n, dtype=torch.uint8)
            t0 = time.perf_counter()
            p = fresh.pin_memory()
            pin_ms.append((time.perf_counter() - t0) * 1e3)
            del p, fresh
        pin = statistics.median(pin_ms)
        rows.append({
            "mib": mib,
            "pageable_ms": round(g_pg, 4), "pageable_gb_per_s": round(n / g_pg / 1e6, 3), "pageable_cpu_blocked_ms": round(c_pg, 4),
            "pinned_ms": round(g_pn, 4), "pinned_gb_per_s": round(n / g_pn / 1e6, 3), "pinned_cpu_blocked_ms": round(c_pn, 4),
            # the first call allocates fresh pinned memory from the driver; later calls of the same size are served
            # from PyTorch's caching host allocator, which reuses pinned blocks freed by earlier calls
            "pin_memory_first_call_ms": round(pin_ms[0], 3),
            "pin_memory_call_ms": round(pin, 3), "pin_memory_call_ms_raw": [round(x, 3) for x in pin_ms],
            # pin a fresh buffer every batch, then copy it: the per-batch rate you actually get
            "pin_every_batch_gb_per_s": round(n / (pin + g_pn) / 1e6, 3),
        })
        del dev, pageable, pinned
        torch.cuda.empty_cache()
    print(json.dumps({"gpu": torch.cuda.get_device_name(0), "torch": torch.__version__, "rows": rows}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
