"""11.12 — Young/Daly interval, waste and lost GPU-hours for four scenarios.

Usage: python solve.py --out DIR      Evidence label: [MODELED] (assumptions [ILLUSTRATIVE], Table 11.4)
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import yaml


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

DATA = Path(__file__).resolve().parents[4] / "lab" / "data"
NAIVE_S = 4 * 3600.0


def solve() -> dict:
    import csv
    rows = {}
    with open(DATA / "reliability_scenarios.csv", encoding="utf-8") as f:
        for rec in csv.DictReader(f):
            mtbf = float(rec["job_mtbf_hours"]) * 3600
            c, rs, gpus = float(rec["checkpoint_blocking_s"]), float(rec["restart_s"]), int(rec["gpus"])
            tau = math.sqrt(2 * c * mtbf)
            lost = tau / 2 + rs
            fpd = 86400 / mtbf
            rows[rec["name"]] = {
                "gpus": gpus, "mtbf_h": mtbf / 3600, "C_s": c, "R_s": rs,
                "tau_opt_s": tau, "tau_opt_min": tau / 60,
                "waste_at_opt": c / tau + (tau / 2 + rs) / mtbf,
                "waste_at_4h": (c / NAIVE_S + (NAIVE_S / 2 + rs) / mtbf) if NAIVE_S < mtbf else None,
                "p_4h_interval_completes": math.exp(-NAIVE_S / mtbf),
                "failures_per_day": fpd, "lost_s_per_failure": lost,
                "lost_gpu_h_per_failure": lost / 3600 * gpus, "lost_gpu_h_per_day": lost / 3600 * gpus * fpd,
                "decomposition": {"C_over_tau": c / tau, "tau_over_2mtbf": tau / (2 * mtbf), "R_over_mtbf": rs / mtbf},
            }
    return {"inputs": {"source": "lab/data/reliability_scenarios.csv", "naive_interval_s": NAIVE_S},
            "answer": rows, "units": {"tau": "s", "waste": "fraction", "lost": "GPU-hours"}, "evidence_label": "[MODELED]"}


def check(r: dict) -> None:
    a = r["answer"]
    # Key 11.12 table (tolerance: 1 s on tau, 0.05 point on waste, 1 GPU-h).
    key = {"orion256_sync_pfs": (3944, 0.0280, 0.050, 204, 102),
           "orion256_async_staged": (1315, 0.0128, 0.047, 111, 55),
           "orionxl4096_sync_pfs": (986, 0.175, None, 1585, 12679),
           "orionxl4096_async_staged": (329, 0.114, None, 1211, 9688)}
    for k, (tau, w, w4, gh, ghd) in key.items():
        x = a[k]
        assert abs(x["tau_opt_s"] - tau) < 1 and abs(x["waste_at_opt"] - w) < 0.0005, (k, x)
        assert (x["waste_at_4h"] is None) == (w4 is None)
        if w4 is not None:
            assert abs(x["waste_at_4h"] - w4) < 0.0005
        assert abs(x["lost_gpu_h_per_failure"] - gh) < 1 and abs(x["lost_gpu_h_per_day"] - ghd) < 1
    d = a["orionxl4096_async_staged"]["decomposition"]
    assert d["R_over_mtbf"] > d["C_over_tau"] + d["tau_over_2mtbf"]          # restart dominates at XL


def report(r: dict) -> str:
    lines = ["# 11.12 (O3) — Checkpoint plan `[MODELED]`", "",
             "| Scenario | tau_opt (min) | Waste opt | Waste 4 h | Failures/day | Lost s/failure | GPU-h/failure | GPU-h/day |",
             "|---|---|---|---|---|---|---|---|"]
    for k, x in r["answer"].items():
        w4 = "invalid" if x["waste_at_4h"] is None else f"{x['waste_at_4h'] * 100:.1f} %"
        lines.append(f"| {k} | {x['tau_opt_min']:.1f} | {x['waste_at_opt'] * 100:.2f} % | {w4} | {x['failures_per_day']:.1f} | "
                     f"{x['lost_s_per_failure']:.0f} | {x['lost_gpu_h_per_failure']:.0f} | {x['lost_gpu_h_per_day']:.0f} |")
    d = r["answer"]["orionxl4096_async_staged"]["decomposition"]
    lines += ["", f"XL async decomposition: C/tau {d['C_over_tau'] * 100:.2f} %, tau/2MTBF {d['tau_over_2mtbf'] * 100:.2f} %, "
              f"R/MTBF {d['R_over_mtbf'] * 100:.2f} %"]
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
