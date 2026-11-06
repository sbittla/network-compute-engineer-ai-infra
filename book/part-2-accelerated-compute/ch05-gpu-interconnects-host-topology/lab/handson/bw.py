#!/usr/bin/env python3
"""Host<->GPU copy bandwidth over this machine's PCIe link (Sections 5.2 and 5.5).

    python bw.py sweep    > sweep.json      # H2D and D2H, pinned and pageable, 64 KiB .. 512 MiB
    python bw.py bidir    > bidir.json      # H2D and D2H at the same time on two streams (full duplex?)
    python bw.py contend  > contend.json    # pinned H2D alone vs while a GEMM loop runs on another stream
    python bw.py point    > point.json      # 256 MiB pinned and pageable H2D only (used for the CPU-affinity runs)
    python bw.py hold --seconds 8           # sustained H2D+D2H traffic for link-state sampling

Every number is a median of timed repetitions after warm-up, timed with CUDA events on the GPU.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import time

import torch

MiB = 1 << 20


def bufs(n: int, pinned: bool):
    host = torch.ones(n, dtype=torch.uint8)
    if pinned:
        host = host.pin_memory()
    return host, torch.empty(n, dtype=torch.uint8, device="cuda")


def time_copy(dst, src, reps: int, stream=None) -> list[float]:
    stream = stream or torch.cuda.current_stream()
    s, e = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
    with torch.cuda.stream(stream):
        for _ in range(2):
            dst.copy_(src, non_blocking=True)
    torch.cuda.synchronize()
    out = []
    for _ in range(reps):
        with torch.cuda.stream(stream):
            s.record(stream)
            dst.copy_(src, non_blocking=True)
            e.record(stream)
        torch.cuda.synchronize()
        out.append(s.elapsed_time(e))
    return out


def gbps(nbytes: int, ms: float) -> float:
    return round(nbytes / (ms / 1e3) / 1e9, 3)


def sweep(a) -> dict:
    rows = []
    for mib in (0.0625, 0.25, 1, 4, 16, 64, 256, 512):
        n = int(mib * MiB)
        reps = 30 if mib <= 16 else 10
        for pinned in (False, True):
            host, dev = bufs(n, pinned)
            for direction in ("h2d", "d2h"):
                ms = time_copy(dev, host, reps) if direction == "h2d" else time_copy(host, dev, reps)
                med = statistics.median(ms)
                rows.append({"direction": direction, "memory": "pinned" if pinned else "pageable", "mib": mib,
                             "reps": reps, "median_ms": round(med, 4), "gb_per_s": gbps(n, med),
                             "min_ms": round(min(ms), 4), "max_ms": round(max(ms), 4)})
            del host, dev
            torch.cuda.empty_cache()
    return {"rows": rows}


def bidir(a) -> dict:
    n = 256 * MiB
    h_up, d_up = bufs(n, True)
    h_dn, d_dn = bufs(n, True)
    s_up, s_dn = torch.cuda.Stream(), torch.cuda.Stream()
    one_up = statistics.median(time_copy(d_up, h_up, 10, s_up))
    one_dn = statistics.median(time_copy(h_dn, d_dn, 10, s_dn))
    both = []
    for _ in range(3):
        d_up.copy_(h_up, non_blocking=True); h_dn.copy_(d_dn, non_blocking=True)
    torch.cuda.synchronize()
    for _ in range(10):
        start = torch.cuda.Event(enable_timing=True)
        e_up, e_dn = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
        start.record()
        s_up.wait_event(start); s_dn.wait_event(start)
        with torch.cuda.stream(s_up):
            d_up.copy_(h_up, non_blocking=True); e_up.record(s_up)
        with torch.cuda.stream(s_dn):
            h_dn.copy_(d_dn, non_blocking=True); e_dn.record(s_dn)
        torch.cuda.synchronize()
        both.append(max(start.elapsed_time(e_up), start.elapsed_time(e_dn)))
    t_both = statistics.median(both)
    return {"mib": 256, "h2d_alone_gb_per_s": gbps(n, one_up), "d2h_alone_gb_per_s": gbps(n, one_dn),
            "concurrent_wall_ms": round(t_both, 3), "concurrent_aggregate_gb_per_s": gbps(2 * n, t_both),
            "concurrent_ms_raw": [round(x, 3) for x in both],
            "aggregate_over_best_unidirectional": round(gbps(2 * n, t_both) / max(gbps(n, one_up), gbps(n, one_dn)), 3)}


def contend(a) -> dict:
    n = 256 * MiB
    host, dev = bufs(n, True)
    alone = time_copy(dev, host, 10)
    x = torch.randn(4096, 4096, device="cuda", dtype=torch.float16)
    s_comp, s_copy = torch.cuda.Stream(), torch.cuda.Stream()
    under = []
    for _ in range(10):
        with torch.cuda.stream(s_comp):            # queue far more GEMM work than the copy takes
            for _ in range(40):
                y = x @ x
        under += time_copy(dev, host, 1, s_copy)
        torch.cuda.synchronize()
    ms_gemm = []
    for _ in range(3):
        s, e = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
        s.record(); [x @ x for _ in range(40)]; e.record(); torch.cuda.synchronize()
        ms_gemm.append(s.elapsed_time(e))
    return {"mib": 256, "alone_gb_per_s": gbps(n, statistics.median(alone)),
            "under_gemm_gb_per_s": gbps(n, statistics.median(under)),
            "under_gemm_ms_raw": [round(v, 3) for v in under], "gemm_burst_ms": round(statistics.median(ms_gemm), 1),
            "ratio_under_over_alone": round(statistics.median(alone) / statistics.median(under), 3)}


def point(a) -> dict:
    n = 256 * MiB
    out = {"cpu_affinity": sorted(os.sched_getaffinity(0)), "mib": 256}
    for pinned in (False, True):
        host, dev = bufs(n, pinned)
        ms = time_copy(dev, host, 10)
        out["h2d_" + ("pinned" if pinned else "pageable") + "_gb_per_s"] = gbps(n, statistics.median(ms))
        out["h2d_" + ("pinned" if pinned else "pageable") + "_ms_raw"] = [round(v, 3) for v in ms]
    return out


def hold(a) -> dict:
    n = 128 * MiB
    h_up, d_up = bufs(n, True)
    h_dn, d_dn = bufs(n, True)
    s_up, s_dn = torch.cuda.Stream(), torch.cuda.Stream()
    end, k = time.monotonic() + a.seconds, 0
    while time.monotonic() < end:
        with torch.cuda.stream(s_up):
            d_up.copy_(h_up, non_blocking=True)
        with torch.cuda.stream(s_dn):
            h_dn.copy_(d_dn, non_blocking=True)
        torch.cuda.synchronize()
        k += 1
    return {"seconds": a.seconds, "iterations": k, "bytes_each_way": k * n}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["sweep", "bidir", "contend", "point", "hold"])
    ap.add_argument("--seconds", type=float, default=8.0)
    a = ap.parse_args()
    torch.cuda.init()
    res = {"mode": a.mode, "gpu": torch.cuda.get_device_name(0), "torch": torch.__version__,
           **globals()[a.mode](a)}
    print(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
