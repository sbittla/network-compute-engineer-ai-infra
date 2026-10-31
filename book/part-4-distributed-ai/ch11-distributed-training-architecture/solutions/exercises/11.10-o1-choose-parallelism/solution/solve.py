"""11.10 — Memory and dominant traffic for three workloads.

Usage: python solve.py --out DIR      Evidence label: [MODELED] (assumptions [ILLUSTRATIVE], Table 11.4)
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import yaml

# --- W-TRAIN step-time and memory model (Chapter 11, Sections 11.2-11.5 and 11.10; Table 11.4) ---
# Independent re-implementation of the chapter's formulas. Bytes are SI (1 GB = 1e9 B).
DATA = Path(__file__).resolve().parents[4] / "lab" / "data"


def load() -> tuple[dict, dict]:
    model = yaml.safe_load((DATA / "model_wtrain.yaml").read_text(encoding="utf-8"))
    cluster = yaml.safe_load((DATA / "cluster_orion.yaml").read_text(encoding="utf-8"))
    return model, cluster


def n_micro(model: dict, cfg: dict) -> int:
    return int(model["global_batch_seqs"] // (cfg["dp"] * cfg["micro_batch"]))


def memory(model: dict, cluster: dict, cfg: dict) -> dict:
    tp, pp, dp, b, z = cfg["tp"], cfg["pp"], cfg["dp"], cfg["micro_batch"], cfg["zero_stage"]
    p_local = model["params"] / (tp * pp)
    w = 2 * p_local / (dp if z >= 3 else 1)
    g = 2 * p_local / (dp if z >= 2 else 1)
    o = 12 * p_local / (dp if z >= 1 else 1)
    per_layer = model["seq_len"] * b * model["hidden"] * (34 if cfg["recompute"] == "selective" else 2) / tp
    m = n_micro(model, cfg)
    in_flight = min(pp, m) if pp > 1 else 1
    act = per_layer * (model["layers"] // pp) * in_flight
    out = {"params_per_gpu": p_local, "weights_gb": w / 1e9, "grads_gb": g / 1e9, "optimizer_gb": o / 1e9,
           "act_per_layer_mb": per_layer / 1e6, "in_flight": in_flight, "activations_gb": act / 1e9,
           "overhead_gb": float(cluster["fixed_overhead_gb"])}
    out["states_gb"] = out["weights_gb"] + out["grads_gb"] + out["optimizer_gb"]
    out["total_gb"] = out["states_gb"] + out["activations_gb"] + out["overhead_gb"]
    return out


def allreduce_s(payload: float, group: int, per_node: int, cluster: dict) -> float:
    if group <= 1:
        return 0.0
    nvl, rail = cluster["nvlink_busbw_gbs"] * 1e9, cluster["rail_busbw_gbs"] * 1e9
    k = max(1, min(per_node, group))
    nodes = math.ceil(group / k)
    if nodes == 1:
        return 2 * (group - 1) / group * payload / nvl
    intra = 2 * (k - 1) / k * payload / nvl if k > 1 else 0.0
    return intra + 2 * (nodes - 1) / nodes * (payload / k) / rail


def comm(model: dict, cluster: dict, cfg: dict) -> dict:
    tp, pp, dp, b, z = cfg["tp"], cfg["pp"], cfg["dp"], cfg["micro_batch"], cfg["zero_stage"]
    gpn = cluster["gpus_per_node"]
    m = n_micro(model, cfg)
    msg = model["seq_len"] * b * model["hidden"] * model["act_bytes"]
    lat_nvl, lat_net = cluster["nvlink_latency_us"] * 1e-6, cluster["internode_latency_us"] * 1e-6
    n_tp = 4 * (model["layers"] // pp) * m if tp > 1 else 0
    tp_bytes = n_tp * 2 * (tp - 1) / tp * msg if tp > 1 else 0.0
    tp_lat = lat_net * 2 if tp > gpn else lat_nvl
    tp_t = n_tp * (allreduce_s(msg, tp, min(tp, gpn), cluster) + tp_lat) if tp > 1 else 0.0
    grad = 2 * model["params"] / (tp * pp)
    dp_node = max(1, min(dp, gpn // tp)) if tp < gpn else 1
    if dp > 1:
        eq, ncoll = (1.5 * m, 3 * m) if z >= 3 else (1.0, 2)
        dp_bytes = eq * 2 * (dp - 1) / dp * grad
        dp_t = eq * allreduce_s(grad, dp, dp_node, cluster) + ncoll * (lat_net if dp_node < dp else lat_nvl)
    else:
        dp_bytes = dp_t = 0.0
    if pp > 1:
        inter = tp * dp >= gpn
        bw = (cluster["rail_busbw_gbs"] if inter else cluster["nvlink_busbw_gbs"]) * 1e9
        pp_bytes = 2 * m * msg / tp
        pp_t = pp_bytes / bw + 2 * m * (lat_net if inter else lat_nvl)
    else:
        pp_bytes = pp_t = 0.0
    return {"m": m, "msg_bytes": msg, "tp_collectives": n_tp, "tp_bytes": tp_bytes, "tp_s": tp_t,
            "dp_bytes": dp_bytes, "dp_s": dp_t, "pp_bytes": pp_bytes, "pp_s": pp_t}


def step(model: dict, cluster: dict, cfg: dict) -> dict:
    world = cfg["tp"] * cfg["pp"] * cfg["dp"]
    tokens = model["global_batch_seqs"] * model["seq_len"]
    useful = 6 * model["params"] * tokens
    rf = cluster["full_recompute_factor"] if cfg["recompute"] == "full" else 1.0
    peak = cluster["peak_bf16_tflops"] * 1e12
    compute = useful / world * rf / (peak * cluster["kernel_efficiency"])
    c = comm(model, cluster, cfg)
    bubble = compute * (cfg["pp"] - 1) / c["m"] if cfg["pp"] > 1 else 0.0
    ex_tp = c["tp_s"] * (1 - cluster["overlap_tp"])
    window = compute if cfg["zero_stage"] >= 3 else compute / c["m"] * cluster["backward_fraction"]
    ex_dp = max(0.0, c["dp_s"] - window)
    ex_pp = c["pp_s"] * (1 - cluster["overlap_pp"])
    total = compute + bubble + ex_tp + ex_dp + ex_pp
    return {"compute_s": compute, "bubble_s": bubble, "bubble_fraction": (cfg["pp"] - 1) / (c["m"] + cfg["pp"] - 1),
            "tp_s": c["tp_s"], "exposed_tp_s": ex_tp, "dp_s": c["dp_s"], "dp_window_s": window,
            "exposed_dp_s": ex_dp, "pp_s": c["pp_s"], "exposed_pp_s": ex_pp, "step_s": total,
            "ideal_s": useful / (world * peak), "mfu": useful / (world * peak * total)}


BASELINE = {"tp": 8, "pp": 4, "dp": 8, "micro_batch": 1, "zero_stage": 1, "recompute": "selective"}


# --- end of model ---


def rnd(obj, nd: int = 4):
    """Round floats for deterministic output: 4 significant digits for very large/small, else nd decimals."""
    if isinstance(obj, bool) or obj is None:
        return obj
    if isinstance(obj, float):
        if obj != obj:
            return None
        return float(f"{obj:.{nd}g}") if abs(obj) >= 1e6 or (obj != 0 and abs(obj) < 1e-3) else round(obj, nd)
    if isinstance(obj, dict):
        return {str(k): rnd(v, nd) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [rnd(v, nd) for v in obj]
    return obj


def emit(out: Path, result: dict, md: str) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(rnd(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "result.md").write_text(md.strip() + "\n", encoding="utf-8")
    print(md)

GPN = 8


def case_a(cluster: dict) -> dict:
    n, s, gb, gpus, h, layers, b = 1.3e9, 2048, 512, 64, 2048, 24, 4
    states = 16 * n / 1e9
    act_seq = s * h * 34 * layers / 1e9           # GB per sequence (TP = 1)
    act = act_seq * b
    total = states + act + cluster["fixed_overhead_gb"]
    grad = 2 * n
    sent = 2 * (gpus - 1) / gpus * grad
    nodes = gpus // GPN
    t = (2 * (GPN - 1) / GPN * grad / (cluster["nvlink_busbw_gbs"] * 1e9)
         + 2 * (nodes - 1) / nodes * (grad / GPN) / (cluster["rail_busbw_gbs"] * 1e9))
    compute = 6 * n * gb * s / gpus / (cluster["peak_bf16_tflops"] * 1e12 * cluster["kernel_efficiency"])
    return {"layout": "DP=64 (DDP or ZeRO-1), b=4 x 2 accumulation", "states_gb": states, "act_gb": act,
            "total_gb": total, "dp_payload_gb": grad / 1e9, "dp_sent_gb": sent / 1e9, "dp_time_s": t,
            "compute_s": compute}


def case_b(model: dict, cluster: dict) -> dict:
    m = dict(model, global_batch_seqs=256)
    cfg = {"tp": 8, "pp": 4, "dp": 2, "micro_batch": 1, "zero_stage": 1, "recompute": "selective"}
    mem, c = memory(m, cluster, cfg), comm(m, cluster, cfg)
    alt = dict(cfg, tp=4, pp=8)
    mem_alt, c_alt = memory(m, cluster, alt), comm(m, cluster, alt)
    return {"layout": "TP8 PP4 DP2 ZeRO-1", "states_gb": mem["states_gb"], "act_gb": mem["activations_gb"],
            "total_gb": mem["total_gb"], "tp_bytes": c["tp_bytes"], "dp_bytes": c["dp_bytes"], "dp_time_s": c["dp_s"],
            "pp_bytes": c["pp_bytes"], "alt_tp4_pp8_total_gb": mem_alt["total_gb"], "alt_tp_bytes": c_alt["tp_bytes"]}


def case_c(model: dict, cluster: dict) -> dict:
    m = dict(model, seq_len=65536, global_batch_seqs=32)
    sel = {"tp": 8, "pp": 4, "dp": 1, "micro_batch": 1, "zero_stage": 1, "recompute": "selective"}
    full = dict(sel, recompute="full")
    mem_sel, mem_full, c = memory(m, cluster, sel), memory(m, cluster, full), comm(m, cluster, full)
    tp_with_recompute = c["tp_bytes"] * 1.5
    return {"layout": "TP8 PP4 DP1 full recompute", "selective_act_gb": mem_sel["activations_gb"],
            "full_act_per_layer_mb": mem_full["act_per_layer_mb"], "act_gb": mem_full["activations_gb"],
            "states_gb": mem_full["states_gb"], "total_gb": mem_full["total_gb"],
            "tp_msg_gb": c["msg_bytes"] / 1e9, "tp_bytes": c["tp_bytes"], "tp_bytes_with_recompute": tp_with_recompute,
            "tp_time_s_at_nvlink": tp_with_recompute / (cluster["nvlink_busbw_gbs"] * 1e9),
            "pp_bytes": c["pp_bytes"], "bubble": (4 - 1) / (c["m"] + 4 - 1)}


def solve() -> dict:
    model, cluster = load()
    return {"inputs": {"planning_limit_gb": cluster["hbm_gb"] * cluster["hbm_headroom_fraction"]},
            "a": case_a(cluster), "b": case_b(model, cluster), "c": case_c(model, cluster),
            "units": {"memory": "GB", "bytes": "B per GPU per step", "time": "s"}, "evidence_label": "[MODELED]"}


def check(r: dict) -> None:
    a, b, c = r["a"], r["b"], r["c"]
    lim = r["inputs"]["planning_limit_gb"]
    # Key 11.10 values (tolerance ~1 %): (a) 20.8 + 13.7 -> ~38 GB, 2.6 GB grads, 0.028 s vs 0.26 s compute.
    assert abs(a["states_gb"] - 20.8) < 0.05 and abs(a["act_gb"] - 13.7) < 0.05 and a["total_gb"] < lim
    assert abs(a["dp_time_s"] - 0.028) < 0.001 and abs(a["compute_s"] - 0.26) < 0.005
    # (b) 21.9 + 11.4 + 4 = 37.3 GB; TP 1.2 TB; DP 4.4 GB; PP 2.15 GB; alt 48.7 GB and 515 GB.
    assert abs(b["total_gb"] - 37.3) < 0.1 and abs(b["tp_bytes"] / 1.2026e12 - 1) < 0.005
    assert abs(b["dp_bytes"] / 4.375e9 - 1) < 0.005 and abs(b["pp_bytes"] / 2.147e9 - 1) < 0.005
    assert abs(b["alt_tp4_pp8_total_gb"] - 48.7) < 0.1 and abs(b["alt_tp_bytes"] / 515e9 - 1) < 0.005
    # (c) selective 182 GB; full 10.7 GB act, 35 GB states, ~50 GB; TP 4.8 TB (7.2 TB with recompute, ~24 s); PP 8.6 GB.
    assert abs(c["selective_act_gb"] - 182.5) < 0.5 and c["selective_act_gb"] > 80
    assert abs(c["act_gb"] - 10.7) < 0.05 and abs(c["states_gb"] - 35.0) < 0.01 and c["total_gb"] < lim
    assert abs(c["tp_bytes"] / 4.81e12 - 1) < 0.01 and abs(c["tp_time_s_at_nvlink"] - 24.0) < 0.2
    assert abs(c["pp_bytes"] / 8.59e9 - 1) < 0.01 and abs(c["bubble"] - 3 / 35) < 1e-9


def report(r: dict) -> str:
    a, b, c = r["a"], r["b"], r["c"]
    return f"""# 11.10 (O1) — Three workloads `[MODELED]`

| Case | Layout | States (GB) | Activations (GB) | Total (GB) | Dominant traffic per GPU per step |
|---|---|---|---|---|---|
| (a) | {a['layout']} | {a['states_gb']:.1f} | {a['act_gb']:.1f} | {a['total_gb']:.1f} | DP all-reduce of {a['dp_payload_gb']:.1f} GB ({a['dp_sent_gb']:.1f} GB sent, {a['dp_time_s']:.3f} s vs {a['compute_s']:.2f} s compute) |
| (b) | {b['layout']} | {b['states_gb']:.1f} | {b['act_gb']:.1f} | {b['total_gb']:.1f} | TP {b['tp_bytes'] / 1e12:.2f} TB (NVLink); DP {b['dp_bytes'] / 1e9:.2f} GB, PP {b['pp_bytes'] / 1e9:.2f} GB (rail) |
| (c) | {c['layout']} | {c['states_gb']:.1f} | {c['act_gb']:.1f} | {c['total_gb']:.1f} | TP {c['tp_bytes'] / 1e12:.2f} TB ({c['tp_bytes_with_recompute'] / 1e12:.1f} TB with recompute, {c['tp_time_s_at_nvlink']:.1f} s on NVLink); PP {c['pp_bytes'] / 1e9:.1f} GB (rail) |

(c) with selective recompute would need {c['selective_act_gb']:.0f} GB of activations: impossible.
(b) alternative TP4/PP8/DP2: {b['alt_tp4_pp8_total_gb']:.1f} GB, TP {b['alt_tp_bytes'] / 1e9:.0f} GB.
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    out = ap.parse_args().out
    r = solve()
    check(r)
    emit(out, r, report(r))


if __name__ == "__main__":
    main()
