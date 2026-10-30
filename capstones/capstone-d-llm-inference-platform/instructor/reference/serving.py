"""Capstone D reference: W-INFER capacity model, request-level serving simulator, SLOs and cost.

INSTRUCTOR EDITION. Same API as starter-kit/starter/serving.py, fully implemented.

The simulator is [SIMULATED]: an iteration-level model of continuous batching on ONE replica with a
roofline iteration cost (max of compute time and HBM traffic time, plus a fixed overhead). It does NOT
capture kernel-level effects, TP all-reduce variance, CPU scheduler overhead, tokenizer/detokenizer
cost, network or load-balancer latency (budgeted separately as frontend_budget_s), prefix caching,
speculative decoding, or GPU clock behaviour.
"""
from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml


def load_inputs(data_dir: str | Path) -> dict[str, Any]:
    """Load the traces and YAML inputs. Keys: traces (list of DataFrames, seeds 1..5), trace (= traces[0]),
    model, hardware, configs, slo, economics."""
    d = Path(data_dir)
    y = lambda n: yaml.safe_load((d / n).read_text(encoding="utf-8"))  # noqa: E731
    traces = [pd.read_csv(p) for p in sorted(d.glob("trace_s*.csv"))]
    return {"traces": traces, "trace": traces[0], "model": y("model.yaml"), "hardware": y("hardware.yaml"),
            "configs": y("configs.yaml")["configs"], "slo": y("slo.yaml"), "economics": y("economics.yaml")}


# ----------------------------------------------------------------------------------------------
# 1. Capacity model [MODELED]
# ----------------------------------------------------------------------------------------------


def kv_bytes_per_token(model: dict) -> int:
    """K and V for every layer: 2 × layers × kv_heads × head_dim × kv_dtype_bytes (bytes per token)."""
    return int(2 * model["layers"] * model["kv_heads"] * model["head_dim"] * model["kv_dtype_bytes"])


def capacity(model: dict, hw: dict, cfg: dict) -> dict[str, float]:
    """Per-replica memory plan. Returns weights_bytes, weights_bytes_per_gpu, usable_hbm_bytes,
    reserve_bytes, kv_budget_bytes, kv_tokens (int), max_seqs_at_4k (int, 4,096-token contexts).

    usable = tp × hbm × gpu_memory_utilization; kv_budget = usable − weights − tp × runtime reserve.
    """
    tp = cfg["tp"]
    w = model["params"] * model["weight_bytes_per_param"][cfg["dtype"]]
    usable = tp * hw["hbm_bytes_per_gpu"] * cfg["gpu_memory_utilization"]
    reserve = tp * hw["runtime_reserve_bytes_per_gpu"]
    kv = usable - w - reserve
    if kv <= 0:
        raise ValueError("weights do not fit")
    tokens = int(kv // kv_bytes_per_token(model))
    return {"weights_bytes": w, "weights_bytes_per_gpu": w / tp, "usable_hbm_bytes": usable,
            "reserve_bytes": reserve, "kv_budget_bytes": kv, "kv_tokens": tokens, "max_seqs_at_4k": tokens // 4096}


def attention_flops(model: dict, prefix: int, chunk: int) -> float:
    """Causal self-attention FLOPs to prefill tokens [prefix, prefix + chunk) of one sequence.

    QKᵀ and AV are 2 FLOP per multiply-accumulate each, over a causal (half) mask: total for an n-token
    prompt ≈ 2 × layers × hidden × n². For a chunk: 2 × L × d × ((prefix + chunk)² − prefix²), which sums
    exactly to the full-prompt value over chunks. Adds ≈ 30 % to a 32k prompt's linear 2·N·n FLOPs.
    """
    return 2.0 * model["layers"] * model["hidden"] * ((prefix + chunk) ** 2 - prefix ** 2)


def iteration_time_s(prefill_tokens: int, decode_seqs: int, kv_tokens_read: int, model: dict, hw: dict,
                     cfg: dict, attn_flops: float = 0.0) -> float:
    """Roofline cost of one engine iteration (seconds).

    compute = (2 × params × (prefill_tokens + decode_seqs) + attn_flops) / (tp × peak[dtype] × prefill_mfu)
    memory  = (weights bytes + kv_tokens_read × kv_bytes_per_token) / (tp × hbm_bw × hbm_bw_efficiency)
    time    = iteration_overhead[tp] + max(compute, memory)
    Decode attention FLOPs are omitted (decode is memory-bound; its KV reads are in the memory term).
    """
    tp = cfg["tp"]
    flops = 2 * model["params"] * (prefill_tokens + decode_seqs) + attn_flops
    comp = flops / (tp * hw["peak_flops"][cfg["dtype"]] * hw["prefill_mfu"])
    w = model["params"] * model["weight_bytes_per_param"][cfg["dtype"]]
    mem = (w + kv_tokens_read * kv_bytes_per_token(model)) / (tp * hw["hbm_bw_bytes_per_s"] * hw["hbm_bw_efficiency"])
    return hw["iteration_overhead_s"][str(tp)] + max(comp, mem)


# ----------------------------------------------------------------------------------------------
# 2. Discrete-event serving simulator [SIMULATED]
# ----------------------------------------------------------------------------------------------


def simulate(trace: pd.DataFrame, model: dict, hw: dict, cfg: dict, rate_scale: float = 1.0) -> pd.DataFrame:
    """Simulate continuous batching on one replica. Returns one row per request:
    request_id, tenant, prompt_tokens, output_tokens, arrival_s, status ('ok' | 'rejected'),
    first_token_s, finish_s, ttft_s, tpot_s, e2e_s, preemptions.
    ``res.attrs['itl_s']`` holds every inter-token gap (seconds) and ``res.attrs['itl_arrival_s']`` the
    arrival time of the request each gap belongs to (for warm-up/cool-down filtering).

    Scheduling per iteration (vLLM-like, simplified):
      1. Requests with prompt + output > max_model_len, or > the replica's KV capacity, are rejected on
         arrival (the second rule prevents a request that can never fit from waiting forever).
      2. Every running request that has finished prefill decodes 1 token (budget 1 token each).
      3. Running requests with unfinished prefill continue (chunk ≤ remaining budget if
         chunked_prefill; else the whole remaining prompt must fit in the budget).
      4. Waiting requests are admitted FIFO while running < max_num_seqs and the KV cache has room
         for their prompt; same chunking rule.
      5. If decode growth would exceed KV capacity, the most recently admitted request is preempted
         (KV freed, progress lost, back to the front of the queue).
    Iteration cost includes causal attention FLOPs for every prefill chunk. The iteration that completes a
    prompt's prefill emits its first token. ``rate_scale`` divides inter-arrival times.
    """
    cap = capacity(model, hw, cfg)["kv_tokens"]
    budget_full = int(cfg["max_num_batched_tokens"])
    chunked = bool(cfg["chunked_prefill"])
    arr = trace["arrival_s"].to_numpy() / rate_scale
    P = trace["prompt_tokens"].to_numpy()
    O = trace["output_tokens"].to_numpy()
    n = len(trace)
    status = np.array(["pending"] * n, dtype=object)
    first = np.full(n, np.nan)
    fin = np.full(n, np.nan)
    last_tok = np.full(n, np.nan)
    pre = np.zeros(n, dtype=int)
    prefilled = np.zeros(n, dtype=int)
    generated = np.zeros(n, dtype=int)
    itl: list[float] = []
    itl_arr: list[float] = []
    waiting: deque[int] = deque()
    running: list[int] = []
    t, nxt = 0.0, 0
    while nxt < n or waiting or running:
        while nxt < n and arr[nxt] <= t:
            if P[nxt] + O[nxt] > cfg["max_model_len"] or P[nxt] + O[nxt] > cap:
                status[nxt] = "rejected"
            else:
                waiting.append(nxt)
            nxt += 1
        if not waiting and not running:
            t = arr[nxt]
            continue
        budget = budget_full
        decoders = [r for r in running if prefilled[r] >= P[r]][:budget]
        budget -= len(decoders)
        kv_used = int(sum(prefilled[r] + generated[r] for r in running))
        while decoders and kv_used + len(decoders) > cap:          # preempt newest
            victim = running.pop()
            kv_used -= prefilled[victim] + generated[victim]
            prefilled[victim] = generated[victim] = 0
            pre[victim] += 1
            if victim in decoders:
                decoders.remove(victim)
                budget += 1
            waiting.appendleft(victim)
        chunks: dict[int, int] = {}
        for r in running:
            if prefilled[r] < P[r] and budget > 0:
                rem = int(P[r] - prefilled[r])
                c = min(rem, budget) if chunked else (rem if rem <= budget else 0)
                if c:
                    chunks[r] = c
                    budget -= c
        while waiting and budget > 0 and len(running) < cfg["max_num_seqs"]:
            r = waiting[0]
            if kv_used + P[r] > cap:
                break
            c = min(int(P[r]), budget) if chunked else (int(P[r]) if P[r] <= budget else 0)
            if c == 0:
                break
            waiting.popleft()
            running.append(r)
            kv_used += int(P[r])                                     # reserve the whole prompt
            chunks[r] = c
            budget -= c
        if not decoders and not chunks:                              # nothing schedulable: wait for arrival
            t = arr[nxt] if nxt < n else t + 1e-3
            continue
        kv_read = int(sum(prefilled[r] + generated[r] for r in running))
        attn = sum(attention_flops(model, int(prefilled[r]), c) for r, c in chunks.items())
        dt = iteration_time_s(sum(chunks.values()), len(decoders), kv_read, model, hw, cfg, attn)
        t += dt
        for r, c in chunks.items():
            prefilled[r] += c
            if prefilled[r] >= P[r]:
                generated[r] = 1
                first[r] = last_tok[r] = t
        for r in decoders:
            generated[r] += 1
            itl.append(t - last_tok[r])
            itl_arr.append(arr[r])
            last_tok[r] = t
        done = [r for r in running if prefilled[r] >= P[r] and generated[r] >= O[r]]
        for r in done:
            fin[r] = t
            status[r] = "ok"
            running.remove(r)
    ttft = first - arr
    e2e = fin - arr
    tpot = np.where(O > 1, (fin - first) / np.maximum(O - 1, 1), np.nan)
    res = pd.DataFrame({"request_id": trace["request_id"], "tenant": trace["tenant"], "prompt_tokens": P,
                        "output_tokens": O, "arrival_s": arr, "status": status, "first_token_s": first,
                        "finish_s": fin, "ttft_s": ttft, "tpot_s": tpot, "e2e_s": e2e, "preemptions": pre})
    res.attrs["itl_s"] = np.asarray(itl)
    res.attrs["itl_arrival_s"] = np.asarray(itl_arr)
    return res


def summarize(res: pd.DataFrame, slo: dict) -> dict[str, float]:
    """SLI summary over the steady-state window: requests arriving in
    [first arrival + warmup_exclude_s, last arrival − cooldown_exclude_s].

    Returns ttft_p50/p95/p99_s (OK reference-length prompts, engine-side), tpot_p50/p95/p99_s (per-request
    mean), itl_p95_s and itl_p99_s (per-token gaps), e2e_p95_s, output/input_tokens_per_s (completed tokens
    of window requests / window length), rejected, error_rate, preemptions, goodput_frac, ttft_trend
    (s of extra TTFT per s of arrival time, linear fit), stable (ttft_trend < 0.005), ttft_target_s
    (= ttft_p95_s SLO − frontend_budget_s) and slo_met (stable and all latency SLIs within target).
    An unstable run (queue growing, ρ ≥ 1) has no meaningful percentile: report it as unstable.
    """
    gaps = res.attrs.get("itl_s", np.array([]))
    garr = res.attrs.get("itl_arrival_s", np.array([]))
    res = res.copy(deep=False)
    res.attrs = {}                     # pandas deep-copies attrs on every operation; drop the big arrays
    lo = res["arrival_s"].min() + slo.get("warmup_exclude_s", 0)
    hi = res["arrival_s"].max() - slo.get("cooldown_exclude_s", 0)
    w = res[(res["arrival_s"] >= lo) & (res["arrival_s"] <= hi)]
    ok = w[w["status"] == "ok"]
    ref = ok[ok["prompt_tokens"] <= slo["ttft_reference_prompt_tokens"]]
    g = gaps[(garr >= lo) & (garr <= hi)] if len(gaps) else np.array([np.nan])
    target = slo["ttft_p95_s"] - slo.get("frontend_budget_s", 0.0)
    span = hi - lo
    q = lambda s, p: float(np.nanpercentile(s, p))  # noqa: E731
    trend = float(np.polyfit(ref["arrival_s"], ref["ttft_s"], 1)[0]) if len(ref) > 10 else float("nan")
    meets = ((ok["prompt_tokens"] > slo["ttft_reference_prompt_tokens"]) | (ok["ttft_s"] <= target)) & \
            (ok["tpot_s"].fillna(0) <= slo["tpot_p95_s"])
    out = {"ttft_p50_s": q(ref["ttft_s"], 50), "ttft_p95_s": q(ref["ttft_s"], 95), "ttft_p99_s": q(ref["ttft_s"], 99),
           "tpot_p50_s": q(ok["tpot_s"], 50), "tpot_p95_s": q(ok["tpot_s"], 95), "tpot_p99_s": q(ok["tpot_s"], 99),
           "itl_p95_s": q(g, 95), "itl_p99_s": q(g, 99), "e2e_p95_s": q(ok["e2e_s"], 95),
           "output_tokens_per_s": float(ok["output_tokens"].sum() / span),
           "input_tokens_per_s": float(ok["prompt_tokens"].sum() / span),
           "rejected": int((w["status"] == "rejected").sum()),
           "error_rate": float((w["status"] == "rejected").mean()),
           "preemptions": int(w["preemptions"].sum()),
           "goodput_frac": float(meets.sum() / len(w)), "ttft_trend": trend, "stable": bool(trend < 0.005),
           "ttft_target_s": target}
    out["slo_met"] = bool(out["stable"] and out["ttft_p95_s"] <= target and out["tpot_p95_s"] <= slo["tpot_p95_s"]
                          and out["itl_p99_s"] <= slo.get("itl_p99_s", np.inf))
    return out


def replicate(traces: list[pd.DataFrame], model: dict, hw: dict, cfg: dict, slo: dict,
              rate_scale: float = 1.0) -> pd.DataFrame:
    """Run simulate + summarize on every trace (independent seeds). One row per seed."""
    return pd.DataFrame([summarize(simulate(tr, model, hw, cfg, rate_scale), slo) for tr in traces])


def aggregate(reps: pd.DataFrame) -> dict[str, object]:
    """Across seeds: median, min and max of ttft_p95_s, tpot_p95_s, itl_p99_s, output_tokens_per_s;
    stable_all (every seed stable); slo_met_all (every seed met the SLO). If any seed is unstable, the
    latency medians are reported as None ("unstable"), not as numbers."""
    out: dict[str, object] = {"n_seeds": int(len(reps)), "stable_all": bool(reps["stable"].all()),
                              "slo_met_all": bool(reps["slo_met"].all())}
    for k in ("ttft_p95_s", "tpot_p95_s", "itl_p99_s", "output_tokens_per_s"):
        unstable_latency = (not out["stable_all"]) and k != "output_tokens_per_s"
        out[f"{k}_median"] = None if unstable_latency else float(reps[k].median())
        out[f"{k}_min"] = float(reps[k].min())
        out[f"{k}_max"] = float(reps[k].max())
    return out


# ----------------------------------------------------------------------------------------------
# 3. SLOs, rollout gates and cost
# ----------------------------------------------------------------------------------------------


def error_budget_minutes(availability: float, window_days: float) -> float:
    """Allowed unavailability in minutes: (1 − availability) × window_days × 1,440."""
    return (1 - availability) * window_days * 1440


def burn_rate(error_rate: float, availability: float) -> float:
    """How fast the error budget is being consumed: error_rate / (1 − availability)."""
    return error_rate / (1 - availability)


def rollback_decision(canary: dict, baseline: dict, slo: dict, max_regression: float = 0.10,
                      fast_burn: float = 14.4) -> tuple[bool, list[str]]:
    """Automated canary gate. Roll back if ANY of:
      * canary ttft_p95_s > slo['ttft_p95_s'] − frontend budget, tpot_p95_s > slo['tpot_p95_s'], or
        itl_p99_s > slo['itl_p99_s'] (when present);
      * canary ttft_p95_s or tpot_p95_s worse than baseline by more than ``max_regression`` (fraction);
      * burn_rate(canary error_rate, availability) ≥ ``fast_burn`` (14.4 = 2 % of a 30-day budget in 1 h).
    Returns (rollback, reasons)."""
    reasons = []
    if canary["ttft_p95_s"] > slo["ttft_p95_s"] - slo.get("frontend_budget_s", 0.0):
        reasons.append("ttft_p95 above SLO")
    if canary["tpot_p95_s"] > slo["tpot_p95_s"]:
        reasons.append("tpot_p95 above SLO")
    if "itl_p99_s" in canary and "itl_p99_s" in slo and canary["itl_p99_s"] > slo["itl_p99_s"]:
        reasons.append("itl_p99 above SLO")
    for k in ("ttft_p95_s", "tpot_p95_s"):
        if canary[k] > baseline[k] * (1 + max_regression):
            reasons.append(f"{k} regressed > {max_regression:.0%} vs baseline")
    if burn_rate(canary["error_rate"], slo["availability"]) >= fast_burn:
        reasons.append("error-budget fast burn")
    return bool(reasons), reasons


def cost_per_million_tokens(summary: dict, cfg: dict, econ: dict) -> dict[str, float]:
    """Cost of one replica's GPUs per million tokens [MODELED].

    usd_per_hour = tp × gpu_hour_usd / fleet_utilization (idle capacity is paid for too);
    usd_per_m_total = usd_per_hour / ((output + input tokens/s) × 3600) × 1e6 — the headline for an
    input-dominated mix; usd_per_m_output = usd_per_hour / (output tokens/s × 3600) × 1e6 (all cost
    loaded on output tokens; an upper bound for output pricing).
    """
    h = cfg["tp"] * econ["gpu_hour_usd"] / econ["fleet_utilization"]
    o = summary["output_tokens_per_s"] * 3600
    i = summary["input_tokens_per_s"] * 3600
    return {"usd_per_hour": h, "usd_per_m_total": h / (o + i) * 1e6, "usd_per_m_output": h / o * 1e6}
