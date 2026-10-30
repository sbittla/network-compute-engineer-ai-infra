"""Reference implementation — Capstone H disaggregated LLM serving (INSTRUCTOR ONLY).

Same public API as starter-kit/starter/serve.py. All outputs are [MODELED] (closed-form) unless
they come from sim.serving_sim, which is [SIMULATED].
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
    m = MODEL
    return 2 * m["layers"] * m["kv_heads"] * m["head_dim"] * m["bytes_per_elem"] * tokens


# --------------------------------------------------------------------------- T2 links
def link_capacity(links: pd.DataFrame) -> list[dict[str, Any]]:
    """Normalise every link profile to achievable GB/s per instance and validate it.

    line rate in Gb/s (convert from GB/s × 8 if ``unit`` says GB/s); achievable GB/s =
    line_Gbps / 8 × nics × efficiency. A profile is INVALID when its per-NIC line rate exceeds what a
    PCIe Gen5 x16 slot can feed (63 GB/s per direction = 504 Gb/s). Returns rows
    {name, transport, line_Gbps, GBps, valid, reason} in input order; GBps is rounded to 0.1.
    """
    out = []
    for r in links.to_dict("records"):
        gbps = float(r["line_rate"]) * (8 if r["unit"] == "GB/s" else 1)
        ok = gbps <= PCIE_GEN5_X16_GBPS_PER_DIR * 8
        out.append({"name": r["name"], "transport": r["transport"], "line_Gbps": gbps,
                    "GBps": round(gbps / 8 * int(r["nics"]) * float(r["efficiency"]), 1),
                    "overhead_s": float(r["overhead_ms"]) / 1000, "valid": ok,
                    "reason": "" if ok else f"{gbps:.0f} Gb/s per NIC exceeds PCIe Gen5 x16 ({PCIE_GEN5_X16_GBPS_PER_DIR * 8:.0f} Gb/s): unit error"})
    return out


# --------------------------------------------------------------------------- T3 roofline
def prefill_time_s(tokens: int, hw: dict[str, Any]) -> float:
    """Compute-bound prefill: (2·N·T + 2·L·d·T²) / (GPUs × peak × MFU)."""
    flops = 2 * MODEL["params"] * tokens + 2 * MODEL["layers"] * MODEL["d_model"] * tokens ** 2
    return flops / (hw["gpus_per_instance"] * hw["peak_TFLOPs"] * 1e12 * hw["mfu_prefill"])


def decode_step_time_s(batch: int, ctx_tokens_total: float, hw: dict[str, Any]) -> float:
    """Memory-bound decode step: (weights + Σctx × KV bytes/token) / (GPUs × HBM × eff) + overhead; 0 if batch = 0."""
    if batch == 0:
        return 0.0
    byts = MODEL["weights_GB"] * 1e9 + ctx_tokens_total * kv_cache_bytes(1)
    return byts / (hw["gpus_per_instance"] * hw["hbm_TBps"] * 1e12 * hw["hbm_eff"]) + hw["step_overhead_s"]


def kv_transfer_exposed_s(tokens: int, link_GBps: float, overhead_s: float, prefill_s: float,
                          pipelined: bool = True) -> float:
    """Exposed KV transfer time after prefill.

    Not pipelined: overhead + bytes / bandwidth. Layer-pipelined (layer i ships while layer i+1
    computes): overhead + max(transfer − prefill × (L−1)/L, transfer / L).
    """
    xfer = kv_cache_bytes(tokens) / (link_GBps * 1e9)
    if not pipelined:
        return overhead_s + xfer
    return overhead_s + max(xfer - prefill_s * (MODEL["layers"] - 1) / MODEL["layers"], xfer / MODEL["layers"])


# --------------------------------------------------------------------------- T4 capacity model
def kv_capacity_tokens(hw: dict[str, Any]) -> int:
    """Tokens of KV that fit on one instance after weights and the reserve fraction."""
    free = hw["gpus_per_instance"] * hw["hbm_GB"] * (1 - hw["reserve_frac"]) - MODEL["weights_GB"]
    return int(free * 1e9 // kv_cache_bytes(1))


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
    rate = slo["target_rps"]
    mp, mo = trace["prompt"].mean(), trace["output"].mean()
    t_pf = float(sum(prefill_time_s(int(t), hw_p) for t in trace["prompt"]) / len(trace))
    P = math.ceil(rate * t_pf / rho_max)
    ctx = mp + mo / 2
    cap = kv_capacity_tokens(hw_d)
    B = 1
    while (decode_step_time_s(B + 1, (B + 1) * ctx, hw_d) <= 0.8 * slo["tpot_p95_s"]
           and (B + 1) * (mp + mo) <= cap):
        B += 1
    step = decode_step_time_s(B, B * ctx, hw_d)
    tput = B / step
    D = math.ceil(rate * mo / (rho_max * tput))
    return {"P": P, "D": D, "mean_prefill_s": t_pf, "mean_prompt": float(mp), "mean_output": float(mo), "decode_batch": B, "decode_step_s": step,
            "decode_tok_per_s_per_instance": tput, "kv_GBps_total": rate * mp * kv_cache_bytes(1) / 1e9,
            "gpus": (P * hw_p["gpus_per_instance"]) + (D * hw_d["gpus_per_instance"])}


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
    kv = rate_rps * sizing["mean_prompt"] * kv_cache_bytes(1) / 1e9
    u = {"prefill": rate_rps * sizing["mean_prefill_s"] / P,
         "decode": rate_rps * mean_output / (D * sizing["decode_tok_per_s_per_instance"]),
         "network_out": kv / P / link_GBps, "network_in": kv / D / link_GBps}
    u["network"] = max(u["network_out"], u["network_in"])
    u["bottleneck"] = max(("prefill", "decode", "network"), key=lambda k: u[k])
    return u


# --------------------------------------------------------------------------- T5 admission
def admission_policy(req: dict[str, Any], state: dict[str, Any], hw_p: dict[str, Any] | None = None,
                     slo: dict[str, Any] | None = None) -> str:
    """Admit or reject one request at arrival (called by the simulator).

    ``state['prefill_backlog_s']`` = mean queued prefill seconds per prefill instance. Predicted
    TTFT = backlog + prefill_time_s(prompt). Reject when it exceeds 90 % of the applicable SLO
    (short prompts: ttft_p95_s; prompts above ttft_applies_to_prompt_tokens_max: ttft_long_p95_s).
    """
    from sim.serving_sim import DEFAULTS  # same efficiency defaults the simulator uses
    hw_p = hw_p or DEFAULTS
    slo = slo or {"ttft_p95_s": 0.8, "ttft_long_p95_s": 3.0, "ttft_applies_to_prompt_tokens_max": 4096}
    limit = slo["ttft_p95_s"] if req["prompt"] <= slo["ttft_applies_to_prompt_tokens_max"] else slo["ttft_long_p95_s"]
    pred = state["prefill_backlog_s"] + prefill_time_s(int(req["prompt"]), hw_p)
    return "reject" if pred > 0.9 * limit else "admit"


# --------------------------------------------------------------------------- T6 speculative decoding
def speculative_gain(alpha: float, k: int, c: float) -> dict[str, float]:
    """Speculative decoding with acceptance rate α, k draft tokens, draft/target step cost ratio c.

    Expected tokens per target step E = (1 − α^(k+1)) / (1 − α) (Leviathan et al., 2023);
    cost per target step = 1 + k·c; speedup = E / (1 + k·c). (Memory-bound regime: the target
    verifies k+1 tokens for about the cost of one step; at large batch this assumption weakens.)
    """
    e = (1 - alpha ** (k + 1)) / (1 - alpha) if alpha < 1 else k + 1
    return {"tokens_per_target_step": e, "speedup": e / (1 + k * c)}


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
    mem = (MODEL["weights_GB"] * 1e9 + ctx_tokens_total * kv_cache_bytes(1)) / (
        hw["gpus_per_instance"] * hw["hbm_TBps"] * 1e12 * hw["hbm_eff"])
    flops_rate = hw["gpus_per_instance"] * hw["peak_TFLOPs"] * 1e12 * decode_mfu
    plain = max(2 * MODEL["params"] * batch / flops_rate, mem) + hw["step_overhead_s"]
    verify = max(2 * MODEL["params"] * batch * (k + 1) / flops_rate, mem) + hw["step_overhead_s"]
    e = speculative_gain(alpha, k, c)["tokens_per_target_step"]
    return {"tokens_per_target_step": e, "plain_step_s": plain, "verify_step_s": verify,
            "speedup": e * plain / (verify + k * c * plain)}


def best_draft_length(alpha: float, c: float, k_max: int = 8) -> int:
    """k in 1..k_max with the highest speedup (smallest k on ties)."""
    return max(range(1, k_max + 1), key=lambda k: (round(speculative_gain(alpha, k, c)["speedup"], 9), -k))


# --------------------------------------------------------------------------- T7 QoS audit
def audit_qos(qos: dict[str, Any]) -> list[str]:
    """Return sorted finding codes for the proposed QoS/isolation design.

    kv_dscp_collision                 KV traffic uses the same DSCP as training RoCE (cannot be told apart)
    kv_shares_lossless_training_tc    KV mapped to the training lossless traffic class
    cnp_not_strict_priority           CNP class missing or not strict priority
    kv_unencrypted_across_boundary    KV crosses a tenant boundary with kv_encryption 'none'
    kv_no_ecn                         KV class without ECN marking
    """
    cls = {c["name"]: c for c in qos["classes"]}
    kv, tr, cnp = cls.get("kv-transfer"), cls.get("training-roce"), cls.get("cnp")
    f = []
    if kv and tr and kv["dscp"] == tr["dscp"]:
        f.append("kv_dscp_collision")
    if kv and tr and kv["tc"] == tr["tc"]:
        f.append("kv_shares_lossless_training_tc")
    if not cnp or not cnp.get("strict_priority"):
        f.append("cnp_not_strict_priority")
    if qos.get("kv_path_crosses_tenant_boundary") and qos.get("kv_encryption", "none") == "none":
        f.append("kv_unencrypted_across_boundary")
    if kv and not kv.get("ecn"):
        f.append("kv_no_ecn")
    return sorted(f)


# --------------------------------------------------------------------------- T8 cost
def cost_per_million_tokens(gpus: int, usd_per_gpu_hour: float, output_tok_per_s: float) -> float:
    """USD per 1,000,000 output tokens = gpus × $/GPU-h / (tokens/s × 3,600) × 1e6."""
    return gpus * usd_per_gpu_hour / (output_tok_per_s * 3600) * 1e6
