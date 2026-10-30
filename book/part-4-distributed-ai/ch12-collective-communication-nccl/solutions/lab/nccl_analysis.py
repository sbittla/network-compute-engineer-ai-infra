"""Analyze nccl-tests ``all_reduce_perf`` outputs (reference solution).

Units: sizes in bytes; times in microseconds (as printed by nccl-tests); bandwidths in GB/s with
GB = 1e9 B (the nccl-tests convention). Results computed from the lab's synthetic logs are
[SIMULATED]; fitted alpha-beta parameters are [MODELED].

nccl-tests definitions (see its PERFORMANCE.md):
    algbw = S / t
    busbw = algbw * factor, factor = 2(n-1)/n for all-reduce, (n-1)/n for all-gather,
            reduce-scatter and all-to-all, 1 for broadcast and reduce.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

COLS = ["size", "count", "type", "redop", "root",
        "time_us", "algbw", "busbw", "wrong",
        "time_us_ip", "algbw_ip", "busbw_ip", "wrong_ip"]
_DEV = re.compile(r"^#\s+Rank\s+(\d+)\s+Group\s+\d+\s+Pid\s+\d+\s+on\s+(\S+)\s+device\s+(\d+)")
_HDR = re.compile(r"warmup iters:\s*(\d+)\s+iters:\s*(\d+)")


def bus_factor(op: str, n: int) -> float:
    """nccl-tests bus-bandwidth correction factor for collective ``op`` over ``n`` ranks."""
    if n < 1:
        raise ValueError("n must be >= 1")
    if op == "all_reduce":
        return 2 * (n - 1) / n
    if op in ("all_gather", "reduce_scatter", "alltoall"):
        return (n - 1) / n
    if op in ("broadcast", "reduce"):
        return 1.0
    raise ValueError(f"unknown op {op}")


def parse_nccl_log(text: str) -> tuple[dict[str, Any], pd.DataFrame]:
    """Parse one all_reduce_perf output.

    Returns (meta, table). ``meta`` has: nranks, hosts (ordered unique hostnames), nodes,
    ranks_per_host (dict), warmup_iters, iters, avg_busbw_reported (float or None).
    ``table`` has one row per message size with columns COLS (numeric where numeric).
    """
    meta: dict[str, Any] = {"nranks": 0, "hosts": [], "ranks_per_host": {}, "warmup_iters": None,
                            "iters": None, "avg_busbw_reported": None}
    rows = []
    for line in text.splitlines():
        if line.startswith("#"):
            m = _DEV.match(line)
            if m:
                host = m.group(2)
                meta["nranks"] += 1
                if host not in meta["ranks_per_host"]:
                    meta["hosts"].append(host)
                    meta["ranks_per_host"][host] = 0
                meta["ranks_per_host"][host] += 1
                continue
            h = _HDR.search(line)
            if h:
                meta["warmup_iters"], meta["iters"] = int(h.group(1)), int(h.group(2))
            if "Avg bus bandwidth" in line:
                meta["avg_busbw_reported"] = float(line.split(":")[1])
            continue
        parts = line.split()
        if len(parts) == len(COLS) and parts[0].isdigit():
            rows.append(parts)
    df = pd.DataFrame(rows, columns=COLS)
    for c in COLS:
        if c not in ("type", "redop"):
            df[c] = pd.to_numeric(df[c])
    meta["nodes"] = len(meta["hosts"])
    return meta, df


def compute_bw(size_b: np.ndarray | float, time_us: np.ndarray | float, n: int,
               op: str = "all_reduce") -> tuple[Any, Any]:
    """(algbw, busbw) in GB/s from size (B) and time (µs)."""
    algbw = np.asarray(size_b, dtype=float) / (np.asarray(time_us, dtype=float) * 1e-6) / 1e9
    return algbw, algbw * bus_factor(op, n)


def plateau_busbw(df: pd.DataFrame, k: int = 4) -> float:
    """Median out-of-place busbw over the ``k`` largest message sizes (GB/s)."""
    return float(df.sort_values("size")["busbw"].tail(k).median())


def classify_regions(df: pd.DataFrame, lat_factor: float = 1.5, bw_fraction: float = 0.8) -> pd.Series:
    """Label each size 'latency', 'transition' or 'bandwidth'.

    latency   : time <= lat_factor * minimum time (time is ~flat: fixed cost dominates)
    bandwidth : busbw >= bw_fraction * plateau busbw
    transition: everything else
    """
    tmin = df["time_us"].min()
    plat = plateau_busbw(df)
    lab = np.where(df["time_us"] <= lat_factor * tmin, "latency",
                   np.where(df["busbw"] >= bw_fraction * plat, "bandwidth", "transition"))
    return pd.Series(lab, index=df.index, name="region")


def fit_alpha_beta(df: pd.DataFrame, n: int, op: str = "all_reduce") -> dict[str, float]:
    """Fit t = alpha + factor * S / B by least squares weighted by 1/t (relative error).

    Uses both out-of-place and in-place times. Returns alpha_us, busbw_fit_GBps (B), and
    n_half_bytes: the message size at which the bandwidth term equals alpha (S* = alpha*B/factor).
    """
    f = bus_factor(op, n)
    s = np.concatenate([df["size"].to_numpy(float)] * 2)
    t = np.concatenate([df["time_us"].to_numpy(float), df["time_us_ip"].to_numpy(float)])
    w = 1.0 / t
    a = np.column_stack([np.ones_like(s), f * s]) * w[:, None]
    coef, *_ = np.linalg.lstsq(a, t * w, rcond=None)
    alpha_us, inv_b = float(coef[0]), float(coef[1])        # inv_b in µs per byte
    b_gbps = 1.0 / (inv_b * 1e-6) / 1e9
    return {"alpha_us": alpha_us, "busbw_fit_GBps": b_gbps,
            "n_half_bytes": alpha_us * 1e-6 * b_gbps * 1e9 / f}


def jitter_cv(df: pd.DataFrame, min_size: int = 256 * 2**20) -> float:
    """Coefficient of variation of busbw (out-of-place and in-place) for sizes >= min_size."""
    big = df[df["size"] >= min_size]
    v = np.concatenate([big["busbw"].to_numpy(float), big["busbw_ip"].to_numpy(float)])
    return float(v.std(ddof=1) / v.mean())


def analyze_all(data_dir: Path) -> pd.DataFrame:
    """Summary row per configuration listed in ``configs.yaml``."""
    data_dir = Path(data_dir)
    cfg = yaml.safe_load((data_dir / "configs.yaml").read_text(encoding="utf-8"))
    rows = []
    for name, c in cfg["configs"].items():
        meta, df = parse_nccl_log((data_dir / c["file"]).read_text(encoding="utf-8"))
        n = meta["nranks"]
        fit = fit_alpha_beta(df, n)
        reg = classify_regions(df)
        lat = df.loc[reg == "latency", "size"]
        bw = df.loc[reg == "bandwidth", "size"]
        rows.append({
            "name": name, "nodes": meta["nodes"], "nranks": n,
            "plateau_busbw": plateau_busbw(df),
            "avg_busbw_reported": meta["avg_busbw_reported"],
            "alpha_us": fit["alpha_us"], "busbw_fit": fit["busbw_fit_GBps"],
            "n_half_bytes": fit["n_half_bytes"],
            "latency_max_size": int(lat.max()) if len(lat) else 0,
            "bandwidth_min_size": int(bw.min()) if len(bw) else 0,
            "jitter_cv": jitter_cv(df),
        })
    return pd.DataFrame(rows)


def detect_anomalies(summary: pd.DataFrame, low_fraction: float = 0.75, cv_limit: float = 0.04) -> dict[str, str]:
    """Label each configuration.

    Multi-node configurations are compared with the *median* multi-node plateau (single-node runs
    form their own class and are labelled 'ok' unless jittery). Labels:
      'ok'                  plateau >= low_fraction * reference and jitter_cv <= cv_limit
      'low_plateau_steady'  plateau low, jitter normal  -> suspect topology/rank/NIC mapping
      'low_plateau_jittery' plateau low and jitter high -> suspect a degraded link/rail
      'jittery'             plateau fine, jitter high   -> suspect intermittent congestion/errors
    """
    multi = summary[summary["nodes"] > 1]
    ref = float(multi["plateau_busbw"].median()) if len(multi) else float("nan")
    out = {}
    for r in summary.to_dict("records"):
        low = r["nodes"] > 1 and r["plateau_busbw"] < low_fraction * ref
        jit = r["jitter_cv"] > cv_limit
        out[r["name"]] = ("low_plateau_jittery" if low and jit else "low_plateau_steady" if low
                          else "jittery" if jit else "ok")
    return out


def predict_time_us(alpha_us: float, busbw_gbps: float, n: int, size_b: float, op: str = "all_reduce") -> float:
    """Alpha-beta prediction t = alpha + factor * S / B, in µs."""
    return alpha_us + bus_factor(op, n) * size_b / (busbw_gbps * 1e9) * 1e6


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="Summarize nccl-tests all_reduce_perf logs")
    ap.add_argument("--data", type=Path, default=Path(__file__).resolve().parents[2] / "lab" / "data")
    args = ap.parse_args()
    pd.set_option("display.width", 200)
    s = analyze_all(args.data)
    print(s.round(3).to_string(index=False))
    print()
    for k, v in detect_anomalies(s).items():
        print(f"{k:22s} {v}")


if __name__ == "__main__":
    main()
