"""Step-time, memory, and checkpoint-interval model for W-TRAIN on ORION (reference solution).

Every value this module produces is [MODELED]: it follows from the formulas in Chapter 11 and the
[ILLUSTRATIVE] efficiency assumptions in ``data/cluster_orion.yaml``. It is a planning tool, not a
measurement.

Conventions
-----------
* Bytes are SI (1 GB = 1e9 B); times are seconds unless a name ends in ``_us``.
* Communication volumes are *per GPU per optimizer step* and count the bytes each GPU sends.
* Rank order is Megatron-style: TP fastest, then DP, then PP. With TP = 8 on 8-GPU nodes, a TP group
  is exactly one node and every DP/PP peer of a GPU has the same local index (same rail).
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

Config = dict[str, Any]


# ----------------------------------------------------------------------------------------- inputs
def load_inputs(data_dir: Path) -> tuple[dict, dict, pd.DataFrame, pd.DataFrame]:
    """Load (model, cluster, candidates, reliability) from ``data_dir``."""
    data_dir = Path(data_dir)
    with open(data_dir / "model_wtrain.yaml", encoding="utf-8") as f:
        model = yaml.safe_load(f)
    with open(data_dir / "cluster_orion.yaml", encoding="utf-8") as f:
        cluster = yaml.safe_load(f)
    cands = pd.read_csv(data_dir / "candidates.csv")
    rel = pd.read_csv(data_dir / "reliability_scenarios.csv")
    return model, cluster, cands, rel


# ------------------------------------------------------------------------------------- structure
def micro_batches_per_step(model: dict, cfg: Config) -> int:
    """Micro-batches each pipeline processes per step: m = global_batch / (dp * micro_batch)."""
    return int(model["global_batch_seqs"] // (cfg["dp"] * cfg["micro_batch"]))


def validate_config(model: dict, cluster: dict, cfg: Config) -> list[str]:
    """Return structural problems with ``cfg`` (empty list = structurally valid).

    Reasons (stable strings, used by the checker):
      ``world_size_mismatch``            tp*pp*dp != cluster GPUs
      ``layers_not_divisible_by_pp``     layers % pp != 0
      ``kv_heads_not_divisible_by_tp``   GQA KV heads must split evenly across TP ranks
      ``batch_not_divisible``            global batch % (dp*micro_batch) != 0
      ``tp_spans_nodes``                 TP group larger than one NVLink domain (node)
    """
    reasons: list[str] = []
    tp, pp, dp, b = cfg["tp"], cfg["pp"], cfg["dp"], cfg["micro_batch"]
    if tp * pp * dp != cluster["gpus"]:
        reasons.append("world_size_mismatch")
    if model["layers"] % pp != 0:
        reasons.append("layers_not_divisible_by_pp")
    if model["kv_heads"] % tp != 0:
        reasons.append("kv_heads_not_divisible_by_tp")
    if model["global_batch_seqs"] % (dp * b) != 0:
        reasons.append("batch_not_divisible")
    if tp > cluster["gpus_per_node"]:
        reasons.append("tp_spans_nodes")
    return reasons


def bubble_fraction(pp: int, m: int) -> float:
    """1F1B / GPipe pipeline bubble fraction of total pipeline time: (p-1)/(m+p-1)."""
    if pp <= 1:
        return 0.0
    return (pp - 1) / (m + pp - 1)


# ---------------------------------------------------------------------------------------- memory
def memory_per_gpu(model: dict, cluster: dict, cfg: Config) -> dict[str, float]:
    """Per-GPU memory in GB (1e9 B) for the most loaded pipeline stage (stage 0 under 1F1B).

    Model-state bytes per local parameter P = N/(tp*pp):
      weights 2 B, gradients 2 B, optimizer 12 B (fp32 master + Adam m + v);
      ZeRO-1 shards optimizer over DP, ZeRO-2 also gradients, ZeRO-3 also weights.
    Activations per layer per micro-batch (Korthikanti et al., 2022, with sequence parallelism):
      selective recompute: s*b*h*34/tp bytes;  full recompute: s*b*h*2/tp bytes (layer input only).
    In-flight micro-batches on stage 0 under 1F1B: min(pp, m) (1 when pp == 1).
    ZeRO-3 adds a gather buffer of two full layers of BF16 weights (current + prefetch).

    Returns keys: params_per_gpu, weights_gb, grads_gb, optimizer_gb, activations_gb,
    zero3_gather_gb, overhead_gb (= cluster fixed_overhead_gb), total_gb (sum of the *_gb keys).
    """
    tp, pp, dp, b, z = cfg["tp"], cfg["pp"], cfg["dp"], cfg["micro_batch"], int(cfg["zero_stage"])
    n, layers = model["params"], model["layers"]
    p_local = n / (tp * pp)
    w = 2 * p_local / (dp if z >= 3 else 1)
    g = 2 * p_local / (dp if z >= 2 else 1)
    o = 12 * p_local / (dp if z >= 1 else 1)
    sbh = model["seq_len"] * b * model["hidden"]
    per_layer = sbh * (34 if cfg["recompute"] == "selective" else 2) / tp
    m = micro_batches_per_step(model, cfg)
    in_flight = min(pp, m) if pp > 1 else 1
    act = per_layer * (layers // pp) * in_flight
    gather = 2 * (n / layers) * 2 / tp if z >= 3 else 0.0
    out = {
        "params_per_gpu": p_local,
        "weights_gb": w / 1e9,
        "grads_gb": g / 1e9,
        "optimizer_gb": o / 1e9,
        "activations_gb": act / 1e9,
        "zero3_gather_gb": gather / 1e9,
        "overhead_gb": float(cluster["fixed_overhead_gb"]),
    }
    out["total_gb"] = sum(v for k, v in out.items() if k.endswith("_gb"))
    return out


# ------------------------------------------------------------------------------- communication
def allreduce_time_s(payload_b: float, group: int, per_node: int, cluster: dict) -> float:
    """Bandwidth term of one all-reduce of ``payload_b`` bytes over ``group`` GPUs.

    ``per_node`` group members share a node. Single node: ring over NVLink, 2(g-1)/g * S / B_nvl.
    Multi-node: hierarchical (intra-node reduce-scatter/all-gather on NVLink, then an inter-node
    ring of each GPU's S/k slice over its own rail NIC), phases not pipelined:
        2(k-1)/k * S / B_nvl  +  2(N-1)/N * (S/k) / B_rail
    """
    if group <= 1:
        return 0.0
    nvl = cluster["nvlink_busbw_gbs"] * 1e9
    rail = cluster["rail_busbw_gbs"] * 1e9
    k = max(1, min(per_node, group))
    nodes = math.ceil(group / k)
    if nodes == 1:
        return 2 * (group - 1) / group * payload_b / nvl
    intra = 2 * (k - 1) / k * payload_b / nvl if k > 1 else 0.0
    inter = 2 * (nodes - 1) / nodes * (payload_b / k) / rail
    return intra + inter


def comm_model(model: dict, cluster: dict, cfg: Config) -> dict[str, float]:
    """Per-GPU, per-step communication volumes (bytes sent) and times (s) by parallelism type.

    TP (Megatron + sequence parallelism): 4 all-reduce-equivalents per layer per micro-batch
      (2 forward, 2 backward), payload s*b*h*2 B.
    DP: gradient reduction once per step (ZeRO 0/1/2: one all-reduce-equivalent of 2 B * P_local).
      ZeRO-3/FSDP: per micro-batch an all-gather (fwd), all-gather (bwd), reduce-scatter (grads)
      = 1.5 all-reduce-equivalents per micro-batch.
    PP: per micro-batch each stage sends activations forward and gradients backward, s*b*h*2/tp B
      each (sequence-parallel slice per TP rank); inter-node (rail) when tp*dp >= gpus_per_node.
    Each collective/message also pays a fixed latency (NVLink or inter-node; TP across nodes pays
    two inter-node latencies per collective). DP members per node = min(dp, gpus_per_node // tp)
    when tp < gpus_per_node, else 1.

    Returns keys: micro_batches, tp_collectives, tp_bytes, tp_time_s, tp_spans_nodes, dp_bytes,
    dp_time_s, pp_bytes, pp_time_s.
    """
    tp, pp, dp, b, z = cfg["tp"], cfg["pp"], cfg["dp"], cfg["micro_batch"], int(cfg["zero_stage"])
    gpn = cluster["gpus_per_node"]
    m = micro_batches_per_step(model, cfg)
    sbh2 = model["seq_len"] * b * model["hidden"] * model["act_bytes"]
    layers_stage = model["layers"] // pp
    lat_nvl = cluster["nvlink_latency_us"] * 1e-6
    lat_net = cluster["internode_latency_us"] * 1e-6

    # Tensor parallel
    tp_colls = 4 * layers_stage * m if tp > 1 else 0
    tp_bytes = tp_colls * 2 * (tp - 1) / tp * sbh2 if tp > 1 else 0.0
    tp_spans = tp > gpn
    tp_lat = (lat_net * 2 if tp_spans else lat_nvl)
    tp_time = tp_colls * (allreduce_time_s(sbh2, tp, min(tp, gpn), cluster) + tp_lat) if tp > 1 else 0.0

    # Data parallel
    p_local = model["params"] / (tp * pp)
    grad_b = 2 * p_local
    dp_per_node = max(1, min(dp, gpn // tp)) if tp < gpn else 1
    if dp > 1:
        if z >= 3:
            ar_equiv, n_colls = 1.5 * m, 3 * m
        else:
            ar_equiv, n_colls = 1.0, 2
        dp_bytes = ar_equiv * 2 * (dp - 1) / dp * grad_b
        dp_lat = lat_net if dp_per_node < dp else lat_nvl
        dp_time = ar_equiv * allreduce_time_s(grad_b, dp, dp_per_node, cluster) + n_colls * dp_lat
    else:
        dp_bytes, dp_time = 0.0, 0.0

    # Pipeline parallel
    if pp > 1:
        msg = sbh2 / tp
        pp_bytes = 2 * m * msg
        inter = tp * dp >= gpn
        bw = (cluster["rail_busbw_gbs"] if inter else cluster["nvlink_busbw_gbs"]) * 1e9
        pp_time = pp_bytes / bw + 2 * m * (lat_net if inter else lat_nvl)
    else:
        pp_bytes, pp_time = 0.0, 0.0

    return {
        "micro_batches": m,
        "tp_collectives": tp_colls,
        "tp_bytes": tp_bytes,
        "tp_time_s": tp_time,
        "tp_spans_nodes": tp_spans,
        "dp_bytes": dp_bytes,
        "dp_time_s": dp_time,
        "pp_bytes": pp_bytes,
        "pp_time_s": pp_time,
    }


# ------------------------------------------------------------------------------------- step time
def step_time(model: dict, cluster: dict, cfg: Config) -> dict[str, float]:
    """Modeled step time (s) = compute + bubble + exposed TP + exposed DP + exposed PP.

    compute = 6*N*tokens/world * recompute_factor / (peak * kernel_efficiency)
    bubble  = compute * (p-1)/m          (so compute+bubble = compute*(m+p-1)/m)
    exposed_tp = tp_time * (1 - overlap_tp);  exposed_pp = pp_time * (1 - overlap_pp)
    exposed_dp = max(0, dp_time - dp_window), where the DP reduction can hide only behind
        the last micro-batch's backward pass: dp_window = compute / m * backward_fraction
        (ZeRO-3/FSDP prefetches per layer, so its window is the whole compute time)
    MFU     = 6*N*tokens / (world * peak * step)   (recompute FLOPs are not "useful")

    Returns keys: compute_s, bubble_s, bubble_fraction, tp_comm_s, dp_comm_s, dp_window_s,
    exposed_dp_s, pp_comm_s, exposed_comm_s, step_s, mfu, tokens_per_s.
    """
    world = cfg["tp"] * cfg["pp"] * cfg["dp"]
    tokens = model["global_batch_seqs"] * model["seq_len"]
    useful = 6 * model["params"] * tokens
    rf = cluster["full_recompute_factor"] if cfg["recompute"] == "full" else 1.0
    peak = cluster["peak_bf16_tflops"] * 1e12
    compute = useful / world * rf / (peak * cluster["kernel_efficiency"])
    c = comm_model(model, cluster, cfg)
    m = c["micro_batches"]
    bubble = compute * (cfg["pp"] - 1) / m if cfg["pp"] > 1 else 0.0
    ex_tp = c["tp_time_s"] * (1 - cluster["overlap_tp"])
    if int(cfg["zero_stage"]) >= 3:
        dp_window = compute
    else:
        dp_window = compute / m * cluster["backward_fraction"]
    ex_dp = max(0.0, c["dp_time_s"] - dp_window)
    ex_pp = c["pp_time_s"] * (1 - cluster["overlap_pp"])
    step = compute + bubble + ex_tp + ex_dp + ex_pp
    return {
        "compute_s": compute,
        "bubble_s": bubble,
        "bubble_fraction": bubble_fraction(cfg["pp"], m),
        "tp_comm_s": c["tp_time_s"],
        "dp_comm_s": c["dp_time_s"],
        "dp_window_s": dp_window,
        "exposed_dp_s": ex_dp,
        "pp_comm_s": c["pp_time_s"],
        "exposed_comm_s": ex_tp + ex_dp + ex_pp,
        "step_s": step,
        "mfu": useful / (world * peak * step),
        "tokens_per_s": tokens / step,
    }


def evaluate_candidates(model: dict, cluster: dict, cands: pd.DataFrame) -> pd.DataFrame:
    """One row per candidate with memory, timing, validity reasons and a feasibility verdict.

    feasible == structurally valid (no reasons) AND total_gb <= hbm_gb * hbm_headroom_fraction.
    ``fits_hbm`` reports the raw 80 GB test separately so "fits but violates headroom" is visible.
    """
    rows = []
    for rec in cands.to_dict("records"):
        cfg = {k: rec[k] for k in ("tp", "pp", "dp", "micro_batch", "zero_stage", "recompute")}
        reasons = validate_config(model, cluster, cfg)
        mem = memory_per_gpu(model, cluster, cfg)
        st = step_time(model, cluster, cfg)
        c = comm_model(model, cluster, cfg)
        limit = cluster["hbm_gb"] * cluster["hbm_headroom_fraction"]
        if mem["total_gb"] > cluster["hbm_gb"]:
            reasons.append("hbm_overflow")
        elif mem["total_gb"] > limit:
            reasons.append("exceeds_headroom")
        rows.append({
            "name": rec["name"], **cfg,
            "micro_batches": c["micro_batches"],
            "mem_total_gb": mem["total_gb"],
            "mem_states_gb": mem["weights_gb"] + mem["grads_gb"] + mem["optimizer_gb"],
            "mem_act_gb": mem["activations_gb"],
            "fits_hbm": mem["total_gb"] <= cluster["hbm_gb"],
            "tp_GB": c["tp_bytes"] / 1e9, "dp_GB": c["dp_bytes"] / 1e9, "pp_GB": c["pp_bytes"] / 1e9,
            **{k: st[k] for k in ("compute_s", "bubble_fraction", "bubble_s", "tp_comm_s", "dp_comm_s",
                                  "pp_comm_s", "exposed_comm_s", "step_s", "mfu")},
            "reasons": ";".join(reasons),
            "feasible": len(reasons) == 0,
        })
    return pd.DataFrame(rows).sort_values("step_s").reset_index(drop=True)


def recommend(table: pd.DataFrame) -> str:
    """Name of the feasible candidate with the lowest modeled step time."""
    ok = table[table["feasible"]]
    if ok.empty:
        raise ValueError("no feasible candidate")
    return str(ok.sort_values("step_s").iloc[0]["name"])


# ------------------------------------------------------------------------------ checkpointing
def young_daly_interval_s(checkpoint_s: float, mtbf_s: float) -> float:
    """First-order optimum checkpoint interval (Young 1974; Daly 2006): sqrt(2*C*MTBF)."""
    return math.sqrt(2.0 * checkpoint_s * mtbf_s)


def waste_fraction(interval_s: float, checkpoint_s: float, restart_s: float, mtbf_s: float) -> float:
    """First-order fraction of wall time lost: C/tau + (tau/2 + R)/MTBF.

    C/tau is checkpoint overhead; each failure (rate 1/MTBF) loses on average half an interval of
    work plus the restart time R. Valid when C, R << tau << MTBF.
    """
    return checkpoint_s / interval_s + (interval_s / 2.0 + restart_s) / mtbf_s


def expected_lost_work_s(interval_s: float, restart_s: float) -> float:
    """Expected wall time lost per failure: half an interval of recomputation plus restart."""
    return interval_s / 2.0 + restart_s


def reliability_table(rel: pd.DataFrame) -> pd.DataFrame:
    """Checkpoint plan per scenario: tau_opt, waste at tau_opt and at a naive 4 h interval,
    failures/day, and GPU-hours lost per failure and per day.

    The first-order waste formula is invalid once the interval approaches MTBF: waste is reported
    as NaN with valid_* = False when interval >= MTBF. p_interval_completes_4h = exp(-4 h / MTBF)
    is the probability that a 4 h interval finishes without a failure (exponential failures)."""
    rows = []
    for r in rel.to_dict("records"):
        mtbf = r["job_mtbf_hours"] * 3600.0
        c, rs = r["checkpoint_blocking_s"], r["restart_s"]
        tau = young_daly_interval_s(c, mtbf)
        naive = 4 * 3600.0
        lost = expected_lost_work_s(tau, rs)
        fpd = 86400.0 / mtbf
        rows.append({
            "name": r["name"], "gpus": r["gpus"],
            "tau_opt_s": tau, "tau_opt_min": tau / 60.0,
            "waste_at_opt": waste_fraction(tau, c, rs, mtbf) if tau < mtbf else float("nan"),
            "valid_at_opt": tau < mtbf,
            "waste_at_4h": waste_fraction(naive, c, rs, mtbf) if naive < mtbf else float("nan"),
            "valid_at_4h": naive < mtbf,
            "p_interval_completes_4h": math.exp(-naive / mtbf),
            "failures_per_day": fpd,
            "lost_s_per_failure": lost,
            "lost_gpu_h_per_failure": lost / 3600.0 * r["gpus"],
            "lost_gpu_h_per_day": (lost / 3600.0 * r["gpus"]) * fpd,
        })
    return pd.DataFrame(rows)


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="W-TRAIN step-time / memory / checkpoint model")
    ap.add_argument("--data", type=Path, default=Path(__file__).resolve().parents[2] / "lab" / "data")
    args = ap.parse_args()
    model, cluster, cands, rel = load_inputs(args.data)
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 40)
    t = evaluate_candidates(model, cluster, cands)
    print(t[["name", "mem_total_gb", "mem_act_gb", "micro_batches", "bubble_fraction", "compute_s",
             "tp_comm_s", "dp_comm_s", "pp_comm_s", "exposed_comm_s", "step_s", "mfu", "reasons"]]
          .round(3).to_string(index=False))
    print("\nrecommended:", recommend(t))
    print()
    print(reliability_table(rel).round(4).to_string(index=False))


if __name__ == "__main__":
    main()
