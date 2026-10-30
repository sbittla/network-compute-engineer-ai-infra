"""Serving simulator for Capstone H — colocated vs disaggregated prefill/decode (GIVEN; not a TODO).

What it models
--------------
* Instances are whole HX8 nodes serving W-INFER (70B, BF16, TP = 8). Physics is roofline-style:
  prefill time = (2·N·T + 2·L·d·T²) / (GPUs · peak · MFU)            (compute-bound)
  decode step  = (weights + Σ context · KV bytes/token) / (GPUs · HBM · eff) + fixed overhead
                                                                     (memory-bound)
* **Colocated**: every instance runs both phases. Without chunking (``chunk_tokens=None``) a whole
  prompt's prefill runs as its own iteration before the next decode step, so long prefills stretch
  the inter-token latency of every running request on that instance. With chunking, each iteration
  FUSES one prefill chunk with the decode step for the running batch and costs
  max(chunk compute, decode memory time) + per-step overhead (chunked prefill / Sarathi-style).
* **Disaggregated**: a FCFS prefill pool produces the first token, then the KV cache crosses the
  network (exposed time = max(transfer − overlap with prefill, transfer / layers) + per-transfer
  overhead) into the least-loaded decode instance with free KV capacity; decode instances run
  continuous batching.
* Optional admission control (both modes): a callable ``admission(req, state) -> "admit" | "reject"``;
  ``state["prefill_backlog_s"]`` is the estimated queued prefill seconds ahead of the request.

What it does NOT capture (state this in every report)
------------------------------------------------------
Real kernel efficiency curves, attention-kernel and paged-KV details, TP communication beyond a
fixed per-step overhead, network congestion and incast between pools (every KV transfer gets the
full link: link *utilisation* and decode-side fan-in must come from the capacity model), NIC/PCIe contention with
other traffic, CPU/tokenizer/scheduler overheads, preemption/swapping, prefix caching,
speculative decoding, failures, and anything about real hardware. All outputs are ``[SIMULATED]``.
"""
from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, field
from typing import Any, Callable

MODEL = {"params": 70e9, "layers": 80, "d_model": 8192, "kv_heads": 8, "head_dim": 128,
         "bytes_per_elem": 2, "weights_GB": 140.0}
KV_BYTES_PER_TOKEN = 2 * MODEL["layers"] * MODEL["kv_heads"] * MODEL["head_dim"] * MODEL["bytes_per_elem"]

DEFAULTS: dict[str, Any] = {
    "gpus_per_instance": 8,
    "peak_TFLOPs": 989.0,      # per GPU, dense BF16 [VENDOR-SPEC, 2026-10] class value
    "hbm_TBps": 3.35,          # per GPU [VENDOR-SPEC, 2026-10] class value
    "hbm_GB": 80.0,            # per GPU
    "mfu_prefill": 0.5,        # [ILLUSTRATIVE]
    "hbm_eff": 0.7,            # [ILLUSTRATIVE]
    "step_overhead_s": 0.004,  # TP all-reduce + launch overhead per decode step [ILLUSTRATIVE]
    "reserve_frac": 0.10,      # HBM held back for activations / fragmentation [ILLUSTRATIVE]
}


def prefill_s(tokens: int, hw: dict[str, Any]) -> float:
    flops = 2 * MODEL["params"] * tokens + 2 * MODEL["layers"] * MODEL["d_model"] * tokens ** 2
    return flops / (hw["gpus_per_instance"] * hw["peak_TFLOPs"] * 1e12 * hw["mfu_prefill"])


def decode_step_s(batch: int, ctx_tokens_total: float, hw: dict[str, Any]) -> float:
    if batch == 0:
        return 0.0
    byts = MODEL["weights_GB"] * 1e9 + ctx_tokens_total * KV_BYTES_PER_TOKEN
    return byts / (hw["gpus_per_instance"] * hw["hbm_TBps"] * 1e12 * hw["hbm_eff"]) + hw["step_overhead_s"]


def kv_capacity_tokens(hw: dict[str, Any]) -> int:
    free = hw["gpus_per_instance"] * hw["hbm_GB"] * (1 - hw["reserve_frac"]) - MODEL["weights_GB"]
    return int(free * 1e9 // KV_BYTES_PER_TOKEN)


def exposed_transfer_s(tokens: int, link_GBps: float, overhead_s: float, prefill_time: float,
                       pipelined: bool = True) -> float:
    xfer = tokens * KV_BYTES_PER_TOKEN / (link_GBps * 1e9)
    if not pipelined:
        return overhead_s + xfer
    overlap = prefill_time * (MODEL["layers"] - 1) / MODEL["layers"]
    return overhead_s + max(xfer - overlap, xfer / MODEL["layers"])


@dataclass
class Result:
    requests: list[dict]
    util: dict[str, float]
    config: dict
    extra: dict = field(default_factory=dict)


class _Decoder:
    """A continuous-batching decode engine on one instance (finish times tracked by step index)."""

    def __init__(self, hw: dict[str, Any]) -> None:
        self.hw = hw
        self.cap = kv_capacity_tokens(hw)
        self.step = 0
        self.heap: list = []              # (finish_step, rid)
        self.ctx_total = 0.0
        self.final_ctx: dict[int, int] = {}
        self.busy_s = 0.0
        self.new: list[int] = []          # added since the last step: their next token is their first from decode

    @property
    def batch(self) -> int:
        return len(self.heap)

    def kv_used(self) -> float:
        return self.ctx_total

    def add(self, rid: int, prompt: int, remaining: int) -> None:
        heapq.heappush(self.heap, (self.step + remaining, rid))
        self.ctx_total += prompt
        self.final_ctx[rid] = prompt + remaining
        self.new.append(rid)

    def run_step(self) -> tuple[float, list[int], list[int], int]:
        """One decode step: returns (dt, finished rids, rids that got their first decode token, batch)."""
        batch = self.batch
        firsts, self.new = self.new, []
        dt = decode_step_s(self.batch, self.ctx_total, self.hw)
        self.step += 1
        self.ctx_total += self.batch
        done = []
        while self.heap and self.heap[0][0] <= self.step:
            _, rid = heapq.heappop(self.heap)
            self.ctx_total -= self.final_ctx.pop(rid)
            done.append(rid)
        return dt, done, firsts, batch


def _pct(xs: list[float], q: float) -> float:
    if not xs:
        return float("nan")
    s = sorted(xs)
    k = max(0, min(len(s) - 1, math.ceil(q / 100 * len(s)) - 1))
    return s[k]


def _wpct(pairs: list[tuple[float, int]], q: float) -> float:
    """Weighted percentile of (value, weight) pairs."""
    pairs = [p for p in pairs if p[1] > 0]
    if not pairs:
        return float("nan")
    pairs.sort()
    total = sum(w for _, w in pairs)
    acc = 0
    for v, w in pairs:
        acc += w
        if acc >= q / 100 * total:
            return v
    return pairs[-1][0]


def summarize(res: Result, short_max_tokens: int = 4096) -> dict[str, float]:
    """TTFT p50/p95 (short and long prompts), TPOT p50/p95 (per-request mean), ITL p50/p95/p99
    (per-token gap distribution, including second-token gaps), throughput, rejection rate."""
    ok = [r for r in res.requests if r["status"] == "done"]
    short = [r["ttft_s"] for r in ok if r["prompt"] <= short_max_tokens]
    long_ = [r["ttft_s"] for r in ok if r["prompt"] > short_max_tokens]
    tpot = [r["tpot_s"] for r in ok if r["output"] > 1]
    dur = max((r["end_s"] for r in ok), default=0.0) - min((r["arrival_s"] for r in res.requests), default=0.0)
    return {"ttft_p50_s": _pct(short, 50), "ttft_p95_s": _pct(short, 95), "ttft_long_p95_s": _pct(long_, 95),
            "tpot_p50_s": _pct(tpot, 50), "tpot_p95_s": _pct(tpot, 95),
            "itl_p50_s": _wpct(list(res.extra.get("itl", [])), 50),
            "itl_p95_s": _wpct(list(res.extra.get("itl", [])), 95),
            "itl_p99_s": _wpct(list(res.extra.get("itl", [])), 99),
            "second_gap_p95_s": _pct(res.extra.get("second_token_gaps", []), 95),
            "second_gap_max_s": max(res.extra.get("second_token_gaps", []), default=float("nan")),
            "output_tok_per_s": sum(r["output"] for r in ok) / dur if dur > 0 else 0.0,
            "reject_rate": sum(1 for r in res.requests if r["status"] == "rejected") / max(1, len(res.requests)),
            "completed": len(ok)}


def run(trace: list[dict], arch: dict[str, Any], admission: Callable | None = None) -> Result:
    """Simulate ``trace`` (list of {rid, arrival_s, prompt, output}) on architecture ``arch``.

    arch: {"kind": "colocated", "instances": N, "chunk_tokens": int|None, "hw": {...}} or
          {"kind": "disaggregated", "prefill": P, "decode": D, "hw_prefill": {...}, "hw_decode": {...},
           "link_GBps": float, "link_overhead_s": float, "layer_pipelined": bool (default True),
           "util_window_s": optional float (adds util["prefill_window"])}
    Deterministic. Returns per-request records and per-pool busy fractions.
    """
    if arch["kind"] == "colocated":
        return _run_colocated(trace, arch, admission)
    return _run_disagg(trace, arch, admission)


def _run_colocated(trace: list[dict], arch: dict[str, Any], admission: Callable | None = None) -> Result:
    hw = {**DEFAULTS, **arch.get("hw", {})}
    n, chunk = arch["instances"], arch.get("chunk_tokens")
    reqs = {r["rid"]: {**r, "status": "pending", "ttft_s": None, "tpot_s": None, "end_s": None} for r in trace}
    order = sorted(trace, key=lambda r: (r["arrival_s"], r["rid"]))
    # Join-shortest-queue dispatch on estimated prefill backlog at arrival time.
    est_free = [0.0] * n
    assigned: list[list[dict]] = [[] for _ in range(n)]
    for r in order:
        j = min(range(n), key=lambda x: (max(est_free[x], r["arrival_s"]), x))
        state = {"now": r["arrival_s"], "prefill_backlog_s": max(0.0, est_free[j] - r["arrival_s"]),
                 "prefill_instances": n}
        if admission is not None and admission(r, state) == "reject":
            reqs[r["rid"]]["status"] = "rejected"
            continue
        est_free[j] = max(est_free[j], r["arrival_s"]) + prefill_s(r["prompt"], hw)
        assigned[j].append(r)
    busy, horizon = 0.0, 0.0
    itl: list[tuple[float, int]] = []
    for arrivals in assigned:
        dec, t, i, q, pf_left = _Decoder(hw), 0.0, 0, [], 0
        first: dict[int, float] = {}
        while i < len(arrivals) or q or dec.batch:
            while i < len(arrivals) and arrivals[i]["arrival_s"] <= t:
                q.append(arrivals[i]["rid"])
                i += 1
            if not q and not dec.batch:
                t = arrivals[i]["arrival_s"]
                continue
            dt, fin = 0.0, None
            if q:
                rid = q[0]
                if pf_left == 0:
                    pf_left = reqs[rid]["prompt"]
                take = pf_left if chunk is None else min(chunk, pf_left)
                done_before = reqs[rid]["prompt"] - pf_left
                dt += prefill_s(done_before + take, hw) - prefill_s(done_before, hw)
                pf_left -= take
                if pf_left == 0:
                    fin = q.pop(0)
            sdt, done, _, bsz = dec.run_step() if dec.batch else (0.0, [], [], 0)
            if chunk is not None and dt > 0 and sdt > 0:
                # fused iteration: compute-bound chunk overlaps the memory-bound decode step
                it = max(dt, sdt - hw["step_overhead_s"]) + hw["step_overhead_s"]
            else:
                it = dt + sdt
            t += it
            busy += it
            if bsz:
                itl.append((it, bsz))   # every running sequence waited this whole iteration for its token
            for rid in done:
                r = reqs[rid]
                r["end_s"], r["status"] = t, "done"
                r["tpot_s"] = (t - first[rid]) / max(1, r["output"] - 1)
            if fin is not None:
                r = reqs[fin]
                first[fin] = t
                r["ttft_s"] = t - r["arrival_s"]
                if r["output"] <= 1:
                    r["end_s"], r["status"], r["tpot_s"] = t, "done", 0.0
                else:
                    dec.add(fin, r["prompt"], r["output"] - 1)
        horizon = max(horizon, t)
    util = {"colocated": busy / (n * horizon) if horizon else 0.0}
    return Result(list(reqs.values()), util, arch, {"itl": itl})


def _run_disagg(trace: list[dict], arch: dict[str, Any], admission: Callable | None) -> Result:
    hwp = {**DEFAULTS, **arch.get("hw_prefill", {})}
    hwd = {**DEFAULTS, **arch.get("hw_decode", {})}
    P, D = arch["prefill"], arch["decode"]
    link, ovh = arch["link_GBps"], arch.get("link_overhead_s", 0.0)
    reqs = {r["rid"]: {**r, "status": "pending", "ttft_s": None, "tpot_s": None, "end_s": None,
                       "kv_exposed_s": None} for r in trace}
    order = sorted(trace, key=lambda r: (r["arrival_s"], r["rid"]))
    pf_free = [0.0] * P
    pf_busy = 0.0
    pf_intervals: list[tuple[float, float]] = []
    ready: list = []        # (ready_time, rid) KV arrived at decode side
    for r in order:
        state = {"now": r["arrival_s"], "prefill_backlog_s": sum(max(0.0, f - r["arrival_s"]) for f in pf_free) / P,
                 "prefill_instances": P}
        if admission is not None and admission(r, state) == "reject":
            reqs[r["rid"]]["status"] = "rejected"
            continue
        k = min(range(P), key=lambda j: (pf_free[j], j))
        start = max(pf_free[k], r["arrival_s"])
        t_pf = prefill_s(r["prompt"], hwp)
        pf_free[k] = start + t_pf
        pf_busy += t_pf
        pf_intervals.append((start, start + t_pf))
        rr = reqs[r["rid"]]
        rr["ttft_s"] = pf_free[k] - r["arrival_s"]
        x = exposed_transfer_s(r["prompt"], link, ovh, t_pf, arch.get("layer_pipelined", True))
        rr["kv_exposed_s"] = x
        rr["first_token_s"] = pf_free[k]
        if r["output"] <= 1:
            rr["status"], rr["end_s"], rr["tpot_s"] = "done", pf_free[k], 0.0
        else:
            heapq.heappush(ready, (pf_free[k] + x, r["rid"]))
    decs = [_Decoder(hwd) for _ in range(D)]
    t_dec = [0.0] * D
    itl: list[tuple[float, int]] = []
    second: list[float] = []
    waiting: list = []

    def place(now: float) -> None:
        nonlocal waiting
        still = []
        for (t, rid) in waiting:
            r = reqs[rid]
            need = r["prompt"] + r["output"]
            cands = [j for j in range(D) if decs[j].kv_used() + need <= decs[j].cap]
            if not cands:
                still.append((t, rid))
                continue
            j = min(cands, key=lambda x: (decs[x].batch, x))
            if not decs[j].batch:
                t_dec[j] = max(t_dec[j], now)
            decs[j].add(rid, r["prompt"], r["output"] - 1)
        waiting = still

    while ready or waiting or any(d.batch for d in decs):
        k = min(range(D), key=lambda j: (t_dec[j] if decs[j].batch else math.inf, j))
        t_next = t_dec[k] if decs[k].batch else math.inf
        if ready and ready[0][0] <= t_next:
            t, rid = heapq.heappop(ready)
            waiting.append((t, rid))
            place(t)
            continue
        if t_next == math.inf:
            raise RuntimeError("request larger than decode KV capacity")
        dt, done, firsts, bsz = decs[k].run_step()
        t_dec[k] += dt
        itl.append((dt, bsz - len(firsts)))
        for rid in firsts:   # second-token gap: exposed KV transfer + wait for a decode slot + this step
            gap = t_dec[k] - reqs[rid]["first_token_s"]
            itl.append((gap, 1))
            second.append(gap)
        decs[k].busy_s += dt
        for rid in done:
            r = reqs[rid]
            r["end_s"], r["status"] = t_dec[k], "done"
            r["tpot_s"] = (t_dec[k] - r["first_token_s"]) / (r["output"] - 1)
        if waiting:
            place(t_dec[k])
    horizon = max((r["end_s"] or 0.0) for r in reqs.values()) or 1.0
    util = {"prefill": pf_busy / (P * horizon), "decode": sum(d.busy_s for d in decs) / (D * horizon)}
    w = arch.get("util_window_s")
    if w:  # prefill busy fraction inside [0, w] only, for like-for-like comparison with a model
        util["prefill_window"] = sum(max(0.0, min(e, w) - s) for s, e in pf_intervals) / (P * w)
    return Result(list(reqs.values()), util, arch, {"itl": itl, "second_token_gaps": second})
