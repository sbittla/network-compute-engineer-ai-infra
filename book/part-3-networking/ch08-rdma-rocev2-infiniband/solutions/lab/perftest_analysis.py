#!/usr/bin/env python3
"""perftest results analyzer (Chapter 8 lab) -- REFERENCE SOLUTION.

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
    df = pd.DataFrame(_table_rows(text, len(BW_COLS)), columns=BW_COLS)
    df[["bytes", "iterations"]] = df[["bytes", "iterations"]].astype(int)
    return df


def parse_lat(text: str) -> pd.DataFrame:
    """Parse ib_write_lat output into a DataFrame with ``LAT_COLS`` (bytes as int, times in us)."""
    df = pd.DataFrame(_table_rows(text, len(LAT_COLS)), columns=LAT_COLS)
    df[["bytes", "iterations"]] = df[["bytes", "iterations"]].astype(int)
    return df


def bw_plateau_gbps(bw: pd.DataFrame) -> float:
    """Median average bandwidth (Gb/s) over message sizes >= 1 MiB."""
    return float(bw.loc[bw["bytes"] >= PLATEAU_MIN_BYTES, "bw_avg_gbps"].median())


def half_bw_bytes(bw: pd.DataFrame) -> int:
    """Smallest message size (bytes) whose average bandwidth reaches half the plateau (n_1/2)."""
    half = 0.5 * bw_plateau_gbps(bw)
    return int(bw.loc[bw["bw_avg_gbps"] >= half, "bytes"].min())


def summarize(perftest_dir: Path) -> pd.DataFrame:
    """Return one row per (pair, rail) with columns:

    ``pair`` ("n05-n06"), ``rail`` (int), ``plateau_gbps``, ``half_bw_bytes``, ``lat_typical_us``
    (t_typical at 2 B), ``p99_us`` and ``p999_us`` (medians over sizes <= 4 KiB), plus boolean
    ``bw_flag`` and ``tail_flag`` computed against fleet medians (see module constants).
    Sorted by pair then rail.
    """
    recs: dict[tuple[str, int], dict] = {}
    for f in sorted(Path(perftest_dir).glob("*.txt")):
        m = NAME_RE.search(f.name)
        if not m:
            continue
        kind, a, b, rail = m.group(1), m.group(2), m.group(3), int(m.group(4))
        key = (f"n{a}-n{b}", rail)
        rec = recs.setdefault(key, {"pair": key[0], "rail": rail})
        text = f.read_text(encoding="utf-8")
        if kind == "bw":
            bw = parse_bw(text)
            rec["plateau_gbps"] = bw_plateau_gbps(bw)
            rec["half_bw_bytes"] = half_bw_bytes(bw)
        else:
            lat = parse_lat(text)
            small = lat[lat["bytes"] <= SMALL_MAX_BYTES]
            rec["lat_typical_us"] = float(lat.loc[lat["bytes"] == lat["bytes"].min(), "t_typical_us"].iloc[0])
            rec["p99_us"] = float(small["p99_us"].median())
            rec["p999_us"] = float(small["p999_us"].median())
    df = pd.DataFrame(list(recs.values())).sort_values(["pair", "rail"]).reset_index(drop=True)
    df["bw_flag"] = df["plateau_gbps"] < BW_FLAG_RATIO * df["plateau_gbps"].median()
    df["tail_flag"] = df["p999_us"] > TAIL_FLAG_RATIO * df["p999_us"].median()
    return df


def pcie_downgrades(csv_path: Path) -> pd.DataFrame:
    """Return rows of the PCIe capture whose negotiated width or speed (LnkSta) is below capability
    (LnkCap). Columns: host, device, bdf, lnkcap, lnksta."""
    df = pd.read_csv(csv_path)

    def parse(s: str) -> tuple[float, int]:
        sp = re.search(r"Speed ([\d.]+)GT/s", s)
        wd = re.search(r"Width x(\d+)", s)
        return (float(sp.group(1)) if sp else 0.0, int(wd.group(1)) if wd else 0)

    cap = df["lnkcap"].map(parse)
    sta = df["lnksta"].map(parse)
    mask = [s[0] < c[0] or s[1] < c[1] for c, s in zip(cap, sta)]
    return df[mask].reset_index(drop=True)


def render(df: pd.DataFrame, pcie: pd.DataFrame) -> str:
    lines = ["# perftest analysis", "",
             f"Fleet median plateau: {df['plateau_gbps'].median():.1f} Gb/s; "
             f"fleet median small-message p99.9: {df['p999_us'].median():.2f} us", "",
             "| Pair | Rail | Plateau Gb/s | n1/2 B | t_typ 2B us | p99 us | p99.9 us | Flags |",
             "|---|---|---|---|---|---|---|---|"]
    for r in df.itertuples():
        flags = ",".join(x for x, on in (("BW", r.bw_flag), ("TAIL", r.tail_flag)) if on) or "-"
        lines.append(f"| {r.pair} | {r.rail} | {r.plateau_gbps:.1f} | {r.half_bw_bytes} | {r.lat_typical_us:.2f} | "
                     f"{r.p99_us:.2f} | {r.p999_us:.2f} | {flags} |")
    lines += ["", "PCIe links below capability:"]
    lines += [f"- {r.host} {r.device} {r.bdf}: {r.lnksta} (cap {r.lnkcap})" for r in pcie.itertuples()] or ["- none"]
    return "\n".join(lines) + "\n"


def main() -> None:
    here = Path(__file__).resolve().parent
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--perftest", type=Path, default=here.parent.parent / "lab" / "data" / "perftest")
    a = p.parse_args()
    df = summarize(a.perftest)
    print(render(df, pcie_downgrades(a.perftest / "pcie_link.csv")))


if __name__ == "__main__":
    main()
