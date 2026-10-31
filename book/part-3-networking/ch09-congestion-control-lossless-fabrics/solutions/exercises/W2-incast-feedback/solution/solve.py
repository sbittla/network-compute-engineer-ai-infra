"""W2 — 16:1 incast into a 400 Gb/s port: fill time, feedback timing, completion bound, DCQCN halvings, BDP.

Usage: python solve.py --out DIR

Prompt parameters: 16 senders x 2 MB; threshold 1.5 MB; buffer share 6 MB; base RTT 6 us; CNP interval
N = 50 us; alpha = 1 (each cut halves the rate). r = 50 KB/us. Sections 9.6-9.7. [MODELED]
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

SENDERS, BURST_MB = 16, 2
R_KB_PER_US = 50.0              # 400 Gb/s = 50 GB/s = 50 KB/us (decimal units)
THRESH_KB, SHARE_KB = 1500, 6000
RTT_US, N_US = 6.0, 50.0
KEY = {"a": 750, "b": 2.0, "d": 640, "e_halvings": 4, "e_us": 156, "e_pct": 24, "f_kb": 300}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    excess = (SENDERS - 1) * R_KB_PER_US
    t_thresh = THRESH_KB / excess
    t_share = SHARE_KB / excess
    feedback_before = RTT_US < t_thresh
    total_b = SENDERS * BURST_MB * 1e6
    d_us = total_b / (R_KB_PER_US * 1000)
    halvings = math.ceil(math.log2(SENDERS))         # aggregate must fall 16x to the drain rate

    # Simulate the per-flow halving schedule: first cut ~1 RTT after marking starts, then one per N.
    rate, t, cuts = float(SENDERS), RTT_US, 0        # aggregate rate in units of the drain rate
    while rate > 1.0 + 1e-12:
        rate /= 2
        cuts += 1
        if rate > 1.0 + 1e-12:
            t += N_US
    e_us = t
    e_pct = 100 * e_us / d_us
    e_alt_us = halvings * N_US                        # accepted alternative: 4 x 50 us
    bdp_kb = R_KB_PER_US * RTT_US

    assert excess == KEY["a"] and abs(t_thresh - KEY["b"]) < 1e-9 and not feedback_before
    assert abs(d_us - KEY["d"]) < 1e-9 and halvings == cuts == KEY["e_halvings"]
    assert abs(e_us - KEY["e_us"]) < 1e-9 and abs(e_pct - KEY["e_pct"]) < 0.5 and 150 <= e_alt_us <= 210
    assert bdp_kb == KEY["f_kb"] and bdp_kb < THRESH_KB

    result = {"exercise": "W2", "evidence_label": "[MODELED]",
              "inputs": {"senders": SENDERS, "burst_mb": BURST_MB, "rate_kb_per_us": R_KB_PER_US, "threshold_kb": THRESH_KB,
                         "share_kb": SHARE_KB, "rtt_us": RTT_US, "cnp_interval_us": N_US, "alpha": 1},
              "steps": {"share_fill_us_without_pfc": t_share, "alternative_e_us": e_alt_us,
                        "alternative_e_pct": round(100 * e_alt_us / d_us, 1)},
              "answer": {"a_excess_kb_per_us": excess, "b_time_to_threshold_us": t_thresh,
                         "c_feedback_before_threshold": feedback_before, "d_min_completion_us": d_us,
                         "e_halvings": halvings, "e_time_us": e_us, "e_pct_of_d": round(e_pct, 1),
                         "f_bdp_kb": bdp_kb, "f_kmin_upper_bound_kb": bdp_kb},
              "units": "KB/us, us, KB", "tolerance": "1e-9 (e: ±0.5 percentage points)"}
    md = f"""# W2 — result `[MODELED]`

- (a) ({SENDERS} − 1) × {R_KB_PER_US:.0f} KB/µs = **{excess:.0f} KB/µs**
- (b) {THRESH_KB:,} KB / {excess:.0f} KB/µs = **{t_thresh:.1f} µs**
- (c) feedback needs ≥ 1 RTT = {RTT_US:.0f} µs > {t_thresh:.1f} µs → **no** (the 6 MB share would fill in {t_share:.0f} µs without PFC)
- (d) {SENDERS} × {BURST_MB} MB / 50 GB/s = **{d_us:.0f} µs**
- (e) log₂ {SENDERS} = **{halvings} halvings**; ≈ {RTT_US:.0f} + 3 × {N_US:.0f} = **{e_us:.0f} µs** = {e_pct:.0f} % of (d) (alternative 4 × 50 = {e_alt_us:.0f} µs ≈ {100 * e_alt_us / d_us:.0f} %)
- (f) BDP = 50 KB/µs × {RTT_US:.0f} µs = **{bdp_kb:.0f} KB**; Kmin ≤ 1 BDP, well below 1.5 MB
"""
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (out / "result.md").write_text(md, encoding="utf-8", newline="\n")
    print("W2 ok")


if __name__ == "__main__":
    main()
