#!/usr/bin/env python3
"""Generate the Chapter 15 synthetic serving trace (deterministic, seeded).

The generator is a small discrete-event simulator of four continuous-batching replicas of the
W-INFER 70B model (docs/REFERENCE_CLUSTER.md), each running tensor parallel TP=2 with FP8 weights
on two H100-class GPUs of one HX8 node (a "canary" pool; the chapter's capacity model explains why
TP=2 leaves only ~214k tokens of KV cache per replica). It models:

* Poisson arrivals from two tenants (``chat`` and ``longctx``), least-loaded routing;
* iteration-level scheduling: an iteration is either a *prefill* iteration (admits waiting
  requests up to a token budget; running sequences receive no token, so their inter-token gap
  stretches) or a *decode* iteration (every running sequence emits one token);
* a paged KV cache with 16-token blocks, admission watermark, and LIFO preemption with
  recompute when the block pool is exhausted (the policy vLLM uses by default; verify against
  the version you run);
* an HBM-bandwidth-bound decode step time and a compute-bound prefill time.

All timings are [SIMULATED]. The simulator does NOT capture: kernel-level effects, TP
all-reduce variance, CUDA graph capture, chunked prefill, prefix caching, network/HTTP
overheads, tokenizer time, or GPU clock behaviour. It exists to produce a realistic-looking,
fully reproducible trace with planted anomalies (documented only in solutions/).

Outputs (lab/data/):
  requests.csv          one row per request (all requests)
  token_gaps.csv        inter-token gaps for a 5 % sample of requests (request_id % 20 == 0)
  replica_telemetry.csv 5-second samples per replica

Usage:
  python generate_trace.py [--out DIR] [--seed 15]
"""
from __future__ import annotations

import argparse
import csv
import heapq
import math
from collections import deque
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------------------------
# Model / hardware constants (W-INFER on HX8, TP=2, FP8 weights, BF16 KV) [ILLUSTRATIVE]
# ---------------------------------------------------------------------------------------------
N_PARAMS = 70e9
WEIGHT_BYTES = 70e9                       # FP8 weights
KV_BYTES_PER_TOKEN = 327_680              # BF16 KV, 80 layers x 8 KV heads x 128 x 2 x 2 B
TP = 2
HBM_BW = 3.35e12                          # B/s per GPU
HBM_EFF = 0.60                            # achieved fraction in decode (ILLUSTRATIVE)
FP8_PEAK = 1979e12                        # dense FP8 FLOP/s per GPU
PREFILL_MFU = 0.40
STEP_OVERHEAD_S = 0.003                   # scheduler + TP all-reduce + launch (ILLUSTRATIVE)
BLOCK = 16
KV_POOL_BYTES = TP * 80e9 * 0.90 - WEIGHT_BYTES - TP * 2e9   # 70e9 B
KV_BLOCKS = int(KV_POOL_BYTES // (BLOCK * KV_BYTES_PER_TOKEN))  # 13,351 blocks
WATERMARK_BLOCKS = int(0.002 * KV_BLOCKS)
MAX_SEQS = 48
MAX_BATCHED_TOKENS = 8192
PREFILL_S_PER_TOKEN = 2 * N_PARAMS / (TP * FP8_PEAK * PREFILL_MFU)

DURATION_S = 600.0
REPLICAS = ["r0", "r1", "r2", "r3"]
SLOW_FACTOR = {"r0": 1.0, "r1": 1.0, "r2": 1.0, "r3": 1.65}   # per-replica iteration-time multiplier

BASE_RATE = 6.0                           # chat req/s, whole pool
BURST = (240.0, 285.0, 20.0)              # extra chat req/s during [start, end)
LONGCTX = (420.0, 470.0, 1.2)             # longctx tenant req/s during [start, end)
LONG_PROMPT = (8_000, 12_000)             # tokens
LONG_OUTPUT = (3_000, 5_000)              # tokens
TELEMETRY_PERIOD_S = 5.0
TOKEN_SAMPLE_MOD = 20


def blocks(tokens: int) -> int:
    return -(-tokens // BLOCK)


def poisson_times(rng: np.random.Generator, rate: float, t0: float, t1: float) -> list[float]:
    out, t = [], t0
    while True:
        t += rng.exponential(1.0 / rate)
        if t >= t1:
            return out
        out.append(t)


def make_requests(rng: np.random.Generator) -> list[dict]:
    reqs = []
    for t in poisson_times(rng, BASE_RATE, 0.0, DURATION_S):
        reqs.append({"t": t, "tenant": "chat"})
    for t in poisson_times(rng, BURST[2], BURST[0], BURST[1]):
        reqs.append({"t": t, "tenant": "chat"})
    for t in poisson_times(rng, LONGCTX[2], LONGCTX[0], LONGCTX[1]):
        reqs.append({"t": t, "tenant": "longctx"})
    reqs.sort(key=lambda r: r["t"])
    for i, r in enumerate(reqs):
        r["id"] = i
        if r["tenant"] == "chat":
            r["prompt"] = int(np.clip(rng.lognormal(math.log(1100), 0.7), 32, 6000))
            r["output"] = int(np.clip(rng.lognormal(math.log(170), 0.6), 4, 1200))
        else:
            r["prompt"] = int(rng.integers(LONG_PROMPT[0], LONG_PROMPT[1] + 1))
            r["output"] = int(rng.integers(LONG_OUTPUT[0], LONG_OUTPUT[1] + 1))
        r.update(replica=None, sched=None, first=None, finish=None, gen=0, ctx=0,
                 prefill_len=r["prompt"], preempt=0, last_tok=None, gaps=[])
    return reqs


class Replica:
    def __init__(self, name: str):
        self.name = name
        self.slow = SLOW_FACTOR[name]
        self.clock = 0.0
        self.running: list[dict] = []
        self.waiting: deque = deque()
        self.used = 0
        self.in_heap = False
        self.busy = {}          # telemetry bucket -> busy seconds
        self.samples = []       # (t, running, waiting, kv_pct)
        self.next_sample = 0.0
        self.preempt_total = 0

    def load(self) -> int:
        return len(self.running) + len(self.waiting)

    def flush(self, t: float) -> None:
        while self.next_sample <= t:
            self.samples.append((self.next_sample, len(self.running), len(self.waiting),
                                 100.0 * self.used / KV_BLOCKS, self.preempt_total))
            self.next_sample += TELEMETRY_PERIOD_S

    def add_busy(self, t0: float, dt: float) -> None:
        t, end = t0, t0 + dt
        while t < end:
            b = int(t // TELEMETRY_PERIOD_S)
            seg_end = min(end, (b + 1) * TELEMETRY_PERIOD_S)
            self.busy[b] = self.busy.get(b, 0.0) + (seg_end - t)
            t = seg_end


def emit_token(r: dict, t: float) -> None:
    if r["last_tok"] is not None and r["id"] % TOKEN_SAMPLE_MOD == 0:
        r["gaps"].append(t - r["last_tok"])
    r["last_tok"] = t
    if r["first"] is None:
        r["first"] = t


def iterate(rep: Replica) -> bool:
    """Run one scheduler iteration starting at rep.clock. Returns True if work remains."""
    t = rep.clock
    # ---- admission (prefill iteration) -------------------------------------------------
    admitted, tokens = [], 0
    while rep.waiting and len(rep.running) + len(admitted) < MAX_SEQS:
        r = rep.waiting[0]
        need = blocks(r["prefill_len"] + 1)
        if rep.used + need > KV_BLOCKS - WATERMARK_BLOCKS:
            break
        if admitted and tokens + r["prefill_len"] > MAX_BATCHED_TOKENS:
            break
        rep.waiting.popleft()
        admitted.append(r)
        rep.used += need
        tokens += r["prefill_len"]
        if r["sched"] is None:
            r["sched"] = t
    if admitted:
        dt = (STEP_OVERHEAD_S + tokens * PREFILL_S_PER_TOKEN) * rep.slow
        end = t + dt
        for r in admitted:
            r["ctx"] = r["prefill_len"] + 1
            r["gen"] += 1
            emit_token(r, end)
        rep.running.extend(admitted)
        rep.add_busy(t, dt)
        rep.clock = end
        finish_done(rep, end)
        return bool(rep.running or rep.waiting)
    if not rep.running:
        return bool(rep.waiting)
    # ---- decode iteration -------------------------------------------------------------
    while True:
        need = sum(1 for r in rep.running if r["ctx"] % BLOCK == 0)
        if rep.used + need <= KV_BLOCKS or len(rep.running) <= 1:
            break
        victim = rep.running.pop()                       # LIFO: most recently admitted
        rep.used -= blocks(victim["ctx"])
        victim["preempt"] += 1
        rep.preempt_total += 1
        victim["prefill_len"] = victim["prompt"] + victim["gen"]
        rep.waiting.appendleft(victim)
    rep.used += sum(1 for r in rep.running if r["ctx"] % BLOCK == 0)
    ctx_total = sum(r["ctx"] for r in rep.running)
    dt = (STEP_OVERHEAD_S + (WEIGHT_BYTES + ctx_total * KV_BYTES_PER_TOKEN)
          / (TP * HBM_BW * HBM_EFF)) * rep.slow
    end = t + dt
    for r in rep.running:
        r["ctx"] += 1
        r["gen"] += 1
        emit_token(r, end)
    rep.add_busy(t, dt)
    rep.clock = end
    finish_done(rep, end)
    return bool(rep.running or rep.waiting)


def finish_done(rep: Replica, t: float) -> None:
    still = []
    for r in rep.running:
        if r["gen"] >= r["output"]:
            r["finish"] = t
            rep.used -= blocks(r["ctx"])
        else:
            still.append(r)
    rep.running = still


def simulate(reqs: list[dict]) -> list[Replica]:
    reps = [Replica(n) for n in REPLICAS]
    heap: list[tuple[float, int]] = []
    ai = 0
    while ai < len(reqs) or heap:
        t_arr = reqs[ai]["t"] if ai < len(reqs) else math.inf
        t_rep = heap[0][0] if heap else math.inf
        if t_arr <= t_rep:
            r = reqs[ai]
            ai += 1
            for rp in reps:
                if not rp.in_heap:
                    rp.flush(r["t"])
            idx = min(range(len(reps)), key=lambda i: (reps[i].load(), i))
            rep = reps[idx]
            r["replica"] = rep.name
            rep.waiting.append(r)
            if not rep.in_heap:
                rep.clock = max(rep.clock, r["t"])
                heapq.heappush(heap, (rep.clock, idx))
                rep.in_heap = True
        else:
            _, idx = heapq.heappop(heap)
            rep = reps[idx]
            rep.flush(rep.clock)
            if iterate(rep):
                heapq.heappush(heap, (rep.clock, idx))
            else:
                rep.in_heap = False
    end = max(r["finish"] for r in reqs)
    for rp in reps:
        rp.flush(end)
    return reps


def write(out: Path, reqs: list[dict], reps: list[Replica]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "requests.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["request_id", "tenant", "replica", "arrival_s", "sched_s", "first_token_s",
                    "finish_s", "prompt_tokens", "output_tokens", "preemptions"])
        for r in reqs:
            w.writerow([r["id"], r["tenant"], r["replica"], f"{r['t']:.4f}", f"{r['sched']:.4f}",
                        f"{r['first']:.4f}", f"{r['finish']:.4f}", r["prompt"], r["output"],
                        r["preempt"]])
    with open(out / "token_gaps.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["request_id", "itl_ms"])
        for r in reqs:
            if r["id"] % TOKEN_SAMPLE_MOD == 0:
                w.writerow([r["id"], ";".join(f"{g * 1000:.1f}" for g in r["gaps"])])
    with open(out / "replica_telemetry.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["t_s", "replica", "num_running", "num_waiting", "kv_usage_pct",
                    "gpu_busy_pct", "preemptions_total"])
        for rp in reps:
            for (t, run, wait, kv, pre) in rp.samples:
                b = int(t // TELEMETRY_PERIOD_S) - 1      # busy fraction of the period ending at t
                busy = 100.0 * rp.busy.get(b, 0.0) / TELEMETRY_PERIOD_S if b >= 0 else 0.0
                w.writerow([f"{t:.1f}", rp.name, run, wait, f"{kv:.1f}", f"{min(busy, 100.0):.1f}",
                            pre])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parents[1] / "data")
    ap.add_argument("--seed", type=int, default=15)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    reqs = make_requests(rng)
    reps = simulate(reqs)
    write(args.out, reqs, reps)
    print(f"wrote {len(reqs)} requests to {args.out} (KV pool {KV_BLOCKS} blocks, "
          f"prefill {PREFILL_S_PER_TOKEN * 1e6:.1f} us/token)")


if __name__ == "__main__":
    main()
