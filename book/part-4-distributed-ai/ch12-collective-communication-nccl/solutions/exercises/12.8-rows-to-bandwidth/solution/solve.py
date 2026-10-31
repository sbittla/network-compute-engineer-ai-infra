"""12.8 — Recompute algbw/busbw for three c4 rows and the NIC-egress efficiency.

Usage: python solve.py --out DIR      Evidence label: [MODELED] from [SIMULATED] lab data
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

SIZES = [1_048_576, 67_108_864, 4_294_967_296]
NODE_EGRESS_GBPS = 8 * 50.0          # 8 x 400 Gb/s NICs per HX8 node


def solve() -> dict:
    n, nodes, rows = read_log("c4_4node_aligned.log")
    f = factor("all_reduce", n)
    reg = dict(zip([r["size"] for r in rows], regions(rows)))
    out = []
    for s in SIZES:
        row = next(r for r in rows if r["size"] == s)
        alg = s / (row["time_us"] * 1e-6) / 1e9
        out.append({"size_b": s, "time_us": row["time_us"], "algbw_GBps": alg, "busbw_GBps": alg * f,
                    "printed_busbw": row["busbw"], "region": reg[s]})
    eff = out[-1]["busbw_GBps"] / NODE_EGRESS_GBPS
    return {"inputs": {"log": "c4_4node_aligned.log", "nranks": n, "nodes": nodes, "factor": f,
                       "plateau_GBps": plateau(rows)},
            "rows": out, "answer": {"efficiency_vs_node_egress": eff},
            "units": {"bandwidth": "GB/s (1e9 B/s)", "time": "us"}, "evidence_label": "[MODELED] from [SIMULATED] data"}


def check(r: dict) -> None:
    assert r["inputs"]["nranks"] == 32 and r["inputs"]["factor"] == 1.9375
    key = [(24.34, 47.16, "latency"), (165.46, 320.57, "bandwidth"), (180.75, 350.20, "bandwidth")]
    for row, (alg, bus, region) in zip(r["rows"], key):
        # Key 12.8 to 2 decimals (tolerance 0.01 GB/s); also equal to the printed column within rounding.
        assert abs(row["algbw_GBps"] - alg) < 0.01 and abs(row["busbw_GBps"] - bus) < 0.01, row
        assert abs(row["busbw_GBps"] - row["printed_busbw"]) < 0.01 and row["region"] == region
    assert abs(r["answer"]["efficiency_vs_node_egress"] - 0.876) < 0.0005


def report(r: dict) -> str:
    rows = "\n".join(f"| {x['size_b']:,} | {x['time_us']} | {x['algbw_GBps']:.2f} | {x['busbw_GBps']:.2f} | {x['region']} |" for x in r["rows"])
    return f"""# 12.8 — c4 rows `[MODELED]` from `[SIMULATED]` data

n = {r['inputs']['nranks']}, factor = {r['inputs']['factor']}

| Size (B) | Time (us) | algbw (GB/s) | busbw (GB/s) | Region |
|---|---|---|---|---|
{rows}

Efficiency vs 400 GB/s node egress: {r['answer']['efficiency_vs_node_egress'] * 100:.1f} %
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
