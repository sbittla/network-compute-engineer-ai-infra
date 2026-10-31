"""11.15 — Memory and step time of candidate layouts at sequence 8,192.

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

LAYOUTS = [(8, 4, 8), (8, 2, 16), (4, 8, 8), (8, 8, 4), (2, 8, 16)]
CHOSEN, ALTERNATIVE = (8, 2, 16), (4, 8, 8)


def solve() -> dict:
    model, cluster = load()
    m8 = dict(model, seq_len=8192, global_batch_seqs=512)
    limit = cluster["hbm_gb"] * cluster["hbm_headroom_fraction"]
    rows = {}
    for tp, pp, dp in LAYOUTS:
        cfg = dict(BASELINE, tp=tp, pp=pp, dp=dp)
        mem, st, c = memory(m8, cluster, cfg), step(m8, cluster, cfg), comm(m8, cluster, cfg)
        rows[f"tp{tp}_pp{pp}_dp{dp}"] = {"mem_gb": mem["total_gb"], "fits_limit": mem["total_gb"] <= limit,
                                        "bubble": st["bubble_fraction"], "step_s": st["step_s"], "mfu": st["mfu"],
                                        "exposed_tp_s": st["exposed_tp_s"], "tp_bytes": c["tp_bytes"], "dp_bytes": c["dp_bytes"]}
    return {"inputs": {"seq_len": 8192, "global_batch_seqs": 512, "planning_limit_gb": limit}, "layouts": rows,
            "answer": {"chosen": "tp8_pp2_dp16", "alternative": "tp4_pp8_dp8"},
            "units": {"mem": "GB", "step": "s"}, "evidence_label": "[MODELED]"}


def check(r: dict) -> None:
    L = r["layouts"]
    # Key 11.15 table (tolerance 0.05 GB, 0.005 s, 0.001 bubble/MFU).
    key = {"tp8_pp4_dp8": (38.8, 0.045, 17.66, 0.394), "tp8_pp2_dp16": (47.6, 0.030, 17.48, 0.398),
           "tp4_pp8_dp8": (61.7, 0.099, 16.79, 0.414), "tp8_pp8_dp4": (34.5, 0.052, 17.77, 0.391)}
    for k, (mem, bub, st, mfu) in key.items():
        x = L[k]
        assert abs(x["mem_gb"] - mem) < 0.05 and abs(x["bubble"] - bub) < 0.001, (k, x)
        assert abs(x["step_s"] - st) < 0.006 and abs(x["mfu"] - mfu) < 0.001, (k, x)
        assert x["fits_limit"]
    assert not L["tp2_pp8_dp16"]["fits_limit"]


def report(r: dict) -> str:
    lines = ["# 11.15 — Sequence 8,192 layouts `[MODELED]`", "",
             "| Layout | Mem (GB) | Fits 68 GB | Bubble | Step (s) | MFU | Exposed TP (s) |", "|---|---|---|---|---|---|---|"]
    for k, x in r["layouts"].items():
        lines.append(f"| {k} | {x['mem_gb']:.1f} | {x['fits_limit']} | {x['bubble'] * 100:.1f} % | {x['step_s']:.2f} | "
                     f"{x['mfu'] * 100:.1f} % | {x['exposed_tp_s']:.2f} |")
    lines += ["", f"Chosen: {r['answer']['chosen']}; alternative: {r['answer']['alternative']}."]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    out = ap.parse_args().out
    r = solve()
    check(r)
    emit(out, r, report(r))


if __name__ == "__main__":
    main()
