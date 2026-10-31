"""14.10 -- Checkpoint planner at the Llama-3-derived job MTBF M = 198 h. [MODELED]

Usage: python solve.py --out DIR
Inputs: lab/data/orion_ckpt_inputs.yaml with reliability.job_mtbf_h = 198 (prompt). The planner model is
the one of manuscript Section 14.12 / lab Part A (Young interval floored at the in-flight completion
latency and rounded up to whole steps; expected lost work and time-to-resume per failure class).
"""
import argparse
import copy
import json
import math
from pathlib import Path

import yaml

DATA = Path(__file__).resolve().parents[4] / "lab" / "data"
MTBF_H = 198.0
STRATEGIES = ("sync_pfs", "async_pfs", "sync_local_drain", "async_two_level")
# Key 14.10 table: (interval_s, steps, lost GPU-h/day ckpt, fail, total)
KEY = {"async_pfs": (1305.0, 75, 5.59, 13.58, 19.2), "async_two_level": (1061.4, 61, 4.54, 19.74, 24.3),
       "sync_local_drain": (2105.4, 121, 9.00, 16.91, 25.9), "sync_pfs": (5046.0, 290, 21.71, 29.69, 51.4)}


def timings(cfg: dict, strategy: str) -> dict:
    w, s, h, a = cfg["workload"], cfg["storage"], cfg["host"], cfg["async"]
    size = float(w["params"]) * w["ckpt_bytes_per_param"]
    t_pfs_w = size / (s["pfs_write_GBps"] * 1e9 * s["pfs_efficiency"])
    t_pfs_r = size / (s["pfs_read_GBps"] * 1e9 * s["pfs_efficiency"])
    commit = s["commit_overhead_s"]
    persist = t_pfs_w + commit
    t_snap = size / w["gpus"] / (h["d2h_GBps_per_gpu"] * 1e9) + h["snapshot_fixed_s"]
    t_loc_w = size / w["nodes"] / (h["nvme_write_GBps_per_node"] * 1e9)
    t_loc_r = size / w["nodes"] / (h["nvme_read_GBps_per_node"] * 1e9)
    i, k = a["interference_frac"], int(a["pfs_every_k"])
    if strategy == "sync_pfs":
        return dict(delta=persist, L_soft=persist, L_hard=persist, load_soft=t_pfs_r, load_hard=t_pfs_r, k=1)
    if strategy == "async_pfs":
        return dict(delta=t_snap + i * persist, L_soft=t_snap + persist, L_hard=t_snap + persist,
                    load_soft=t_pfs_r, load_hard=t_pfs_r, k=1)
    if strategy == "sync_local_drain":
        b = t_loc_w + commit
        return dict(delta=b + i * t_pfs_w, L_soft=b, L_hard=b + persist, load_soft=t_loc_r, load_hard=t_pfs_r, k=1)
    local = t_snap + t_loc_w + commit
    return dict(delta=t_snap + i * (t_loc_w + t_pfs_w / k), L_soft=local, L_hard=local + persist,
                load_soft=t_loc_r, load_hard=t_pfs_r, k=k)


def plan(cfg: dict, strategy: str) -> dict:
    w, r, rel = cfg["workload"], cfg["restart"], cfg["reliability"]
    t = timings(cfg, strategy)
    m = rel["job_mtbf_h"] * 3600.0
    hf, k = rel["hard_failure_frac"], t["k"]
    floor = t["L_soft"] if k > 1 else t["L_hard"]
    young = math.sqrt(2 * t["delta"] * m)
    tau = math.ceil(max(young, floor) / w["step_time_s"] - 1e-9) * w["step_time_s"]
    e_lost = (1 - hf) * (tau / 2 + t["L_soft"]) + hf * (k * tau / 2 + t["L_hard"])
    base = r["detect_s"] + r["relaunch_s"] + r["validate_s"] + r["warmup_s"]
    e_ttr = (1 - hf) * (base + t["load_soft"]) + hf * (base + r["replace_s"] + t["load_hard"])
    ckpt_h = 86400 / tau * t["delta"] * w["gpus"] / 3600
    fail_h = 86400 / m * (e_lost + e_ttr) * w["gpus"] / 3600
    return {"delta_s": t["delta"], "young_s": young, "interval_s": tau, "interval_steps": round(tau / w["step_time_s"]),
            "overhead_pct": 100 * t["delta"] / tau, "rpo_max_s": k * tau + t["L_hard"], "completion_s": t["L_hard"],
            "e_lost_s": e_lost, "e_ttr_s": e_ttr, "lost_gpu_h_ckpt": ckpt_h, "lost_gpu_h_fail": fail_h,
            "lost_gpu_h_day": ckpt_h + fail_h}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    base_cfg = yaml.safe_load((DATA / "orion_ckpt_inputs.yaml").read_text(encoding="utf-8"))
    cfg = copy.deepcopy(base_cfg)
    cfg["reliability"]["job_mtbf_h"] = MTBF_H
    rows = {s: plan(cfg, s) for s in STRATEGIES}
    base = {s: plan(base_cfg, s) for s in STRATEGIES}
    for s, (tau, steps, ck, fl, tot) in KEY.items():
        r = rows[s]
        assert abs(r["interval_s"] - tau) < 0.05 and r["interval_steps"] == steps, (s, r)
        assert abs(r["lost_gpu_h_ckpt"] - ck) < 0.01 and abs(r["lost_gpu_h_fail"] - fl) < 0.01, (s, r)
        assert abs(r["lost_gpu_h_day"] - tot) < 0.05, (s, r)
    # hand check (async PFS): Young sqrt(2 × 1.188 × 712,800) = 1,301.5 s
    assert abs(rows["async_pfs"]["delta_s"] - 1.188) < 0.001 and abs(rows["async_pfs"]["young_s"] - 1301.5) < 0.5
    order = sorted(rows, key=lambda s: rows[s]["lost_gpu_h_day"])
    order_base = sorted(base, key=lambda s: base[s]["lost_gpu_h_day"])
    assert order == order_base, "ranking should be unchanged"
    ratio = base["async_pfs"]["lost_gpu_h_day"] / rows["async_pfs"]["lost_gpu_h_day"]
    assert abs(ratio - 2.9) < 0.05, ratio

    rnd = {s: {k: round(v, 3) for k, v in r.items()} for s, r in rows.items()}
    result = {"inputs": {"yaml": "lab/data/orion_ckpt_inputs.yaml", "job_mtbf_h": MTBF_H},
              "steps": {"mtbf_s": MTBF_H * 3600, "failures_per_day": round(86400 / (MTBF_H * 3600), 4),
                        "baseline_M48_lost_gpu_h_day": {s: round(b["lost_gpu_h_day"], 2) for s, b in base.items()}},
              "answer": {"table": rnd, "ranking": order, "async_loss_reduction_x": round(ratio, 2),
                         "interval_stretch_x": round(math.sqrt(MTBF_H / 48.0), 2)},
              "units": {"time": "s", "lost": "GPU-h/day", "overhead": "%"},
              "evidence_label": "[MODELED]"}
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# 14.10 planner at M = 198 h `[MODELED]`", "",
             "| Strategy | tau (steps) | Overhead | RPO max | Lost GPU-h/day (ckpt + fail) |", "|---|---|---|---|---|"]
    for s in order:
        r = rows[s]
        lines.append(f"| {s} | {r['interval_s']:.1f} s ({r['interval_steps']}) | {r['overhead_pct']:.2f} % | "
                     f"{r['rpo_max_s']:.0f} s | {r['lost_gpu_h_ckpt']:.2f} + {r['lost_gpu_h_fail']:.2f} = "
                     f"{r['lost_gpu_h_day']:.1f} |")
    a = rows["async_pfs"]
    lines += ["", f"Hand check (async PFS): Young = sqrt(2 × {a['delta_s']:.3f} × 712,800) = {a['young_s']:.1f} s "
              f"-> {a['interval_steps']} steps = {a['interval_s']:.1f} s",
              f"Ranking unchanged; async losses fall {ratio:.1f}× vs M = 48 h.", ""]
    (out / "result.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
