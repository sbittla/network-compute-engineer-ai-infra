"""Capstone C reference: L1 CPU-proxy benchmark harness.

INSTRUCTOR EDITION. Same API as starter-kit/starter/harness.py, fully implemented.

The harness times a data-parallel training step proxy on the CPU: per-rank matrix multiply ("compute")
followed by an in-process ring all-reduce of a gradient buffer ("communication"). Its timings are
[MEASURED] on the learner's laptop and say NOTHING about GPU, NVLink, NIC or NCCL performance. The point
is the discipline: warm-up, repetitions, percentiles, manifest, deterministic numerics.
"""
from __future__ import annotations

import datetime as _dt
import os
import platform
import sys
import time
from typing import Any

import numpy as np

EVIDENCE_LABEL = "MEASURED (L1 CPU proxy on this machine; not GPU, NVLink, NIC or NCCL evidence)"


def ring_allreduce(buffers: list[np.ndarray]) -> tuple[list[np.ndarray], list[int]]:
    """Sum-all-reduce ``buffers`` (one equal-length 1-D array per rank) with the ring algorithm.

    Reduce-scatter (n−1 steps), then all-gather (n−1 steps), over n chunks from np.array_split, so
    lengths that do not divide by n work. Returns (per-rank results, bytes sent by each rank).
    Each rank sends ≈ 2(n−1)/n × buffer bytes; the total over all ranks is exactly 2(n−1) × buffer bytes.
    """
    n = len(buffers)
    if n == 0:
        raise ValueError("need at least one rank")
    length = buffers[0].size
    if any(b.size != length for b in buffers):
        raise ValueError("all ranks must contribute equal-length buffers")
    work = [b.astype(np.float64, copy=True).ravel() for b in buffers]
    if n == 1:
        return work, [0]
    bounds = np.array_split(np.arange(length), n)
    sl = [slice(int(ix[0]), int(ix[-1]) + 1) if ix.size else slice(0, 0) for ix in bounds]
    sent = [0] * n
    item = work[0].itemsize
    for step in range(n - 1):                       # reduce-scatter
        msgs = []
        for r in range(n):
            c = (r - step) % n
            msgs.append((r, c, work[r][sl[c]].copy()))
        for r, c, data in msgs:
            dst = (r + 1) % n
            work[dst][sl[c]] += data
            sent[r] += data.size * item
    for step in range(n - 1):                       # all-gather
        msgs = []
        for r in range(n):
            c = (r + 1 - step) % n
            msgs.append((r, c, work[r][sl[c]].copy()))
        for r, c, data in msgs:
            dst = (r + 1) % n
            work[dst][sl[c]] = data
            sent[r] += data.size * item
    return work, sent


def capture_manifest(seed: int) -> dict[str, Any]:
    """Environment manifest for an L1 run: python, numpy, platform, machine, processor, cpu_count,
    blas, seed, timestamp_utc, evidence_class."""
    blas = "unknown"
    try:
        cfg = np.show_config(mode="dicts")  # numpy >= 1.25
        dep = cfg.get("Build Dependencies", {}).get("blas", {})
        blas = f"{dep.get('name', 'unknown')} {dep.get('version', '')}".strip()
    except Exception:  # noqa: BLE001 - older numpy or unusual builds
        pass
    return {
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor() or "unknown",
        "cpu_count": os.cpu_count(),
        "blas": blas,
        "seed": seed,
        "timestamp_utc": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "evidence_class": EVIDENCE_LABEL,
    }


def summarize(times: list[float] | np.ndarray) -> dict[str, float]:
    """Summary statistics (seconds): n, mean, median, p95, p99, min, max, iqr (p75 − p25),
    cv (sample std / mean). Percentiles use numpy's default linear interpolation."""
    a = np.asarray(times, dtype=float)
    if a.size == 0:
        raise ValueError("no samples")
    p25, p50, p75, p95, p99 = np.percentile(a, [25, 50, 75, 95, 99])
    return {"n": int(a.size), "mean": float(a.mean()), "median": float(p50), "p95": float(p95),
            "p99": float(p99), "min": float(a.min()), "max": float(a.max()), "iqr": float(p75 - p25),
            "cv": float(a.std(ddof=1) / a.mean()) if a.size > 1 else 0.0}


def run_benchmark(n_ranks: int = 4, dim: int = 256, grad_elems: int = 1_000_000, warmup: int = 3,
                  reps: int = 10, seed: int = 0) -> dict[str, Any]:
    """Time ``warmup + reps`` proxy steps; record only the ``reps`` measured ones.

    Each step: every rank computes A_r @ B_r (dim × dim, float64) — timed as compute — then the ranks
    ring-all-reduce a gradient buffer of ``grad_elems`` float64 values — timed as comm. Inputs come from
    ``np.random.default_rng(seed)`` so the numerical result (``checksum`` = sum of rank 0's final reduced
    buffer) is identical across runs and machines.

    Returns config, manifest, times_s, compute_s, comm_s (lists of length reps), summary
    (summarize(times_s)), checksum, bytes_sent_per_rank, evidence_label.
    """
    if reps < 1 or warmup < 0:
        raise ValueError("reps must be >= 1 and warmup >= 0")
    rng = np.random.default_rng(seed)
    a = [rng.standard_normal((dim, dim)) for _ in range(n_ranks)]
    b = [rng.standard_normal((dim, dim)) for _ in range(n_ranks)]
    times, comp, comm = [], [], []
    checksum, sent = 0.0, [0] * n_ranks
    for i in range(warmup + reps):
        grads = [rng.standard_normal(grad_elems) for _ in range(n_ranks)]
        t0 = time.perf_counter()
        for r in range(n_ranks):
            _ = a[r] @ b[r]
        t1 = time.perf_counter()
        reduced, sent = ring_allreduce(grads)
        t2 = time.perf_counter()
        checksum = float(reduced[0].sum())
        if i >= warmup:
            comp.append(t1 - t0)
            comm.append(t2 - t1)
            times.append(t2 - t0)
    return {"config": {"n_ranks": n_ranks, "dim": dim, "grad_elems": grad_elems, "warmup": warmup,
                       "reps": reps, "seed": seed},
            "manifest": capture_manifest(seed), "times_s": times, "compute_s": comp, "comm_s": comm,
            "summary": summarize(times), "checksum": checksum, "bytes_sent_per_rank": sent,
            "evidence_label": EVIDENCE_LABEL}
