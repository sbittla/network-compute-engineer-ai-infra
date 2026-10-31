#!/usr/bin/env python3
"""3.13: snapshot volume for a full ORION-XL sweep, from the supplied snapshot sizes.

Usage: python solve.py --out DIR
Reads the sizes of lab/data/snapshots/*.json (LF-normalized so the result does not depend on checkout
line endings). Cost figures from manuscript Section 3.11 and docs/REFERENCE_CLUSTER.md [ILLUSTRATIVE].
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
from pathlib import Path


def house(line: str) -> str:
    """Apply the book's copyedit house style to generated Markdown (x -> ×, ~ -> ≈, '40 %', µs)."""
    line = re.sub(r"(\d)%", r"\1 %", line)
    line = line.replace(" x ", " × ")
    line = re.sub(r"(\d)x\b", r"\1×", line)
    line = re.sub(r"~ ?", "≈ ", line)
    line = re.sub(r"(\d) us\b", r"\1 µs", line)
    return line.replace("scaleout", "scale-out").replace("scaleup", "scale-up")

SNAPS = Path(__file__).resolve().parents[4] / "lab" / "data" / "snapshots"
NODES, DAYS = 512, 365
COMPRESSION = (5, 10)
XL_GPUS, STRAGGLER_FRACTION = 4096, 0.0551     # Section 3.11 Gen3 x8 lost fraction
FALSE_DRAIN_GPU_H = 8 * 1.0                    # one node, 1 h to inspect and return
KEY = {"median_KB": 141.0, "sweep_MB": 72.0, "year_GB": 26.0}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    sizes = {p.stem: len(p.read_bytes().replace(b"\r\n", b"\n")) for p in sorted(SNAPS.glob("*.json"))}
    kb = {k: v / 1000 for k, v in sizes.items()}
    median = statistics.median(kb.values())
    sweep_mb = NODES * median / 1000
    year_gb = sweep_mb * DAYS / 1000
    compressed = [round(year_gb / c, 2) for c in COMPRESSION]
    straggler_gpu_h_per_h = XL_GPUS * STRAGGLER_FRACTION
    got = {"median_KB": median, "sweep_MB": sweep_mb, "year_GB": year_gb}
    for k, v in KEY.items():
        assert abs(got[k] - v) <= 0.03 * v, (k, got[k], v)
    assert len(sizes) == 6 and straggler_gpu_h_per_h > 20 * FALSE_DRAIN_GPU_H
    result = {"evidence": "[SIMULATED] snapshot sizes; volumes [MODELED]",
              "answer": {"snapshot_KB": {k: round(v, 1) for k, v in kb.items()}, "median_KB": round(median, 1),
                         "min_KB": round(min(kb.values()), 1), "max_KB": round(max(kb.values()), 1),
                         "sweep_MB": round(sweep_mb, 1), "daily_sweeps_GB_per_year": round(year_gb, 1),
                         "compressed_GB_per_year_range": compressed,
                         "missed_straggler_gpu_h_per_hour_xl": round(straggler_gpu_h_per_h, 1),
                         "false_drain_gpu_h": FALSE_DRAIN_GPU_H},
              "units": {"size": "KB/MB/GB (SI)", "cost": "GPU-hours"}}
    md = ["# 3.13 — snapshot volume `[MODELED]`", "",
          f"- supplied snapshots: {min(kb.values()):.1f}-{max(kb.values()):.1f} KB, median {median:.1f} KB",
          f"- one sweep: {NODES} x {median:.1f} KB = {sweep_mb:.1f} MB; daily for a year: {year_gb:.1f} GB "
          f"({compressed[1]}-{compressed[0]} GB compressed)",
          f"- missed straggler at ORION-XL: {straggler_gpu_h_per_h:.0f} GPU-h per hour vs false drain {FALSE_DRAIN_GPU_H:.0f} GPU-h"]
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "result.md").write_text("\n".join(house(l) for l in md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
