"""11.9 — Per-GPU TP/DP/PP bytes and times for the baseline; TP bytes at TP = 2.

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

def tp_bytes_identity(model: dict, world: int, t: int) -> float:
    m_bytes = model["seq_len"] * 1 * model["hidden"] * model["act_bytes"]
    return 8 * (t - 1) * m_bytes * model["layers"] * model["global_batch_seqs"] / (world * 1)


def solve() -> dict:
    model, cluster = load()
    c = comm(model, cluster, BASELINE)
    s = step(model, cluster, BASELINE)
    tp2 = tp_bytes_identity(model, 256, 2)
    tp2_model = comm(model, cluster, dict(BASELINE, tp=2, pp=4, dp=32))["tp_bytes"]
    exposed = {"tp": s["exposed_tp_s"], "dp": s["exposed_dp_s"], "pp": s["exposed_pp_s"]}
    return {"inputs": {"layout": BASELINE, "nvlink_gbs": cluster["nvlink_busbw_gbs"], "rail_gbs": cluster["rail_busbw_gbs"]},
            "volumes_bytes": {"tp": c["tp_bytes"], "dp": c["dp_bytes"], "pp": c["pp_bytes"]},
            "times_s": {"tp": c["tp_s"], "dp": c["dp_s"], "pp": c["pp_s"]},
            "exposed_s": exposed, "dp_window_s": s["dp_window_s"], "step_s": s["step_s"],
            "tp_share_of_exposed": exposed["tp"] / sum(exposed.values()),
            "tp_share_of_step": exposed["tp"] / s["step_s"],
            "answer": {"tp2_bytes": tp2, "tp2_bytes_layout_check": tp2_model, "tp8_over_tp2": c["tp_bytes"] / tp2,
                       "attack_first": max(exposed, key=exposed.get)},
            "units": {"volumes": "bytes per GPU per step", "times": "s"}, "evidence_label": "[MODELED]"}


def check(r: dict) -> None:
    v, t, e = r["volumes_bytes"], r["times_s"], r["exposed_s"]
    # Key 11.9 (tolerance 0.5 %): TP 1.2026e12 B / 4.11 s / 3.08 s; DP 7.656e9 B / 0.170 s / 0.098 s;
    # PP 2.147e9 B / 0.055 s / 0.028 s; TP = 2 -> 171.8 GB = TP8 / 7.
    assert abs(v["tp"] / 1.2026e12 - 1) < 0.005 and abs(v["dp"] / 7.656e9 - 1) < 0.005 and abs(v["pp"] / 2.147e9 - 1) < 0.005
    assert abs(t["tp"] - 4.11) < 0.01 and abs(t["dp"] - 0.170) < 0.001 and abs(t["pp"] - 0.055) < 0.001
    assert abs(e["tp"] - 3.08) < 0.01 and abs(e["dp"] - 0.098) < 0.001 and abs(e["pp"] - 0.028) < 0.001
    a = r["answer"]
    assert abs(a["tp2_bytes"] / 171.8e9 - 1) < 0.005 and abs(a["tp2_bytes_layout_check"] / a["tp2_bytes"] - 1) < 1e-9
    assert abs(a["tp8_over_tp2"] - 7.0) < 1e-6 and a["attack_first"] == "tp"


def report(r: dict) -> str:
    v, t, e, a = r["volumes_bytes"], r["times_s"], r["exposed_s"], r["answer"]
    return f"""# 11.9 — Communication budget `[MODELED]`

| Dim | Bytes/GPU/step | Time (s) | Exposed (s) |
|---|---|---|---|
| TP | {v['tp']:.4g} | {t['tp']:.3f} | {e['tp']:.3f} |
| DP | {v['dp']:.4g} | {t['dp']:.3f} | {e['dp']:.3f} |
| PP | {v['pp']:.4g} | {t['pp']:.3f} | {e['pp']:.3f} |

TP is {r['tp_share_of_exposed'] * 100:.1f} % of exposed communication and {r['tp_share_of_step'] * 100:.1f} % of the {r['step_s']:.2f} s step: attack {a['attack_first'].upper()} first.
TP = 2: 8 x (t-1) x M x L x B / (W x b) = {a['tp2_bytes'] / 1e9:.1f} GB (TP 8 / TP 2 = {a['tp8_over_tp2']:.1f}).
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
