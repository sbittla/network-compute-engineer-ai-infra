#!/usr/bin/env python3
"""Step 2: overlap host-to-device copies with compute on CUDA streams, and prove it with GPU timestamps.

A chunked pipeline: copy chunk i to the GPU, then run compute that reads it. Three schedules:
  serial            one stream: copy 0, compute 0, copy 1, compute 1, ...
  overlap_pinned    copy stream + compute stream, two device buffers (double buffering), pinned host chunks:
                    copy i+1 runs while compute i runs; CUDA events order the dependencies
  overlap_pageable  the same schedule from pageable host chunks

Every copy and every compute records a start and an end CUDA event on its own stream. Elapsed time from a
common start event gives GPU-side timestamps for each operation, so the overlap is measured, not inferred:
overlap_ms = |union(copy intervals) ∩ union(compute intervals)|.

torch.profiler is also tried; where CUPTI GPU activity tracing is unavailable (as in WSL2) the trace has no
GPU rows, and the script records that instead of pretending.

    python overlap.py > overlap.json
"""
from __future__ import annotations

import json
import statistics

import torch

MiB = 1 << 20
CHUNK_MIB, NCHUNK = 64, 12


def intervals_union(iv):
    out = []
    for a, b in sorted(iv):
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def intersect_len(u, v):
    i = j = 0
    tot = 0.0
    while i < len(u) and j < len(v):
        lo, hi = max(u[i][0], v[j][0]), min(u[i][1], v[j][1])
        tot += max(0.0, hi - lo)
        if u[i][1] < v[j][1]:
            i += 1
        else:
            j += 1
    return tot


class Work:
    def __init__(self, k: int):
        self.k = k
        self.w = torch.randn(2048, 2048, device="cuda", dtype=torch.float16)

    def __call__(self, buf):
        acc = buf[: 2048 * 2048 * 2].view(torch.float16).view(2048, 2048).clone()   # depends on the chunk
        for _ in range(self.k):
            acc = torch.tanh(acc @ self.w)
        return acc


def ev():
    return torch.cuda.Event(enable_timing=True)


def run(schedule: str, host_chunks, work: Work):
    dev = [torch.empty(CHUNK_MIB * MiB, dtype=torch.uint8, device="cuda") for _ in range(2)]
    s_copy, s_comp = torch.cuda.Stream(), torch.cuda.Stream()
    if schedule == "serial":
        s_copy = s_comp = torch.cuda.current_stream()
    torch.cuda.synchronize()
    t0 = ev()
    t0.record()
    s_copy.wait_event(t0)
    s_comp.wait_event(t0)
    copies, comps = [], []
    copy_done = [None] * NCHUNK
    comp_done = [None] * NCHUNK
    for i in range(NCHUNK + 1):
        if i < NCHUNK:                                   # enqueue copy i (into buffer i % 2)
            with torch.cuda.stream(s_copy):
                if i >= 2:
                    s_copy.wait_event(comp_done[i - 2])  # buffer reuse: compute i-2 must be done with it
                a, b = ev(), ev()
                a.record(s_copy)
                dev[i % 2].copy_(host_chunks[i], non_blocking=True)
                b.record(s_copy)
                copies.append((a, b))
                copy_done[i] = b
        if i >= 1:                                       # enqueue compute i-1
            j = i - 1
            with torch.cuda.stream(s_comp):
                s_comp.wait_event(copy_done[j])
                a, b = ev(), ev()
                a.record(s_comp)
                work(dev[j % 2])
                b.record(s_comp)
                comps.append((a, b))
                comp_done[j] = b
    end = ev()
    end.record(s_comp)
    torch.cuda.synchronize()
    cp = [(t0.elapsed_time(a), t0.elapsed_time(b)) for a, b in copies]
    cm = [(t0.elapsed_time(a), t0.elapsed_time(b)) for a, b in comps]
    wall = t0.elapsed_time(end)
    copy_ms = sum(b - a for a, b in cp)
    comp_ms = sum(b - a for a, b in cm)
    ov = intersect_len(intervals_union(cp), intervals_union(cm))
    return {"wall_ms": round(wall, 3), "sum_copy_ms": round(copy_ms, 3), "sum_compute_ms": round(comp_ms, 3),
            "overlap_ms": round(ov, 3), "copy_hidden_fraction": round(ov / copy_ms, 3) if copy_ms else 0.0,
            "copy_intervals_ms": [[round(a, 3), round(b, 3)] for a, b in cp],
            "compute_intervals_ms": [[round(a, 3), round(b, 3)] for a, b in cm]}


def profiler_probe(host_chunks, work):
    try:
        from torch.profiler import ProfilerActivity, profile
        with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA]) as p:
            run("overlap_pinned", host_chunks, work)
        evs = p.events()
        gpu = [e for e in evs if getattr(e, "device_type", None) is not None and "CUDA" in str(e.device_type)]
        kinds = {}
        for e in p.key_averages():
            if getattr(e, "device_time_total", 0) or getattr(e, "cuda_time_total", 0):
                kinds[e.key] = round((getattr(e, "device_time_total", 0) or getattr(e, "cuda_time_total", 0)) / 1e3, 3)
        return {"ran": True, "gpu_side_events": len(gpu), "ops_with_gpu_time_ms": dict(list(kinds.items())[:12])}
    except Exception as exc:  # noqa: BLE001
        return {"ran": False, "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    torch.manual_seed(0)
    pinned = [torch.randint(0, 255, (CHUNK_MIB * MiB,), dtype=torch.uint8).pin_memory() for _ in range(NCHUNK)]
    pageable = [c.clone() for c in pinned]
    # calibrate compute so one chunk's compute takes about as long as one chunk's copy (the case where
    # overlap matters most: ideal speedup 2x)
    probe = Work(1)
    dev = torch.empty(CHUNK_MIB * MiB, dtype=torch.uint8, device="cuda")
    s, e = ev(), ev()
    for _ in range(3):
        dev.copy_(pinned[0], non_blocking=True); probe(dev)
    torch.cuda.synchronize()
    s.record(); [dev.copy_(pinned[0], non_blocking=True) for _ in range(5)]; e.record(); torch.cuda.synchronize()
    copy_ms = s.elapsed_time(e) / 5
    s.record(); [probe(dev) for _ in range(5)]; e.record(); torch.cuda.synchronize()
    one_ms = s.elapsed_time(e) / 5
    k = max(1, round(copy_ms / one_ms))
    work = Work(k)
    del dev
    res = {"gpu": torch.cuda.get_device_name(0), "torch": torch.__version__, "chunk_mib": CHUNK_MIB, "chunks": NCHUNK,
           "calibration": {"copy_ms_per_chunk": round(copy_ms, 3), "one_matmul_iter_ms": round(one_ms, 3), "k": k},
           "schedules": {}}
    for name, chunks in (("serial", pinned), ("overlap_pinned", pinned), ("overlap_pageable", pageable)):
        reps = [run(name if name == "serial" else "overlap", chunks, work) for _ in range(5)]
        best = sorted(reps, key=lambda r: r["wall_ms"])[len(reps) // 2]          # the median run, kept whole
        best["wall_ms_all_reps"] = [r["wall_ms"] for r in reps]
        res["schedules"][name] = best
    sc = res["schedules"]
    ideal = max(sc["overlap_pinned"]["sum_copy_ms"], sc["overlap_pinned"]["sum_compute_ms"])
    res["serial_over_overlap_pinned"] = round(sc["serial"]["wall_ms"] / sc["overlap_pinned"]["wall_ms"], 3)
    res["ideal_overlap_wall_ms"] = round(ideal, 3)
    res["profiler"] = profiler_probe(pinned, work)
    print(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
