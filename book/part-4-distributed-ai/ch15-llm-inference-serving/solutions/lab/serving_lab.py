"""Chapter 15 lab — LLM serving capacity, trace analysis, and disaggregation model.

REFERENCE SOLUTION (instructor only). Same public API as ``lab/starter/serving_lab.py``.

Units: bytes (B), seconds (s), FLOP/s, B/s. Link rates are given in Gb/s (10^9 bit/s) and are
converted with ``/ 8``. Every number this module produces is [MODELED] (parts A and C) or derived
from a [SIMULATED] trace (part B); none of it is a measurement of real hardware.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import yaml

# =============================================================================================
# Loaders (provided, identical in starter)
# =============================================================================================


def load_config(path: str | Path) -> dict:
    """Load ``configs.yaml`` (model, GPU, serving configs, workload, disaggregation)."""
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_requests(path: str | Path) -> pd.DataFrame:
    """Load ``requests.csv``. Times are seconds since trace start."""
    return pd.read_csv(path)


def load_token_gaps(path: str | Path) -> pd.DataFrame:
    """Load ``token_gaps.csv``: one row per *sampled* request, ``itl_ms`` = ';'-joined gaps (ms)."""
    return pd.read_csv(path, dtype={"itl_ms": str}, keep_default_na=False)


def load_telemetry(path: str | Path) -> pd.DataFrame:
    """Load ``replica_telemetry.csv`` (5-second samples per replica)."""
    return pd.read_csv(path)


# =============================================================================================
# Part A — capacity model
# =============================================================================================


def kv_bytes_per_token(n_layers: int, n_kv_heads: int, head_dim: int, bytes_per_elem: float) -> int:
    """KV-cache bytes for one token: 2 (K and V) x layers x KV heads x head_dim x bytes/element."""
    return int(round(2 * n_layers * n_kv_heads * head_dim * bytes_per_elem))


def kv_budget_bytes(n_gpus: int, hbm_bytes_per_gpu: float, mem_fraction: float,
                    weight_bytes: float, reserve_bytes_per_gpu: float) -> float:
    """Bytes left for the KV cache in one replica.

    budget = n_gpus * hbm * mem_fraction - weight_bytes - n_gpus * reserve_per_gpu
    ``reserve`` covers activations, CUDA graphs, communication buffers. Returns >= 0.
    """
    return max(0.0, n_gpus * hbm_bytes_per_gpu * mem_fraction - weight_bytes
               - n_gpus * reserve_bytes_per_gpu)


def max_concurrent_sequences(kv_budget: float, kv_per_token: int, seq_tokens: int,
                             block_tokens: int = 16) -> int:
    """Max sequences of ``seq_tokens`` that fit in a paged KV pool of ``kv_budget`` bytes.

    Pool blocks = floor(budget / (block_tokens * kv_per_token)); each sequence needs
    ceil(seq_tokens / block_tokens) blocks; result = floor(pool / per_seq).
    """
    pool_blocks = int(kv_budget // (block_tokens * kv_per_token))
    per_seq = math.ceil(seq_tokens / block_tokens)
    return pool_blocks // per_seq


def prefill_time_s(n_params: float, prompt_tokens: int, n_gpus: int, peak_flops_per_gpu: float,
                   mfu: float) -> float:
    """Compute-bound prefill time: 2 * N * P / (n_gpus * peak * MFU). Ignores the attention
    O(P^2) term (a few % at 2k tokens; much larger beyond ~16k)."""
    return 2.0 * n_params * prompt_tokens / (n_gpus * peak_flops_per_gpu * mfu)


def decode_step_time_s(weight_bytes: float, batch: float, avg_context_tokens: float,
                       kv_per_token: int, n_gpus: int, hbm_bw_per_gpu: float,
                       hbm_efficiency: float = 1.0, overhead_s: float = 0.0) -> float:
    """HBM-bandwidth-bound decode step: every step streams all weights once plus the KV cache of
    every running sequence.

    t = overhead + (W + batch * ctx * kv_per_token) / (n_gpus * bw * efficiency)
    With efficiency = 1 and overhead = 0 this is a hard lower bound on TPOT.
    """
    bytes_moved = weight_bytes + batch * avg_context_tokens * kv_per_token
    return overhead_s + bytes_moved / (n_gpus * hbm_bw_per_gpu * hbm_efficiency)


def decode_tokens_per_s(weight_bytes: float, batch: float, avg_context_tokens: float,
                        kv_per_token: int, n_gpus: int, hbm_bw_per_gpu: float,
                        hbm_efficiency: float = 1.0, overhead_s: float = 0.0) -> float:
    """Aggregate decode throughput of one replica (tokens/s) = batch / decode_step_time."""
    return batch / decode_step_time_s(weight_bytes, batch, avg_context_tokens, kv_per_token,
                                      n_gpus, hbm_bw_per_gpu, hbm_efficiency, overhead_s)


def _kvpt(cfg: dict) -> int:
    m = cfg["model"]
    return kv_bytes_per_token(m["n_layers"], m["n_kv_heads"], m["head_dim"], m["kv_bytes_per_elem"])


def _peak(cfg: dict, sc: dict) -> float:
    return cfg["gpu"]["fp8_peak_flops"] if sc["weight_dtype"] == "fp8" else cfg["gpu"]["bf16_peak_flops"]


def compare_serving_configs(cfg: dict) -> pd.DataFrame:
    """Evaluate every entry of ``cfg['serving_configs']`` at its saturated operating point.

    For each config: max_seqs at ``workload.capacity_seq_tokens``; batch = min(max_batch, max_seqs);
    tpot_s = decode_step_time at avg context = prompt + output/2; tokens_per_s_per_node =
    batch / tpot * replicas_per_node; prefill_s for ``workload.prompt_tokens``.
    Columns: name, max_seqs, batch, tpot_s, tokens_per_s_per_node, prefill_s, meets_tpot_slo.
    """
    g, w, m = cfg["gpu"], cfg["workload"], cfg["model"]
    kvpt = _kvpt(cfg)
    ctx = w["prompt_tokens"] + w["output_tokens"] / 2
    rows = []
    for sc in cfg["serving_configs"]:
        budget = kv_budget_bytes(sc["tp"], g["hbm_bytes"], sc["mem_fraction"], sc["weight_bytes"],
                                 sc["reserve_bytes_per_gpu"])
        mx = max_concurrent_sequences(budget, kvpt, w["capacity_seq_tokens"], sc["block_tokens"])
        batch = min(sc["max_batch"], mx)
        tpot = decode_step_time_s(sc["weight_bytes"], batch, ctx, kvpt, sc["tp"], g["hbm_bw"],
                                  sc["hbm_efficiency"], sc["step_overhead_s"])
        rows.append({
            "name": sc["name"], "max_seqs": mx, "batch": batch, "tpot_s": tpot,
            "tokens_per_s_per_node": batch / tpot * sc["replicas_per_node"],
            "prefill_s": prefill_time_s(m["n_params"], w["prompt_tokens"], sc["tp"], _peak(cfg, sc),
                                        sc["prefill_mfu"]),
            "meets_tpot_slo": tpot <= w["tpot_slo_s"],
        })
    return pd.DataFrame(rows)


def recommend_config(table: pd.DataFrame, objective: str) -> str:
    """Pick a config name. ``latency``: lowest tpot_s among SLO-meeting rows.
    ``throughput``: highest tokens_per_s_per_node among SLO-meeting rows."""
    ok = table[table["meets_tpot_slo"]]
    if ok.empty:
        raise ValueError("no configuration meets the TPOT SLO")
    if objective == "latency":
        return str(ok.loc[ok["tpot_s"].idxmin(), "name"])
    if objective == "throughput":
        return str(ok.loc[ok["tokens_per_s_per_node"].idxmax(), "name"])
    raise ValueError(f"unknown objective {objective!r}")


# =============================================================================================
# Part B — serving-trace analyzer
# =============================================================================================


def request_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with per-request latency columns (seconds):

    queue_s = sched_s - arrival_s; prefill_s = first_token_s - sched_s;
    ttft_s = first_token_s - arrival_s; e2e_s = finish_s - arrival_s;
    tpot_s = (finish_s - first_token_s) / (output_tokens - 1), NaN when output_tokens < 2.
    """
    out = df.copy()
    out["queue_s"] = out["sched_s"] - out["arrival_s"]
    out["prefill_s"] = out["first_token_s"] - out["sched_s"]
    out["ttft_s"] = out["first_token_s"] - out["arrival_s"]
    out["e2e_s"] = out["finish_s"] - out["arrival_s"]
    denom = (out["output_tokens"] - 1).where(out["output_tokens"] >= 2)
    out["tpot_s"] = (out["finish_s"] - out["first_token_s"]) / denom
    return out


def latency_percentiles(values: Iterable[float], ps: tuple[float, ...] = (50, 90, 95, 99)) -> dict:
    """Percentiles (numpy 'linear' method) of finite values, keyed 'p50', 'p90', ..."""
    arr = np.asarray(list(values), dtype=float)
    arr = arr[np.isfinite(arr)]
    return {f"p{int(p) if float(p).is_integer() else p}": float(np.percentile(arr, p)) for p in ps}


def itl_values_s(gaps: pd.DataFrame) -> np.ndarray:
    """Flatten the sampled inter-token gaps into one array of seconds."""
    vals = [float(x) for s in gaps["itl_ms"] if s for x in s.split(";")]
    return np.asarray(vals) / 1000.0


def slo_report(metrics: pd.DataFrame, slos: dict, duration_s: float) -> dict:
    """SLO attainment and goodput.

    ``slos`` maps tenant -> {"ttft_s": x, "tpot_s": y}. A request *meets SLO* when ttft_s <= ttft
    AND (tpot_s <= tpot OR tpot_s is NaN). Returns:
      attainment       fraction of requests meeting SLO
      goodput_rps      SLO-meeting requests / duration_s
      throughput_rps   all completed requests / duration_s
      output_tokens_per_s  sum(output_tokens) / duration_s
      per_tenant       {tenant: attainment}
    """
    ttft_lim = metrics["tenant"].map(lambda t: slos[t]["ttft_s"])
    tpot_lim = metrics["tenant"].map(lambda t: slos[t]["tpot_s"])
    ok = (metrics["ttft_s"] <= ttft_lim) & ((metrics["tpot_s"] <= tpot_lim) | metrics["tpot_s"].isna())
    per = ok.groupby(metrics["tenant"]).mean().to_dict()
    return {
        "attainment": float(ok.mean()),
        "goodput_rps": float(ok.sum() / duration_s),
        "throughput_rps": float(len(metrics) / duration_s),
        "output_tokens_per_s": float(metrics["output_tokens"].sum() / duration_s),
        "per_tenant": {k: float(v) for k, v in per.items()},
    }


def windowed(metrics: pd.DataFrame, window_s: float = 15.0) -> pd.DataFrame:
    """Aggregate by arrival-time window. Index: window start (s). Columns: arrivals, queue_p95_s,
    ttft_p95_s, tpot_p50_s, preemptions (sum), preempted_frac."""
    w = (metrics["arrival_s"] // window_s) * window_s
    g = metrics.groupby(w)
    out = pd.DataFrame({
        "arrivals": g.size(),
        "queue_p95_s": g["queue_s"].quantile(0.95),
        "ttft_p95_s": g["ttft_s"].quantile(0.95),
        "tpot_p50_s": g["tpot_s"].median(),
        "preemptions": g["preemptions"].sum(),
        "preempted_frac": g["preemptions"].apply(lambda s: float((s > 0).mean())),
    })
    out.index.name = "window_s"
    return out


def _episodes(flags: pd.Series, window_s: float, max_gap: int = 1) -> list[tuple[float, float]]:
    """Merge flagged windows into [start, end) episodes, bridging gaps of <= max_gap windows."""
    starts = sorted(float(i) for i, f in flags.items() if f)
    eps: list[list[float]] = []
    for s in starts:
        if eps and s - eps[-1][1] <= max_gap * window_s:
            eps[-1][1] = s + window_s
        else:
            eps.append([s, s + window_s])
    return [(a, b) for a, b in eps]


def detect_issues(metrics: pd.DataFrame, window_s: float = 15.0, queue_p95_threshold_s: float = 2.0,
                  burst_ratio: float = 1.5, min_preemptions: int = 2,
                  slow_ratio: float = 1.4) -> list[dict]:
    """Find planted-style anomalies. Returns a list of dicts with key ``type``:

    * ``queueing_collapse`` — an episode of windows with queue p95 > threshold that contains at
      least one window whose arrivals >= burst_ratio x the median window arrivals (arrival-driven).
      Keys: start_s, end_s, peak_queue_p95_s, peak_arrival_ratio.
    * ``preemption_storm`` — an episode of windows with preemptions >= min_preemptions (bridging
      single quiet windows). Keys: start_s, end_s, preemptions.
    * ``capacity_shortfall`` — a high-queue episode with neither an arrival spike nor overlapping
      preemption storm. Keys: start_s, end_s.
    * ``slow_replica`` — replica whose median TPOT > slow_ratio x the median of the other replicas'
      medians. Keys: replica, tpot_p50_s, peer_tpot_p50_s.
    """
    win = windowed(metrics, window_s)
    med_arr = float(win["arrivals"].median())
    issues: list[dict] = []

    storms = _episodes(win["preemptions"] >= min_preemptions, window_s, max_gap=2)
    for a, b in storms:
        issues.append({"type": "preemption_storm", "start_s": a, "end_s": b,
                       "preemptions": int(win.loc[a:b - window_s, "preemptions"].sum())})

    for a, b in _episodes(win["queue_p95_s"] > queue_p95_threshold_s, window_s, max_gap=0):
        seg = win.loc[a:b - window_s]
        ratio = float(seg["arrivals"].max() / med_arr)
        if ratio >= burst_ratio:
            issues.append({"type": "queueing_collapse", "start_s": a, "end_s": b,
                           "peak_queue_p95_s": float(seg["queue_p95_s"].max()),
                           "peak_arrival_ratio": ratio})
        elif not any(sa < b and a < sb for sa, sb in storms):
            issues.append({"type": "capacity_shortfall", "start_s": a, "end_s": b})

    med = metrics.groupby("replica")["tpot_s"].median()
    for rep, v in med.items():
        peers = float(med.drop(rep).median())
        if v > slow_ratio * peers:
            issues.append({"type": "slow_replica", "replica": str(rep), "tpot_p50_s": float(v),
                           "peer_tpot_p50_s": peers})
    return issues


def telemetry_evidence(tel: pd.DataFrame, start_s: float, end_s: float) -> dict:
    """Corroborate an episode with replica telemetry in [start_s, end_s]:
    kv_usage_max_pct, waiting_mean (mean over samples and replicas), preemptions_delta
    (sum over replicas of the counter increase within the interval), gpu_busy_mean_pct."""
    seg = tel[(tel["t_s"] >= start_s) & (tel["t_s"] <= end_s)]
    delta = 0
    for _, s in seg.groupby("replica"):
        delta += int(s["preemptions_total"].max() - s["preemptions_total"].min())
    return {
        "kv_usage_max_pct": float(seg["kv_usage_pct"].max()),
        "waiting_mean": float(seg["num_waiting"].mean()),
        "preemptions_delta": delta,
        "gpu_busy_mean_pct": float(seg["gpu_busy_pct"].mean()),
    }


# =============================================================================================
# Part C — disaggregated prefill/decode model and speculative decoding
# =============================================================================================


def kv_transfer_time_s(kv_bytes: float, link_gbps: float, n_links: int, efficiency: float,
                       fixed_latency_s: float) -> float:
    """t = fixed_latency + bytes / (n_links * link_gbps * 1e9 / 8 * efficiency)."""
    return fixed_latency_s + kv_bytes / (n_links * link_gbps * 1e9 / 8 * efficiency)


def md1_wait_s(rho: float, service_s: float) -> float:
    """Mean M/D/1 queueing delay: rho * s / (2 * (1 - rho)); inf when rho >= 1."""
    if rho >= 1.0:
        return math.inf
    return rho * service_s / (2.0 * (1.0 - rho))


def _decode_fixed_point(rate_per_replica: float, output_tokens: int, step, stall_frac: float = 0.0,
                        iters: int = 500) -> tuple[float, float, float]:
    """Solve B = rate * output * TPOT, TPOT = step(B) / (1 - stall_frac). Returns (tpot, B, step).

    Returns (inf, inf, inf) when no finite fixed point exists, i.e. decode cannot keep up with the
    offered load (the queue of decoding sequences grows without bound)."""
    if stall_frac >= 1.0:
        return math.inf, math.inf, math.inf
    tpot = step(0.0) / (1.0 - stall_frac)
    for _ in range(iters):
        b = rate_per_replica * output_tokens * tpot
        tpot = step(b) / (1.0 - stall_frac)
        if tpot > 1e3:
            return math.inf, math.inf, math.inf
    b = rate_per_replica * output_tokens * tpot
    return tpot, b, step(b)


def compare_designs(cfg: dict) -> pd.DataFrame:
    """Compare shared-pool vs disaggregated (RDMA, TCP) serving for ``cfg['disaggregation']``.

    Model ([MODELED]; assumptions in configs.yaml):
      t_p   = prefill_time(prompt) on the replica config
      t_d(B)= decode_step_time(B, ctx = prompt + output/2)
      Shared pool (n replicas, rate r = lambda/n; prefill iterations pause decode, no chunking):
        rho_p = r * t_p;  TTFT = M/D/1 wait + t_p;  TPOT = t_d(B)/(1-rho_p), B = r*out*TPOT;
        itl_worst = t_d + t_p (one prefill lands between two tokens)
      Disaggregated (n_prefill, n_decode; first token returned by the prefill pool):
        rho_p = lambda/n_prefill * t_p;  TTFT = M/D/1 wait + t_p
        TPOT = t_d(B) + t_kv/(out-1), B = (lambda/n_decode)*out*t_d;  itl_worst = t_d + t_kv
      kv_bytes = prompt * kv_per_token;  agg_kv_Gbps = lambda * kv_bytes * 8 / 1e9
      per_decode_replica_Gbps = agg / n_decode;  link_util_pct = per-replica demand / achievable
    """
    g, m, d = cfg["gpu"], cfg["model"], cfg["disaggregation"]
    sc = next(s for s in cfg["serving_configs"] if s["name"] == d["replica_config"])
    kvpt = _kvpt(cfg)
    lam, P, O = d["request_rate"], d["prompt_tokens"], d["output_tokens"]
    ctx = P + O / 2
    t_p = prefill_time_s(m["n_params"], P, sc["tp"], _peak(cfg, sc), sc["prefill_mfu"])

    def step(b: float) -> float:
        return decode_step_time_s(sc["weight_bytes"], b, ctx, kvpt, sc["tp"], g["hbm_bw"],
                                  sc["hbm_efficiency"], sc["step_overhead_s"])

    kv_bytes = P * kvpt
    agg_gbps = lam * kv_bytes * 8 / 1e9
    rows = []
    n = d["shared_replicas"]
    rho = lam / n * t_p
    tpot, b, td = _decode_fixed_point(lam / n, O, step, stall_frac=rho)
    rows.append({"design": "shared", "prefill_rho": rho, "ttft_s": md1_wait_s(rho, t_p) + t_p,
                 "tpot_s": tpot, "itl_worst_s": td + t_p, "decode_batch": b, "kv_transfer_s": 0.0,
                 "agg_kv_Gbps": 0.0, "per_decode_replica_Gbps": 0.0, "link_util_pct": 0.0})
    npf, nd = d["prefill_replicas"], d["decode_replicas"]
    rho = lam / npf * t_p
    for tname, t in d["transports"].items():
        t_kv = kv_transfer_time_s(kv_bytes, t["link_gbps"], t["links_per_replica"], t["efficiency"],
                                  t["fixed_latency_s"])
        td, b, _ = _decode_fixed_point(lam / nd, O, step)
        per = agg_gbps / nd
        achievable = t["link_gbps"] * t["links_per_replica"] * t["efficiency"]
        rows.append({"design": f"disagg-{tname}", "prefill_rho": rho,
                     "ttft_s": md1_wait_s(rho, t_p) + t_p, "tpot_s": td + t_kv / (O - 1),
                     "itl_worst_s": td + t_kv, "decode_batch": b, "kv_transfer_s": t_kv,
                     "agg_kv_Gbps": agg_gbps, "per_decode_replica_Gbps": per,
                     "link_util_pct": 100.0 * per / achievable})
    return pd.DataFrame(rows)


def speculative_expected_tokens(alpha: float, k: int) -> float:
    """Expected tokens per target verification step with k draft tokens and i.i.d. acceptance
    rate alpha (Leviathan et al., 2023): (1 - alpha^(k+1)) / (1 - alpha); k+1 when alpha == 1."""
    if alpha >= 1.0:
        return float(k + 1)
    return (1.0 - alpha ** (k + 1)) / (1.0 - alpha)


def speculative_speedup(alpha: float, k: int, draft_cost_ratio: float,
                        verify_cost_ratio: float = 1.0) -> float:
    """Walltime speedup vs plain decoding = E[tokens] / (k * c_draft + c_verify), costs relative to
    one target decode step. c_verify = 1 assumes verifying k+1 tokens is still memory-bound."""
    return speculative_expected_tokens(alpha, k) / (k * draft_cost_ratio + verify_cost_ratio)
