"""12.11 — Fit alpha/B, n_half, plateau and regions for all six lab configurations.

Usage: python solve.py --out DIR      Evidence label: [MODELED] fits of [SIMULATED] lab data
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

CONFIGS = {"c1_1node_8gpu": "c1_1node_8gpu.log", "c2_2node_aligned": "c2_2node_aligned.log",
           "c3_2node_alt_map": "c3_2node_alt_map.log", "c4_4node_aligned": "c4_4node_aligned.log",
           "c5_8node_aligned": "c5_8node_aligned.log", "c6_8node_run2": "c6_8node_run2.log"}
CACHE: dict = {}


def cv_large(rows: list[dict], min_size: int = 256 * 2**20) -> float:
    v = np.array([x for r in rows if r["size"] >= min_size for x in (r["busbw"], r["busbw_ip"])])
    return float(v.std(ddof=1) / v.mean())


def solve() -> dict:
    summary = {}
    for name, f in CONFIGS.items():
        n, nodes, rows = read_log(f)
        CACHE[name] = rows
        reg = regions(rows)
        lat = [r["size"] for r, g in zip(rows, reg) if g == "latency"]
        bw = [r["size"] for r, g in zip(rows, reg) if g == "bandwidth"]
        summary[name] = {"nodes": nodes, "nranks": n, **fit(rows, n), "plateau_GBps": plateau(rows),
                         "latency_max_size": int(max(lat)), "bandwidth_min_size": int(min(bw)),
                         "egress_efficiency": plateau(rows) / (nodes * 400.0) if nodes > 1 else None,
                         "jitter_cv": cv_large(rows)}
    aligned = ["c2_2node_aligned", "c4_4node_aligned", "c5_8node_aligned"]
    return {"inputs": {"data": "lab/data/*.log", "thresholds": {"latency": "t <= 1.5 x min", "bandwidth": ">= 0.8 x plateau"}},
            "summary": summary,
            "scaling": {"aligned_plateau_GBps": [summary[c]["plateau_GBps"] for c in aligned],
                        "aligned_alpha_us": [summary[c]["alpha_us"] for c in aligned],
                        "plateau_drop_2_to_8_nodes": 1 - summary[aligned[-1]]["plateau_GBps"] / summary[aligned[0]]["plateau_GBps"]},
            "units": {"alpha": "us", "B": "GB/s", "n_half": "MB"}, "evidence_label": "[MODELED] fits of [SIMULATED] data"}


def check(r: dict) -> None:
    s = r["summary"]
    # Key 12.11 table: alpha (0.1 us), B (1 GB/s), n_half (0.1 MB), plateau (1 GB/s), region edges (exact).
    key = {"c1_1node_8gpu": (14.1, 448, 3.6, 449, 2**20, 16 * 2**20),
           "c2_2node_aligned": (28.1, 354, 5.3, 352, 2**20, 32 * 2**20),
           "c3_2node_alt_map": (39.2, 185, 3.9, 184, 2**20, 16 * 2**20),
           "c4_4node_aligned": (36.2, 349, 6.5, 349, 2 * 2**20, 32 * 2**20),
           "c5_8node_aligned": (47.3, 346, 8.3, 345, 2 * 2**20, 32 * 2**20),
           "c6_8node_run2": (49.8, 185, 4.7, 177, 2**20, 16 * 2**20)}
    for k, (a, b, nh, p, lat, bw) in key.items():
        x = s[k]
        assert abs(x["alpha_us"] - a) < 0.1 and abs(x["B_GBps"] - b) < 1 and abs(x["n_half_MB"] - nh) < 0.1, (k, x)
        assert abs(x["plateau_GBps"] - p) < 1 and x["latency_max_size"] == lat and x["bandwidth_min_size"] == bw, (k, x)
    assert r["scaling"]["plateau_drop_2_to_8_nodes"] < 0.03


def extras(r: dict) -> dict:
    lines = ["size_b,time_us_c2,time_us_c5"]
    c5 = {row["size"]: row["time_us"] for row in CACHE["c5_8node_aligned"]}
    for row in CACHE["c2_2node_aligned"]:
        lines.append(f"{int(row['size'])},{row['time_us']},{c5.get(row['size'], '')}")
    return {"plot_data_c2_c5.csv": "\n".join(lines) + "\n"}


def report(r: dict) -> str:
    lines = ["# 12.11 (O2) — Result-set analysis `[MODELED]`", "",
             "| Config | Ranks | Latency <= (B) | Bandwidth >= (B) | alpha (us) | B (GB/s) | n_half (MB) | Plateau (GB/s) | CV |",
             "|---|---|---|---|---|---|---|---|---|"]
    for k, x in r["summary"].items():
        lines.append(f"| {k} | {x['nranks']} | {x['latency_max_size']:,} | {x['bandwidth_min_size']:,} | {x['alpha_us']:.1f} | "
                     f"{x['B_GBps']:.0f} | {x['n_half_MB']:.1f} | {x['plateau_GBps']:.0f} | {x['jitter_cv']:.3f} |")
    sc = r["scaling"]
    lines += ["", f"Aligned plateau 2/4/8 nodes: {[round(v) for v in sc['aligned_plateau_GBps']]} GB/s; "
              f"alpha {[round(v, 1) for v in sc['aligned_alpha_us']]} us; drop {sc['plateau_drop_2_to_8_nodes'] * 100:.1f} %"]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    out = ap.parse_args().out
    r = solve()
    check(r)
    emit(out, r, report(r), extras(r) if "extras" in globals() else None)


if __name__ == "__main__":
    main()
