#!/usr/bin/env python3
"""perftest results analyzer (Chapter 8 lab) -- STARTER (complete the TODOs).

Parses ``ib_write_bw -a --report_gbits`` and ``ib_write_lat -a`` outputs for every node pair and
rail, summarises bandwidth versus message size and latency percentiles, and flags pairs that
underperform the fleet. Correlates flags with a PCIe link-status capture.

File naming: ``bw_nAA-nBB_railR.txt`` / ``lat_nAA-nBB_railR.txt``.

Usage:
    python perftest_analysis.py --perftest ../../lab/data/perftest
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd

BW_COLS = ["bytes", "iterations", "bw_peak_gbps", "bw_avg_gbps", "msg_rate_mpps"]
LAT_COLS = ["bytes", "iterations", "t_min_us", "t_max_us", "t_typical_us", "t_avg_us", "t_stdev_us",
            "p99_us", "p999_us"]
NAME_RE = re.compile(r"(bw|lat)_n(\d+)-n(\d+)_rail(\d+)\.txt$")

PLATEAU_MIN_BYTES = 1 << 20      # sizes >= 1 MiB define the bandwidth plateau
SMALL_MAX_BYTES = 4096           # sizes <= 4 KiB define small-message latency
BW_FLAG_RATIO = 0.90             # flag plateau < 90 % of the fleet median
TAIL_FLAG_RATIO = 3.0            # flag small-message p99.9 > 3x the fleet median


def _table_rows(text: str, ncols: int) -> list[list[float]]:
    rows = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) == ncols and parts[0].isdigit():
            try:
                rows.append([float(x) for x in parts])
            except ValueError:
                continue
    return rows


def parse_bw(text: str) -> pd.DataFrame:
    """Parse ib_write_bw output into a DataFrame with ``BW_COLS`` (bytes as int, Gb/s, Mpps)."""
    # TODO: implement parse_bw (see the docstring and lab/README.md, Task list).
    raise NotImplementedError("parse_bw")


def parse_lat(text: str) -> pd.DataFrame:
    """Parse ib_write_lat output into a DataFrame with ``LAT_COLS`` (bytes as int, times in us)."""
    # TODO: implement parse_lat (see the docstring and lab/README.md, Task list).
    raise NotImplementedError("parse_lat")


def bw_plateau_gbps(bw: pd.DataFrame) -> float:
    """Median average bandwidth (Gb/s) over message sizes >= 1 MiB."""
    # TODO: implement bw_plateau_gbps (see the docstring and lab/README.md, Task list).
    raise NotImplementedError("bw_plateau_gbps")


def half_bw_bytes(bw: pd.DataFrame) -> int:
    """Smallest message size (bytes) whose average bandwidth reaches half the plateau (n_1/2)."""
    # TODO: implement half_bw_bytes (see the docstring and lab/README.md, Task list).
    raise NotImplementedError("half_bw_bytes")


def summarize(perftest_dir: Path) -> pd.DataFrame:
    """Return one row per (pair, rail) with columns:

    ``pair`` ("n05-n06"), ``rail`` (int), ``plateau_gbps``, ``half_bw_bytes``, ``lat_typical_us``
    (t_typical at 2 B), ``p99_us`` and ``p999_us`` (medians over sizes <= 4 KiB), plus boolean
    ``bw_flag`` and ``tail_flag`` computed against fleet medians (see module constants).
    Sorted by pair then rail.
    """
    # TODO: implement summarize (see the docstring and lab/README.md, Task list).
    raise NotImplementedError("summarize")


def pcie_downgrades(csv_path: Path) -> pd.DataFrame:
    """Return rows of the PCIe capture whose negotiated width or speed (LnkSta) is below capability
    (LnkCap). Columns: host, device, bdf, lnkcap, lnksta."""
    # TODO: implement pcie_downgrades (see the docstring and lab/README.md, Task list).
    raise NotImplementedError("pcie_downgrades")


def render(df: pd.DataFrame, pcie: pd.DataFrame) -> str:
    # TODO: implement render (see the docstring and lab/README.md, Task list).
    raise NotImplementedError("render")


def main() -> None:
    here = Path(__file__).resolve().parent
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--perftest", type=Path, default=here.parent.parent / "lab" / "data" / "perftest")
    a = p.parse_args()
    df = summarize(a.perftest)
    print(render(df, pcie_downgrades(a.perftest / "pcie_link.csv")))


if __name__ == "__main__":
    main()
