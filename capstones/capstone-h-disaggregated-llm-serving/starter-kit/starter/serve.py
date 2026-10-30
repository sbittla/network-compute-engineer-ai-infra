"""Capstone H starter module - disaggregated LLM serving across prefill and decode pools.

Implement every function marked TODO. The loaders, MODEL constants and hw_profile() are given; the
simulator in sim/serving_sim.py is given. Run ``python check.py`` from starter-kit/. Everything you
compute here is MODELED; anything from the simulator is SIMULATED.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

MODEL = {"params": 70e9, "layers": 80, "d_model": 8192, "kv_heads": 8, "head_dim": 128,
         "bytes_per_elem": 2, "weights_GB": 140.0}
PCIE_GEN5_X16_GBPS_PER_DIR = 63.0    # theoretical, per direction [VENDOR-SPEC, 2026-10] class value


# --------------------------------------------------------------------------- loaders (given)
def load_dataset(data_dir: Path) -> dict[str, Any]:
    """Load data/ (given; not a TODO)."""
    d = Path(data_dir)
    y = lambda f: yaml.safe_load(open(d / f, encoding="utf-8"))  # noqa: E731
    return {"trace": pd.read_csv(d / "trace.csv"), "hardware": pd.read_csv(d / "hardware.csv"),
            "links": pd.read_csv(d / "links.csv"), "qos": y("qos_proposal.yaml"), "slo": y("slo.yaml"),
            "config": y("config.yaml")}


def hw_profile(hardware: pd.DataFrame, name: str, **overrides: Any) -> dict[str, Any]:
    """Return one accelerator row as a dict with the simulator's efficiency defaults (given)."""
    row = hardware.set_index("name").loc[name].to_dict()
    prof = {"gpus_per_instance": int(row["gpus_per_instance"]), "peak_TFLOPs": float(row["peak_TFLOPs"]),
            "hbm_TBps": float(row["hbm_TBps"]), "hbm_GB": float(row["hbm_GB"]),
            "usd_per_gpu_hour": float(row["usd_per_gpu_hour"]), "mfu_prefill": 0.5, "hbm_eff": 0.7,
            "step_overhead_s": 0.004, "reserve_frac": 0.10}
    prof.update(overrides)
    return prof


# --------------------------------------------------------------------------- T1 KV size
def kv_cache_bytes(tokens: int) -> int:
    """KV-cache bytes for ``tokens`` tokens: 2 (K,V) × layers × KV heads × head dim × bytes/elem × tokens."""
    # TODO: derive from MODEL: layers, KV heads (GQA), head dim, bytes per element; K and V
    # TODO: check: 1 token must be 327,680 B (320 KiB) for W-INFER in BF16
    raise NotImplementedError("TODO: implement kv_cache_bytes()")


# --------------------------------------------------------------------------- T2 links
def link_capacity(links: pd.DataFrame) -> list[dict[str, Any]]:
    """Normalise every link profile to achievable GB/s per instance and validate it.

    line rate in Gb/s (convert from GB/s × 8 if ``unit`` says GB/s); achievable GB/s =
    line_Gbps / 8 × nics × efficiency. A profile is INVALID when its per-NIC line rate exceeds what a
    PCIe Gen5 x16 slot can feed (63 GB/s per direction = 504 Gb/s). Returns rows
    {name, transport, line_Gbps, GBps, valid, reason} in input order; GBps is rounded to 0.1.
    """
    # TODO: normalise every row to Gb/s using its unit column, then to achievable GB/s per instance
    # TODO: a single NIC cannot exceed what its PCIe Gen5 x16 slot can feed - flag such rows invalid instead of using them
    raise NotImplementedError("TODO: implement link_capacity()")


# --------------------------------------------------------------------------- T3 roofline
def prefill_time_s(tokens: int, hw: dict[str, Any]) -> float:
    """Compute-bound prefill: (2·N·T + 2·L·d·T²) / (GPUs × peak × MFU)."""
    # TODO: compute-bound: linear FLOPs 2*N*T plus causal attention 2*L*d*T^2
    # TODO: divide by GPUs x peak x MFU from the hw profile
    raise NotImplementedError("TODO: implement prefill_time_s()")


def decode_step_time_s(batch: int, ctx_tokens_total: float, hw: dict[str, Any]) -> float:
    """Memory-bound decode step: (weights + Σctx × KV bytes/token) / (GPUs × HBM × eff) + overhead; 0 if batch = 0."""
    # TODO: memory-bound: every step reads all weights plus the KV of every sequence in the batch
    # TODO: add the fixed per-step overhead; an empty batch costs nothing
    raise NotImplementedError("TODO: implement decode_step_time_s()")


def kv_transfer_exposed_s(tokens: int, link_GBps: float, overhead_s: float, prefill_s: float,
                          pipelined: bool = True) -> float:
    """Exposed KV transfer time after prefill.

    Not pipelined: overhead + bytes / bandwidth. Layer-pipelined (layer i ships while layer i+1
    computes): overhead + max(transfer − prefill × (L−1)/L, transfer / L).
    """
    # TODO: transfer = bytes / bandwidth; with layer pipelining only the part that does not overlap prefill is exposed
    # TODO: even perfectly overlapped, the last layer's share is exposed
    raise NotImplementedError("TODO: implement kv_transfer_exposed_s()")


# --------------------------------------------------------------------------- T4 capacity model
def kv_capacity_tokens(hw: dict[str, Any]) -> int:
    """Tokens of KV that fit on one instance after weights and the reserve fraction."""
    # TODO: HBM per instance minus reserve minus weights, divided by KV bytes per token
    raise NotImplementedError("TODO: implement kv_capacity_tokens()")


def size_pools(trace: pd.DataFrame, hw_p: dict[str, Any], hw_d: dict[str, Any], slo: dict[str, Any],
               rho_max: float) -> dict[str, Any]:
    """Size prefill and decode pools for the SLO's ``target_rps`` (steady state, no burst).

    * mean_prefill_s = mean of prefill_time_s over the trace prompts;
      P = ceil(target_rps × mean_prefill_s / rho_max).
    * Decode batch B = largest batch with decode_step_time_s(B, B × ctx_mean) ≤ 0.8 × tpot_p95_s AND
      B × (mean_prompt + mean_output) ≤ kv_capacity_tokens(hw_d); ctx_mean = mean_prompt + mean_output/2.
      Per-instance decode throughput = B / step(B). D = ceil(target_rps × mean_output / (rho_max × throughput)).
    * kv_GBps_total = target_rps × mean_prompt × KV bytes/token / 1e9.
    Returns {P, D, mean_prefill_s, mean_prompt, mean_output, decode_batch, decode_step_s, decode_tok_per_s_per_instance,
             kv_GBps_total, gpus}.
    """
    # TODO: prefill pool from mean prefill seconds per request and the utilisation cap
    # TODO: decode batch: largest B meeting 0.8 x TPOT SLO and fitting in KV memory
    # TODO: decode pool from required output tokens/s
    raise NotImplementedError("TODO: implement size_pools()")


def utilizations(P: int, D: int, sizing: dict[str, Any], rate_rps: float, mean_output: float,
                 link_GBps: float) -> dict[str, Any]:
    """Utilisation of each resource for a fixed deployment at ``rate_rps``; the highest is the bottleneck.

    prefill     = rate × mean_prefill_s / P
    decode      = rate × mean_output / (D × decode_tok_per_s_per_instance)
    network_out = KV GB/s / P / link_GBps   (each prefill instance's outbound link)
    network_in  = KV GB/s / D / link_GBps   (each decode instance's inbound link: fan-in from P senders)
    network     = max(network_out, network_in) — with P > D the decode side saturates first.
    KV GB/s = rate × mean_prompt × KV bytes/token / 1e9.
    Returns {prefill, decode, network_out, network_in, network, bottleneck}.
    """
    # TODO: one utilisation per resource for a FIXED deployment; the largest is the bottleneck
    # TODO: network has two sides: each prefill instance sends KV/P, each decode instance receives KV/D (fan-in); with P > D the receiver saturates first
    raise NotImplementedError("TODO: implement utilizations()")


# --------------------------------------------------------------------------- T5 admission
def admission_policy(req: dict[str, Any], state: dict[str, Any], hw_p: dict[str, Any] | None = None,
                     slo: dict[str, Any] | None = None) -> str:
    """Admit or reject one request at arrival (called by the simulator).

    ``state['prefill_backlog_s']`` = mean queued prefill seconds per prefill instance. Predicted
    TTFT = backlog + prefill_time_s(prompt). Reject when it exceeds 90 % of the applicable SLO
    (short prompts: ttft_p95_s; prompts above ttft_applies_to_prompt_tokens_max: ttft_long_p95_s).
    """
    # TODO: predict this request's TTFT from the queued prefill backlog plus its own prefill time
    # TODO: use the long-prompt SLO for prompts above the short-prompt limit
    # TODO: leave 10 % margin; return 'admit' or 'reject'
    raise NotImplementedError("TODO: implement admission_policy()")


# --------------------------------------------------------------------------- T6 speculative decoding
def speculative_gain(alpha: float, k: int, c: float) -> dict[str, float]:
    """Speculative decoding with acceptance rate α, k draft tokens, draft/target step cost ratio c.

    Expected tokens per target step E = (1 − α^(k+1)) / (1 − α) (Leviathan et al., 2023);
    cost per target step = 1 + k·c; speedup = E / (1 + k·c). (Memory-bound regime: the target
    verifies k+1 tokens for about the cost of one step; at large batch this assumption weakens.)
    """
    # TODO: expected accepted tokens per target step: (1 - a^(k+1)) / (1 - a)
    # TODO: each draft token costs c target-steps
    raise NotImplementedError("TODO: implement speculative_gain()")


def speculative_gain_at_batch(alpha: float, k: int, c: float, batch: int, ctx_tokens_total: float,
                              hw: dict[str, Any], decode_mfu: float = 0.6) -> dict[str, float]:
    """Batch-aware speculative decoding speedup at an operating point.

    A decode step costs max(compute, memory) + overhead, where compute = 2·N·(tokens verified) /
    (GPUs × peak × decode_mfu) and memory = (weights + Σctx × KV bytes) / (GPUs × HBM × eff).
    Plain step: B tokens. Verification step: B·(k+1) tokens (same memory traffic). Draft cost per
    cycle = k·c × plain step. Speedup = E × plain / (verify + k·c × plain), E from speculative_gain().
    At small batch both steps are memory-bound and this reduces to E / (1 + k·c); at large batch the
    verification step becomes compute-bound and the gain shrinks.
    """
    # TODO: a decode step costs max(compute, memory) + overhead
    # TODO: verification processes B*(k+1) tokens with the same memory traffic: at large B it turns compute-bound
    # TODO: speedup = E * plain / (verify + k*c*plain); check it reduces to the simple model at batch 1
    raise NotImplementedError("TODO: implement speculative_gain_at_batch()")


def best_draft_length(alpha: float, c: float, k_max: int = 8) -> int:
    """k in 1..k_max with the highest speedup (smallest k on ties)."""
    # TODO: search k = 1..k_max; prefer the smaller k on ties
    raise NotImplementedError("TODO: implement best_draft_length()")


# --------------------------------------------------------------------------- T7 QoS audit
def audit_qos(qos: dict[str, Any]) -> list[str]:
    """Return sorted finding codes for the proposed QoS/isolation design.

    kv_dscp_collision                 KV traffic uses the same DSCP as training RoCE (cannot be told apart)
    kv_shares_lossless_training_tc    KV mapped to the training lossless traffic class
    cnp_not_strict_priority           CNP class missing or not strict priority
    kv_unencrypted_across_boundary    KV crosses a tenant boundary with kv_encryption 'none'
    kv_no_ecn                         KV class without ECN marking
    """
    # TODO: compare the kv-transfer class with training-roce and cnp
    # TODO: check the trust boundary and encryption setting
    # TODO: return sorted finding codes
    raise NotImplementedError("TODO: implement audit_qos()")


# --------------------------------------------------------------------------- T8 cost
def cost_per_million_tokens(gpus: int, usd_per_gpu_hour: float, output_tok_per_s: float) -> float:
    """USD per 1,000,000 output tokens = gpus × $/GPU-h / (tokens/s × 3,600) × 1e6."""
    # TODO: GPU-hours per second of service divided by tokens per second, scaled to 1e6 tokens
    raise NotImplementedError("TODO: implement cost_per_million_tokens()")
