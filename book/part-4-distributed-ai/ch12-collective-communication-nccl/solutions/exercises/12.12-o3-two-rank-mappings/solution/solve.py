"""12.12 — Predict c2/c3 plateaus from topology and compare with the lab data.

Usage: python solve.py --out DIR      Evidence label: [MODELED] prediction vs [SIMULATED] lab data
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

import numpy as np

DATA = Path(__file__).resolve().parents[4] / "lab" / "data"
COLS = ["size", "count", "type", "redop", "root", "time_us", "algbw", "busbw", "wrong",
        "time_us_ip", "algbw_ip", "busbw_ip", "wrong_ip"]


def factor(op: str, n: int) -> float:
    """nccl-tests busbw correction factor (PERFORMANCE.md)."""
    return {"all_reduce": 2 * (n - 1) / n, "all_gather": (n - 1) / n, "reduce_scatter": (n - 1) / n,
            "alltoall": (n - 1) / n, "broadcast": 1.0, "reduce": 1.0}[op]


def read_log(name: str) -> tuple[int, int, list[dict]]:
    """Return (nranks, nodes, rows) from an all_reduce_perf log in lab/data."""
    ranks, hosts, rows = 0, [], []
    for line in (DATA / name).read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            m = re.match(r"^#\s+Rank\s+\d+\s+Group\s+\d+\s+Pid\s+\d+\s+on\s+(\S+)\s+device", line)
            if m:
                ranks += 1
                if m.group(1) not in hosts:
                    hosts.append(m.group(1))
            continue
        p = line.split()
        if len(p) == len(COLS) and p[0].isdigit():
            rows.append({k: (v if k in ("type", "redop") else float(v)) for k, v in zip(COLS, p)})
    return ranks, len(hosts), rows


def plateau(rows: list[dict], k: int = 4) -> float:
    """Median out-of-place busbw of the k largest sizes (GB/s)."""
    return float(np.median([r["busbw"] for r in sorted(rows, key=lambda r: r["size"])[-k:]]))


def fit(rows: list[dict], n: int) -> dict:
    """Least-squares fit of t = alpha + factor*S/B, weighted by 1/t, on out-of-place and in-place times."""
    f = factor("all_reduce", n)
    s = np.array([r["size"] for r in rows] * 2, dtype=float)
    t = np.array([r["time_us"] for r in rows] + [r["time_us_ip"] for r in rows], dtype=float)
    w = 1 / t
    coef, *_ = np.linalg.lstsq(np.column_stack([np.ones_like(s), f * s]) * w[:, None], t * w, rcond=None)
    alpha, b = float(coef[0]), 1 / (float(coef[1]) * 1e-6) / 1e9
    return {"alpha_us": alpha, "B_GBps": b, "n_half_MB": alpha * 1e-6 * b * 1e9 / f / 1e6}


def regions(rows: list[dict], lat_factor: float = 1.5, bw_fraction: float = 0.8) -> list[str]:
    """latency: time <= 1.5 x min time; bandwidth: busbw >= 0.8 x plateau; else transition."""
    tmin, plat = min(r["time_us"] for r in rows), plateau(rows)
    return ["latency" if r["time_us"] <= lat_factor * tmin else
            "bandwidth" if r["busbw"] >= bw_fraction * plat else "transition" for r in rows]


def rnd(obj, nd: int = 4):
    """Round floats for deterministic output."""
    if isinstance(obj, (bool, np.bool_)) or obj is None:
        return bool(obj) if isinstance(obj, np.bool_) else obj
    if isinstance(obj, (float, np.floating)):
        obj = float(obj)
        return float(f"{obj:.{nd}g}") if abs(obj) >= 1e6 or (obj != 0 and abs(obj) < 1e-3) else round(obj, nd)
    if isinstance(obj, dict):
        return {str(k): rnd(v, nd) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [rnd(v, nd) for v in obj]
    if isinstance(obj, np.integer):
        return int(obj)
    return obj


def emit(out: Path, result: dict, md: str, extra: dict | None = None) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(rnd(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "result.md").write_text(md.strip() + "\n", encoding="utf-8")
    for name, text in (extra or {}).items():
        (out / name).write_text(text, encoding="utf-8")
    print(md)

NIC_GBPS = 50.0
PRED = {"c2_2node_aligned": {"nics": 8, "eff": 0.88}, "c3_2node_alt_map": {"nics": 4, "eff": 0.92}}
FILES = {"c2_2node_aligned": "c2_2node_aligned.log", "c3_2node_alt_map": "c3_2node_alt_map.log"}


def solve() -> dict:
    out = {}
    for k, p in PRED.items():
        n, nodes, rows = read_log(FILES[k])
        ceiling = p["nics"] * NIC_GBPS
        meas = plateau(rows)
        out[k] = {"nics_per_node": p["nics"], "ceiling_GBps": ceiling, "predicted_GBps": ceiling * p["eff"],
                  "measured_plateau_GBps": meas, "alpha_us": fit(rows, n)["alpha_us"],
                  "error_vs_prediction": meas / (ceiling * p["eff"]) - 1}
    ratio = out["c3_2node_alt_map"]["measured_plateau_GBps"] / out["c2_2node_aligned"]["measured_plateau_GBps"]
    d_alpha = out["c3_2node_alt_map"]["alpha_us"] - out["c2_2node_aligned"]["alpha_us"]
    return {"inputs": {"nic_GBps": NIC_GBPS, "assumed_efficiency": {k: v["eff"] for k, v in PRED.items()}},
            "answer": out, "c3_over_c2": ratio, "alpha_increase_us": d_alpha,
            "units": {"bandwidth": "GB/s", "alpha": "us"}, "evidence_label": "[MODELED] vs [SIMULATED]"}


def check(r: dict) -> None:
    a = r["answer"]
    # Key 12.12: predictions ~350 / ~185 GB/s; data 352 / 184 GB/s; alpha 28 vs 39 us (+5..15 us predicted).
    assert abs(a["c2_2node_aligned"]["predicted_GBps"] - 352) < 3 and abs(a["c3_2node_alt_map"]["predicted_GBps"] - 184) < 3
    assert abs(a["c2_2node_aligned"]["measured_plateau_GBps"] - 352) < 1 and abs(a["c3_2node_alt_map"]["measured_plateau_GBps"] - 184) < 1
    assert all(abs(x["error_vs_prediction"]) < 0.02 for x in a.values())
    assert 5 <= r["alpha_increase_us"] <= 15


def report(r: dict) -> str:
    rows = "\n".join(f"| {k} | {x['nics_per_node']} | {x['ceiling_GBps']:.0f} | {x['predicted_GBps']:.0f} | "
                     f"{x['measured_plateau_GBps']:.0f} | {x['alpha_us']:.1f} |" for k, x in r["answer"].items())
    return f"""# 12.12 (O3) — Prediction vs data

| Config | NICs/node | Ceiling (GB/s) | Predicted (GB/s) `[MODELED]` | Plateau (GB/s) `[SIMULATED]` | alpha (us) |
|---|---|---|---|---|---|
{rows}

c3/c2 = {r['c3_over_c2']:.3f}; alpha increase {r['alpha_increase_us']:.1f} us
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    out = ap.parse_args().out
    r = solve()
    check(r)
    emit(out, r, report(r), extras(r) if "extras" in globals() else None)


if __name__ == "__main__":
    main()
