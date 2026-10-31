#!/usr/bin/env python3
"""T1 — statistics of the shared-fabric 4-node all_reduce_perf runs [ILLUSTRATIVE inputs].

Usage: python solve.py --out DIR   (writes result.json and result.md; asserts the answer key)
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def r(x: float, nd: int = 4) -> float:
    return round(float(x), nd)


def write(out: Path, result: dict, md_lines: list[str]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                                     encoding="utf-8")
    (out / "result.md").write_text("\n".join(md_lines).rstrip() + "\n", encoding="utf-8")


def close(a: float, b: float, tol: float) -> bool:
    return abs(a - b) <= tol

import statistics

# Inputs: exercises.md T1 [ILLUSTRATIVE]; B-02 and A-06 from manuscript Table 23.8 / Section 23.7.
RUNS_GBPS = [329.6, 194.4, 318.4, 208.8, 324.0]    # node busbw over 8 rails, runs 1..5
CONTAMINATED = {2, 4}                                # runs overlapping the other team's job
B02_GBPS = 356.0                                     # 2-node median, clean
A06_PER_RAIL = 40.0                                  # design assumption, GB/s per rail
RAILS = 8


def main(out: Path) -> None:
    mean = statistics.mean(RUNS_GBPS)
    median = statistics.median(RUNS_GBPS)
    clean = [v for i, v in enumerate(RUNS_GBPS, 1) if i not in CONTAMINATED]
    clean_median = statistics.median(clean)
    loss_claimed = 100 * (1 - mean / B02_GBPS)        # 1 - 275.04 / 356
    loss_clean = 100 * (1 - clean_median / B02_GBPS)
    a06_node = A06_PER_RAIL * RAILS

    assert close(mean, 275.04, 0.005) and close(median, 318.4, 1e-9)   # key D.1
    assert close(mean / RAILS, 34.4, 0.05)
    assert close(clean_median, 324.0, 1e-9) and close(loss_clean, 9.0, 0.05)
    assert close(loss_claimed, 22.7, 0.05)
    assert clean_median > a06_node                                      # A-06 not contradicted

    result = {
        "id": "T1", "evidence_label": "ILLUSTRATIVE",
        "inputs": {"runs_GBps": RUNS_GBPS, "contaminated_runs": sorted(CONTAMINATED), "b02_GBps": B02_GBPS,
                   "a06_per_rail_GBps": A06_PER_RAIL},
        "steps": {"sorted": sorted(RUNS_GBPS), "sum": r(sum(RUNS_GBPS), 2), "clean_runs": clean},
        "answer": {"mean_GBps": r(mean, 2), "median_GBps": r(median, 2), "mean_per_rail_GBps": r(mean / RAILS, 2),
                   "claimed_loss_pct": r(loss_claimed, 1), "clean_median_GBps": r(clean_median, 2),
                   "clean_loss_vs_b02_pct": r(loss_clean, 1), "a06_node_GBps": r(a06_node, 1),
                   "a06_change_supported": False},
        "units": {"busbw": "GB/s", "loss": "%"},
    }
    md = [
        "# T1 — shared-fabric benchmark statistics (inputs `[ILLUSTRATIVE]`)", "",
        f"- sorted: {', '.join(f'{v:.1f}' for v in sorted(RUNS_GBPS))} GB/s",
        f"- mean = {sum(RUNS_GBPS):,.1f} / 5 = {mean:.2f} GB/s ({mean / RAILS:.1f} GB/s per rail); median = {median:.1f} GB/s",
        f"- claimed loss 1 − {mean:.1f} / {B02_GBPS:.0f} = {loss_claimed:.1f} %",
        f"- clean runs 1, 3, 5 median {clean_median:.1f} GB/s → {loss_clean:.1f} % below B-02; "
        f"A-06 = {a06_node:.0f} GB/s node busbw, not contradicted",
    ]
    write(out, result, md)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    main(ap.parse_args().out)
