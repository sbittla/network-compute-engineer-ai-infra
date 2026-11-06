#!/usr/bin/env python3
"""Step 3: what CPU placement does to throughput. Runs CPU-bound worker processes pinned with
sched_setaffinity (what `taskset -c` does) and reports work per second per worker.

    python3 cpu_bench.py --cpu 14 --seconds 3 --reps 3 > bench.json

Configurations (all workers run the same pure-Python integer loop):
  alone           one worker on CPU X
  same_cpu        two workers both pinned to CPU X (they time-share one logical CPU)
  smt_siblings    two workers on CPU X and its SMT sibling (two hardware threads of one core, as the guest sees it)
  separate_cores  two workers on CPU X and a CPU in a different core
  unpinned        two workers, no affinity (the scheduler places them)
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import statistics
import sys
import time
from pathlib import Path

CHUNK = 20_000


def worker(cpus, seconds, start, q):
    if cpus is not None:
        os.sched_setaffinity(0, cpus)
    start.wait()
    n, acc = 0, 0
    t0 = time.perf_counter()
    end = t0 + seconds
    while time.perf_counter() < end:
        for i in range(CHUNK):
            acc += i * i
        n += 1
    q.put({"pid": os.getpid(), "affinity": sorted(os.sched_getaffinity(0)),
           "chunks_per_s": n / (time.perf_counter() - t0)})


def run(placements, seconds):
    ctx = mp.get_context("fork")
    q, start = ctx.Queue(), ctx.Event()
    ps = [ctx.Process(target=worker, args=(p, seconds, start, q), name="ch03-bench") for p in placements]
    for p in ps:
        p.start()
    time.sleep(0.2)
    start.set()
    out = [q.get(timeout=seconds + 30) for _ in ps]
    for p in ps:
        p.join()
    return out


def cpu_list(text: str) -> list[int]:
    out: list[int] = []
    for part in text.strip().split(","):
        a, _, b = part.partition("-")
        out += range(int(a), int(b or a) + 1)
    return out


def topo(cpu: int, name: str) -> str:
    return Path(f"/sys/devices/system/cpu/cpu{cpu}/topology/{name}").read_text().strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cpu", type=int, required=True)
    ap.add_argument("--seconds", type=float, default=3.0)
    ap.add_argument("--reps", type=int, default=3)
    a = ap.parse_args()
    sys.argv[0] = "ch03-bench"
    x = a.cpu
    sib = [c for c in cpu_list(topo(x, "thread_siblings_list")) if c != x]
    other = next(c for c in sorted(os.sched_getaffinity(0))
                 if c != 0 and c not in sib and c != x and topo(c, "core_id") != topo(x, "core_id"))
    configs = {"alone": [{x}], "same_cpu": [{x}, {x}], "separate_cores": [{x}, {other}], "unpinned": [None, None]}
    if sib:
        configs["smt_siblings"] = [{x}, {sib[0]}]
    configs["alone_again"] = [{x}]          # drift control: the same as "alone", measured last
    result = {"cpu_x": x, "smt_sibling": sib[0] if sib else None, "other_core_cpu": other, "seconds": a.seconds,
              "reps": a.reps, "chunk_iterations": CHUNK, "configs": {}}
    for name, placement in configs.items():
        reps = [run(placement, a.seconds) for _ in range(a.reps)]
        per_worker = [statistics.median(r[i]["chunks_per_s"] for r in reps) for i in range(len(placement))]
        result["configs"][name] = {"placement": [sorted(p) if p else "any" for p in placement], "raw": reps,
                                   "median_chunks_per_s_per_worker": [round(v, 2) for v in per_worker]}
    base = result["configs"]["alone"]["median_chunks_per_s_per_worker"][0]
    for c in result["configs"].values():
        c["per_worker_vs_alone"] = [round(v / base, 3) for v in c["median_chunks_per_s_per_worker"]]
        c["total_vs_alone"] = round(sum(c["median_chunks_per_s_per_worker"]) / base, 3)
    print(json.dumps(result, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
