"""Capstone D starter: W-INFER capacity model, request-level serving simulator, SLOs and cost.

Implement every function that raises NotImplementedError (the docstrings are the specification), then
run ``python check.py`` from starter-kit/.

The simulator is [SIMULATED]: an iteration-level model of continuous batching on ONE replica with a
roofline iteration cost (max of compute time and HBM traffic time, plus a fixed overhead). It does NOT
capture kernel-level effects, TP all-reduce variance, CPU scheduler overhead, tokenizer/detokenizer
cost, network or load-balancer latency (budgeted separately as frontend_budget_s), prefix caching,
speculative decoding, or GPU clock behaviour.
"""
from __future__ import annotations

from collections import deque  # noqa: F401  (you will need it)
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
    raise NotImplementedError("kv_bytes_per_token: 2 x layers x kv_heads x head_dim x bytes")


def capacity(model: dict, hw: dict, cfg: dict) -> dict[str, float]:
    """Per-replica memory plan. Returns weights_bytes, weights_bytes_per_gpu, usable_hbm_bytes,
    reserve_bytes, kv_budget_bytes, kv_tokens (int), max_seqs_at_4k (int, 4,096-token contexts).

    usable = tp × hbm × gpu_memory_utilization; kv_budget = usable − weights − tp × runtime reserve.
    """
    raise NotImplementedError("capacity: weights, reserve and KV-cache budget per replica")


def attention_flops(model: dict, prefix: int, chunk: int) -> float:
    """Causal self-attention FLOPs to prefill tokens [prefix, prefix + chunk) of one sequence.

    QKᵀ and AV are 2 FLOP per multiply-accumulate each, over a causal (half) mask: total for an n-token
    prompt ≈ 2 × layers × hidden × n². For a chunk: 2 × L × d × ((prefix + chunk)² − prefix²), which sums
    exactly to the full-prompt value over chunks. Adds ≈ 30 % to a 32k prompt's linear 2·N·n FLOPs.
    """
    raise NotImplementedError("attention_flops: 2·L·d·((p+c)² − p²) for a causal prefill chunk")


def iteration_time_s(prefill_tokens: int, decode_seqs: int, kv_tokens_read: int, model: dict, hw: dict,
                     cfg: dict, attn_flops: float = 0.0) -> float:
    """Roofline cost of one engine iteration (seconds).

    compute = (2 × params × (prefill_tokens + decode_seqs) + attn_flops) / (tp × peak[dtype] × prefill_mfu)
    memory  = (weights bytes + kv_tokens_read × kv_bytes_per_token) / (tp × hbm_bw × hbm_bw_efficiency)
    time    = iteration_overhead[tp] + max(compute, memory)
    Decode attention FLOPs are omitted (decode is memory-bound; its KV reads are in the memory term).
    """
    raise NotImplementedError("iteration_time_s: overhead + max(compute incl. attention, HBM traffic)")


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
    raise NotImplementedError("simulate: iteration-level continuous batching with paged-KV admission and ITL capture")


def summarize(res: pd.DataFrame, slo: dict) -> dict[str, float]:
    """SLI summary over the steady-state window: requests arriving in
    [first arrival + warmup_exclude_s, last arrival − cooldown_exclude_s].

    Returns ttft_p50/p95/p99_s (OK reference-length prompts, engine-side), tpot_p50/p95/p99_s (per-request
    mean), itl_p95_s and itl_p99_s (per-token gaps), e2e_p95_s, output/input_tokens_per_s (completed tokens
    of window requests / window length), rejected, error_rate, preemptions, goodput_frac, ttft_trend
    (s of extra TTFT per s of arrival time, linear fit), stable (ttft_trend < 0.005), ttft_target_s
    (= ttft_p95_s SLO − frontend_budget_s) and slo_met (stable and all latency SLIs within target).
    An unstable run (queue growing, ρ ≥ 1) has no meaningful percentile: report it as unstable.
    Tip: read res.attrs first, then drop them (pandas deep-copies attrs on every operation).
    """
    raise NotImplementedError("summarize: steady-state SLIs, ITL tails, stability, goodput")


def replicate(traces: list[pd.DataFrame], model: dict, hw: dict, cfg: dict, slo: dict,
              rate_scale: float = 1.0) -> pd.DataFrame:
    """Run simulate + summarize on every trace (independent seeds). One row per seed."""
    raise NotImplementedError("replicate: run every seed")


def aggregate(reps: pd.DataFrame) -> dict[str, object]:
    """Across seeds: median, min and max of ttft_p95_s, tpot_p95_s, itl_p99_s, output_tokens_per_s;
    stable_all (every seed stable); slo_met_all (every seed met the SLO). If any seed is unstable, the
    latency medians are reported as None ("unstable"), not as numbers."""
    raise NotImplementedError("aggregate: median and range across seeds; None when unstable")


# ----------------------------------------------------------------------------------------------
# 3. SLOs, rollout gates and cost
# ----------------------------------------------------------------------------------------------


def error_budget_minutes(availability: float, window_days: float) -> float:
    """Allowed unavailability in minutes: (1 − availability) × window_days × 1,440."""
    raise NotImplementedError("error_budget_minutes")


def burn_rate(error_rate: float, availability: float) -> float:
    """How fast the error budget is being consumed: error_rate / (1 − availability)."""
    raise NotImplementedError("burn_rate")


def rollback_decision(canary: dict, baseline: dict, slo: dict, max_regression: float = 0.10,
                      fast_burn: float = 14.4) -> tuple[bool, list[str]]:
    """Automated canary gate. Roll back if ANY of:
      * canary ttft_p95_s > slo['ttft_p95_s'] − frontend budget, tpot_p95_s > slo['tpot_p95_s'], or
        itl_p99_s > slo['itl_p99_s'] (when present);
      * canary ttft_p95_s or tpot_p95_s worse than baseline by more than ``max_regression`` (fraction);
      * burn_rate(canary error_rate, availability) ≥ ``fast_burn`` (14.4 = 2 % of a 30-day budget in 1 h).
    Returns (rollback, reasons)."""
    raise NotImplementedError("rollback_decision: SLO (with frontend budget and ITL), regression and burn gates")


def cost_per_million_tokens(summary: dict, cfg: dict, econ: dict) -> dict[str, float]:
    """Cost of one replica's GPUs per million tokens [MODELED].

    usd_per_hour = tp × gpu_hour_usd / fleet_utilization (idle capacity is paid for too);
    usd_per_m_total = usd_per_hour / ((output + input tokens/s) × 3600) × 1e6 — the headline for an
    input-dominated mix; usd_per_m_output = usd_per_hour / (output tokens/s × 3600) × 1e6 (all cost
    loaded on output tokens; an upper bound for output pricing).
    """
    raise NotImplementedError("cost_per_million_tokens: total-token headline, output-loaded bound")
