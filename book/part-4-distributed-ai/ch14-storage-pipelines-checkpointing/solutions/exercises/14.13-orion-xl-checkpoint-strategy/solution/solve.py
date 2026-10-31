"""14.13 -- Checkpoint strategy for a 405B model on ORION-XL (4,096 GPUs). [MODELED]

Usage: python solve.py --out DIR
Inputs: lab/data/orion_ckpt_inputs.yaml with the prompt's [ILLUSTRATIVE] overrides (405e9 params,
4,096 GPUs, 512 nodes, 20 s step, PFS 400/800 GB/s, commit 3 s, job MTBF 3 h, 25 TB quota).
Planner model: manuscript Section 14.12 / lab Part A.
"""
import argparse
import copy
import json
import math
from pathlib import Path

import yaml

DATA = Path(__file__).resolve().parents[4] / "lab" / "data"
OVERRIDES = {"workload": {"params": 405.0e9, "gpus": 4096, "nodes": 512, "step_time_s": 20.0},
             "storage": {"pfs_write_GBps": 400.0, "pfs_read_GBps": 800.0, "commit_overhead_s": 3.0},
             "reliability": {"job_mtbf_h": 3.0}}
QUOTA_B = 25e12
DETECT_FAST_S = 60
STRATEGIES = ("sync_pfs", "async_pfs", "sync_local_drain", "async_two_level")
# Key 14.13 table: (interval_s, steps, ckpt GPU-h/day, fail GPU-h/day, total)
KEY = {"async_pfs": (180, 9, 662, 9265, 9927), "async_two_level": (140, 7, 478, 9964, 10441),
       "sync_local_drain": (300, 15, 1298, 9667, 10966), "sync_pfs": (700, 35, 3076, 11627, 14702)}


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
        return dict(delta=persist, blocking=persist, L_soft=persist, L_hard=persist, load_soft=t_pfs_r,
                    load_hard=t_pfs_r, k=1, t_pfs_w=t_pfs_w)
    if strategy == "async_pfs":
        return dict(delta=t_snap + i * persist, blocking=t_snap, L_soft=t_snap + persist, L_hard=t_snap + persist,
                    load_soft=t_pfs_r, load_hard=t_pfs_r, k=1, t_pfs_w=t_pfs_w)
    if strategy == "sync_local_drain":
        b = t_loc_w + commit
        return dict(delta=b + i * t_pfs_w, blocking=b, L_soft=b, L_hard=b + persist, load_soft=t_loc_r,
                    load_hard=t_pfs_r, k=1, t_pfs_w=t_pfs_w)
    local = t_snap + t_loc_w + commit
    return dict(delta=t_snap + i * (t_loc_w + t_pfs_w / k), blocking=t_snap, L_soft=local, L_hard=local + persist,
                load_soft=t_loc_r, load_hard=t_pfs_r, k=k, t_pfs_w=t_pfs_w)


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
    return {"blocking_s": t["blocking"], "delta_s": t["delta"], "completion_s": t["L_hard"], "young_s": young,
            "interval_s": tau, "interval_steps": round(tau / w["step_time_s"]), "overhead_pct": 100 * t["delta"] / tau,
            "rpo_max_s": k * tau + t["L_hard"], "e_ttr_s": e_ttr, "lost_gpu_h_ckpt": ckpt_h,
            "lost_gpu_h_fail": fail_h, "lost_gpu_h_day": ckpt_h + fail_h, "t_pfs_w_s": t["t_pfs_w"]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    cfg = yaml.safe_load((DATA / "orion_ckpt_inputs.yaml").read_text(encoding="utf-8"))
    cfg = copy.deepcopy(cfg)
    for sec, vals in OVERRIDES.items():
        cfg[sec].update(vals)
    rows = {s: plan(cfg, s) for s in STRATEGIES}
    for s, (tau, steps, ck, fl, tot) in KEY.items():
        r = rows[s]
        assert abs(r["interval_s"] - tau) < 0.01 and r["interval_steps"] == steps, (s, r)
        assert abs(r["lost_gpu_h_ckpt"] - ck) < 1 and abs(r["lost_gpu_h_fail"] - fl) < 1, (s, r)
        assert abs(r["lost_gpu_h_day"] - tot) < 1, (s, r)
    best = min(rows, key=lambda s: rows[s]["lost_gpu_h_day"])
    assert best == "async_pfs"
    a = rows["async_pfs"]
    w = cfg["workload"]
    size = float(w["params"]) * w["ckpt_bytes_per_param"]
    n_fit = int(QUOTA_B // size)
    gpu_h_day = w["gpus"] * 24
    fails = 24 / cfg["reliability"]["job_mtbf_h"]
    restart_gpu_h = fails * a["e_ttr_s"] * w["gpus"] / 3600
    saving = fails * (cfg["restart"]["detect_s"] - DETECT_FAST_S) * w["gpus"] / 3600
    duty = (a["t_pfs_w_s"] + cfg["storage"]["commit_overhead_s"]) / a["interval_s"]
    avg_share = size / a["interval_s"] / (cfg["storage"]["pfs_write_GBps"] * 1e9)
    # Key 14.13 checks (tolerances in the units shown).
    checks = [(size / 1e12, 5.67, 0.005), (a["t_pfs_w_s"], 18.9, 0.05), (a["blocking_s"], 0.555, 0.001),
              (a["delta_s"], 1.21, 0.005), (a["completion_s"], 22.5, 0.05), (a["young_s"], 161.8, 0.1),
              (n_fit, 4, 0), (n_fit * size / 1e12, 22.7, 0.05), (a["rpo_max_s"], 202, 0.5), (a["e_ttr_s"], 905, 0.5),
              (a["lost_gpu_h_day"] / gpu_h_day * 100, 10.1, 0.05), (restart_gpu_h, 8241, 1), (saving, 2185, 1),
              (duty * 100, 12, 0.5), (avg_share * 100, 7.9, 0.05)]
    for got, want, tol in checks:
        assert abs(got - want) <= tol, (got, want)

    result = {"inputs": {"yaml": "lab/data/orion_ckpt_inputs.yaml", "overrides": OVERRIDES, "quota_B": QUOTA_B},
              "steps": {"size_TB": round(size / 1e12, 3), "failures_per_day": fails, "gpu_h_per_day": gpu_h_day,
                        "table": {s: {k: round(v, 3) for k, v in r.items()} for s, r in rows.items()}},
              "answer": {"strategy": best, "interval_steps": a["interval_steps"], "interval_s": a["interval_s"],
                         "lost_pct_of_gpu_h": round(a["lost_gpu_h_day"] / gpu_h_day * 100, 2),
                         "checkpoints_in_quota": n_fit, "retention": "3 validated + 1 in flight",
                         "rpo_max_s": round(a["rpo_max_s"], 1), "e_time_to_resume_s": round(a["e_ttr_s"], 1),
                         "pfs_burst_duty_pct": round(duty * 100, 1), "pfs_avg_write_share_pct": round(avg_share * 100, 1),
                         "restart_gpu_h_day": round(restart_gpu_h), "detect_300_to_60_saves_gpu_h_day": round(saving)},
              "units": {"time": "s", "lost": "GPU-h/day", "size": "TB (1e12 B)"},
              "evidence_label": "[MODELED]"}
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# 14.13 ORION-XL planner `[MODELED]`", "",
             "| Strategy | tau (steps) | Overhead | RPO max | E[resume] | Lost GPU-h/day |", "|---|---|---|---|---|---|"]
    for s in sorted(rows, key=lambda s: rows[s]["lost_gpu_h_day"]):
        r = rows[s]
        lines.append(f"| {s} | {r['interval_s']:.0f} s ({r['interval_steps']}) | {r['overhead_pct']:.2f} % | "
                     f"{r['rpo_max_s']:.0f} s | {r['e_ttr_s']:.0f} s | {r['lost_gpu_h_ckpt']:.0f} + "
                     f"{r['lost_gpu_h_fail']:.0f} = {r['lost_gpu_h_day']:.0f} |")
    lines += ["", f"Capacity: 25 TB / {size/1e12:.2f} TB -> {n_fit} checkpoints ({n_fit*size/1e12:.1f} TB)",
              f"PFS burst: {size/1e12:.2f} TB in {a['t_pfs_w_s']:.1f} s every {a['interval_s']:.0f} s "
              f"(duty {duty*100:.0f} %, average {avg_share*100:.1f} % of write capacity)",
              f"Restart time costs {restart_gpu_h:,.0f} GPU-h/day; detection 300 -> 60 s saves {saving:,.0f} GPU-h/day", ""]
    (out / "result.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
