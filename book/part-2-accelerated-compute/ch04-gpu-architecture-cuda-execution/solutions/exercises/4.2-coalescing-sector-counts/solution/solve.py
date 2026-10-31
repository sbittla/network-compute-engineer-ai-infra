"""Exercise 4.2: 32-byte sectors fetched by one warp loading one 4-byte float per thread.

Usage: python solve.py --out DIR
Inputs are the prompt's parameters (manuscript Section 4.4: sector = 32 B, warp = 32 threads).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

WARP = 32          # threads per warp (Table 4.1)
ELEM_B = 4         # one FP32 value per thread (prompt)
SECTOR_B = 32      # L2/DRAM access granularity (Section 4.4)
STRIDES = {"a_consecutive": 1, "b_stride_2": 2, "c_stride_32": 32}
KEY = {"a_consecutive": (4, 1.0), "b_stride_2": (8, 0.5), "c_stride_32": (32, 0.125)}  # exercises-key.md 4.2


def sectors_touched(stride_elems: int) -> int:
    """Count distinct 32-B sectors touched by the warp's 32 addresses (base aligned to 128 B)."""
    addrs = [t * stride_elems * ELEM_B for t in range(WARP)]
    return len({a // SECTOR_B for a in addrs})


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    useful = WARP * ELEM_B
    cases = {}
    for name, s in STRIDES.items():
        n = sectors_touched(s)
        fetched = n * SECTOR_B
        cases[name] = {"stride_elements": s, "sectors": n, "bytes_fetched": fetched,
                       "useful_bytes": useful, "useful_fraction": round(useful / fetched, 4)}
        k_sectors, k_frac = KEY[name]
        assert n == k_sectors, (name, n)
        assert abs(useful / fetched - k_frac) < 1e-9, (name, useful / fetched)
    result = {"exercise": "4.2", "evidence_label": "MODELED", "units": {"bytes": "B", "fraction": "1"},
              "inputs": {"warp_threads": WARP, "element_bytes": ELEM_B, "sector_bytes": SECTOR_B},
              "answer": cases}
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# Exercise 4.2 — sectors per warp load `[MODELED]`", "",
             f"Useful bytes per warp = {WARP} × {ELEM_B} B = {useful} B.", "",
             "| Case | Stride (elements) | Sectors | Bytes fetched | Useful fraction |", "|---|---|---|---|---|"]
    for name, c in cases.items():
        lines.append(f"| {name} | {c['stride_elements']} | {c['sectors']} | {c['bytes_fetched']:,} B | "
                     f"{c['useful_fraction'] * 100:.1f} % |")
    (out / "result.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
