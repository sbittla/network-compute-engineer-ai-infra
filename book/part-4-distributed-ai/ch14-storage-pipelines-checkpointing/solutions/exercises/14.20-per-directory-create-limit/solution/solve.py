"""14.20 -- Per-directory create limit: create time per checkpoint for three layouts. [MODELED]

Usage: python solve.py --out DIR
Inputs (prompt, [ILLUSTRATIVE]): 256 ranks; 1,025 files per rank (new image, Section 14.14) or 2 (old);
2,700 creates/s into one directory; 30,000 creates/s aggregate across many directories;
async completion latency L = 18.49 s (Section 14.12); budget 5 % of L.
"""
import argparse
import json
import math
from pathlib import Path

RANKS = 256
FILES_NEW, FILES_OLD = 1025, 2
PER_DIR_RATE = 2700.0       # creates/s into one directory
AGG_RATE = 30000.0          # creates/s across many directories
L_ASYNC_S = 18.49
BUDGET_FRAC = 0.05
KEY = {"a_one_dir_s": 97.2, "b_per_rank_dirs_s": 8.75, "c_old_format_s": 0.190, "d_max_files_per_rank": 9}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    n_new = RANKS * FILES_NEW
    a = n_new / PER_DIR_RATE
    per_dir_b = FILES_NEW / PER_DIR_RATE
    agg_b = n_new / AGG_RATE
    b = max(agg_b, per_dir_b)
    c = RANKS * FILES_OLD / PER_DIR_RATE
    budget = BUDGET_FRAC * L_ASYNC_S
    max_creates = budget * PER_DIR_RATE
    d = math.floor(max_creates / RANKS)

    # Key 14.20 (tolerance: 3 significant figures; d exact).
    assert abs(a - KEY["a_one_dir_s"]) < 0.05, a
    assert abs(b - KEY["b_per_rank_dirs_s"]) < 0.005, b
    assert abs(c - KEY["c_old_format_s"]) < 0.0005, c
    assert d == KEY["d_max_files_per_rank"], d

    result = {
        "inputs": {"ranks": RANKS, "files_per_rank_new": FILES_NEW, "files_per_rank_old": FILES_OLD,
                   "per_directory_creates_per_s": PER_DIR_RATE, "aggregate_creates_per_s": AGG_RATE,
                   "async_completion_s": L_ASYNC_S, "budget_fraction": BUDGET_FRAC},
        "steps": {"files_new": n_new, "b_per_directory_s": round(per_dir_b, 3), "b_aggregate_s": round(agg_b, 3),
                  "budget_s": round(budget, 4), "max_creates_in_budget": round(max_creates, 1),
                  "max_files_per_rank_exact": round(max_creates / RANKS, 3)},
        "answer": {"a_one_dir_s": round(a, 1), "b_per_rank_dirs_s": round(b, 2), "c_old_format_s": round(c, 3),
                   "d_max_files_per_rank": d},
        "units": {"time": "s", "files": "count"},
        "evidence_label": "[MODELED]",
    }
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# 14.20 result `[MODELED]`", "",
             "| Layout | Formula | Create time (s) |", "|---|---|---|",
             f"| (a) one directory, 1,025 files/rank | {n_new:,} / {PER_DIR_RATE:,.0f} | {a:.1f} |",
             f"| (b) one subdirectory per rank | max({n_new:,} / {AGG_RATE:,.0f}, {FILES_NEW:,} / {PER_DIR_RATE:,.0f}) "
             f"| {b:.2f} |",
             f"| (c) one directory, 2 files/rank | {RANKS * FILES_OLD} / {PER_DIR_RATE:,.0f} | {c:.3f} |", "",
             f"(d) budget {BUDGET_FRAC:.0%} x {L_ASYNC_S} s = {budget:.4f} s -> {max_creates:,.0f} creates -> "
             f"{max_creates / RANKS:.2f} per rank -> **{d} files per rank**.", ""]
    (out / "result.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
