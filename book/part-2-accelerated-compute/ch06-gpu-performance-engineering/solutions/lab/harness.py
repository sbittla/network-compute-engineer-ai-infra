#!/usr/bin/env python3
"""Chapter 6 lab — reference solution: a small, reproducible benchmark harness.

Runs CPU microbenchmarks (numpy matmul → GFLOP/s, memory copy → GB/s) with an explicit warm-up policy,
fixed repetitions, per-sample timing, and an environment manifest, and writes everything to JSON. The
same structure (warm-up, repetitions, manifest, raw samples, summary) is what an L2 GPU benchmark needs;
only the timed function and the manifest fields change.

Results on a laptop are [MEASURED] for that laptop only — never for ORION hardware.

CLI:
    python harness.py --quick --out results.json
    python harness.py --runs 5 --out results.json        # 5 runs, each in a fresh process (unit of replication)
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import platform
import socket
import subprocess
import tempfile
import sys
import time
from pathlib import Path
from typing import Callable

import numpy as np

THREAD_ENV = ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS")
MANIFEST_KEYS = ("timestamp_utc", "hostname", "platform", "machine", "python", "numpy", "cpu_count",
                 "thread_env", "blas", "harness_version", "seed", "pid")
HARNESS_VERSION = "1.0"


def environment_manifest(seed: int = 0) -> dict:
    """Record what can change a result: time, host, OS, CPU architecture, Python and numpy versions,
    logical CPU count, threading environment variables, BLAS configuration (best effort), harness
    version, seed and the process id (pid) — so that independent runs can be shown to be separate
    processes. Every key in MANIFEST_KEYS must be present (use None when unknown)."""
    try:
        cfg = np.show_config(mode="dicts")  # numpy >= 1.26
        blas = cfg.get("Build Dependencies", {}).get("blas", {}) if isinstance(cfg, dict) else None
    except Exception:  # noqa: BLE001 — older numpy prints instead of returning
        blas = None
    return {"timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "hostname": socket.gethostname(), "platform": platform.platform(), "machine": platform.machine(),
            "python": platform.python_version(), "numpy": np.__version__, "cpu_count": os.cpu_count(),
            "thread_env": {k: os.environ.get(k) for k in THREAD_ENV}, "blas": blas,
            "harness_version": HARNESS_VERSION, "seed": seed, "pid": os.getpid()}


def time_samples(fn: Callable[[], object], warmup: int, reps: int,
                 timer: Callable[[], int] = time.perf_counter_ns) -> dict:
    """Call fn `warmup` times (timed but reported separately), then `reps` times. Each call is timed
    individually with `timer` (integer ns). Returns {"warmup_ns": [...], "samples_ns": [...]}.
    For GPU work fn must include its own synchronization or use device events (Chapter 4)."""
    if reps < 1 or warmup < 0:
        raise ValueError("reps must be >= 1 and warmup >= 0")
    warm, samples = [], []
    for i in range(warmup + reps):
        t0 = timer()
        fn()
        t1 = timer()
        (warm if i < warmup else samples).append(int(t1 - t0))
    return {"warmup_ns": warm, "samples_ns": samples}


def summarize_ns(samples_ns: list[int], work: float, unit: str) -> dict:
    """Summary of one benchmark's samples. `work` is the amount of work per call in base units (FLOP
    for "GFLOP/s", bytes for "GB/s"); rate = work / time / 1e9. Returns n, median_ms, p95_ms, iqr_ms,
    min_ms, max_ms, and rate_median (rate at the median time) with its unit."""
    a = np.sort(np.asarray(samples_ns, dtype=float)) / 1e6  # ms
    q = lambda p: float(np.quantile(a, p))  # noqa: E731 — numpy 'linear' method
    med = q(0.5)
    return {"n": int(a.size), "median_ms": med, "p95_ms": q(0.95), "iqr_ms": q(0.75) - q(0.25),
            "min_ms": float(a[0]), "max_ms": float(a[-1]), "rate_median": work / (med / 1e3) / 1e9, "unit": unit}


def matmul_bench(n: int, seed: int = 0) -> tuple[Callable[[], object], float]:
    """Return (fn, flop_per_call) for an n×n float32 matmul: 2·n³ FLOP per call. Inputs are created once
    from a seeded generator so every run computes on identical data."""
    rng = np.random.default_rng(seed)
    a = rng.standard_normal((n, n), dtype=np.float32)
    b = rng.standard_normal((n, n), dtype=np.float32)
    return (lambda: a @ b), 2.0 * n ** 3


def copy_bench(nbytes: int) -> tuple[Callable[[], object], float]:
    """Return (fn, bytes_moved_per_call) for copying an nbytes buffer into a preallocated destination:
    each byte is read once and written once → 2·nbytes moved."""
    src = np.ones(nbytes // 8, dtype=np.float64)
    dst = np.empty_like(src)
    return (lambda: np.copyto(dst, src)), 2.0 * src.nbytes


def run_suite(quick: bool = True, warmup: int = 3, reps: int = 10, seed: int = 0) -> dict:
    """Run the microbenchmark suite once. Returns {"manifest": ..., "config": ..., "results": [...]}
    where each result has bench, size, warmup_ns, samples_ns and the summarize_ns() fields."""
    sizes_mm = [128, 256] if quick else [256, 512, 1024, 2048]
    sizes_cp = [1 << 20, 16 << 20] if quick else [1 << 20, 16 << 20, 256 << 20]
    results = []
    for n in sizes_mm:
        fn, work = matmul_bench(n, seed)
        s = time_samples(fn, warmup, reps)
        results.append({"bench": "matmul_f32", "size": n, **s, **summarize_ns(s["samples_ns"], work, "GFLOP/s")})
    for nb in sizes_cp:
        fn, work = copy_bench(nb)
        s = time_samples(fn, warmup, reps)
        results.append({"bench": "memcpy", "size": nb, **s, **summarize_ns(s["samples_ns"], work, "GB/s")})
    return {"manifest": environment_manifest(seed),
            "config": {"quick": quick, "warmup": warmup, "reps": reps, "matmul_sizes": sizes_mm,
                       "copy_sizes_bytes": sizes_cp, "timer": "time.perf_counter_ns"},
            "results": results}


def run_independent(n_runs: int, quick: bool = True, warmup: int = 3, reps: int = 10, seed: int = 0) -> list[dict]:
    """Run the suite n_runs times, each in a FRESH Python process (the unit of replication, Table 6.5):
    re-execute this file with `--single-run --out <tmpfile>` via subprocess.run([sys.executable, __file__, ...]),
    read each run's JSON back, and return the list of run dicts (each carries its own manifest with a
    distinct pid). Raise RuntimeError if a child process fails."""
    runs = []
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(n_runs):
            out = Path(tmp) / f"run{i}.json"
            cmd = [sys.executable, str(Path(__file__).resolve()), "--single-run", "--out", str(out),
                   "--warmup", str(warmup), "--reps", str(reps), "--seed", str(seed)] + (["--quick"] if quick else [])
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode != 0:
                raise RuntimeError(f"run {i} failed: {proc.stderr.strip()[-500:]}")
            runs.append(json.loads(out.read_text(encoding="utf-8")))
    return runs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quick", action="store_true", help="small sizes (seconds)")
    ap.add_argument("--warmup", type=int, default=3)
    ap.add_argument("--reps", type=int, default=10)
    ap.add_argument("--runs", type=int, default=1, help="independent runs, each in a fresh process")
    ap.add_argument("--single-run", action="store_true", help=argparse.SUPPRESS)  # used by run_independent
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", type=Path, default=Path("results.json"))
    args = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if args.single_run:
        args.out.write_text(json.dumps(run_suite(args.quick, args.warmup, args.reps, args.seed)), encoding="utf-8")
        return 0
    runs = run_independent(args.runs, args.quick, args.warmup, args.reps, args.seed)
    args.out.write_text(json.dumps({"runs": runs}, indent=1), encoding="utf-8")
    for i, r in enumerate(runs):
        for x in r["results"]:
            print(f"run {i} pid {r['manifest']['pid']} {x['bench']:10} size={x['size']:>10}  median {x['median_ms']:8.3f} ms  "
                  f"IQR {x['iqr_ms']:.3f} ms  {x['rate_median']:8.1f} {x['unit']}  [MEASURED on this host]")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
