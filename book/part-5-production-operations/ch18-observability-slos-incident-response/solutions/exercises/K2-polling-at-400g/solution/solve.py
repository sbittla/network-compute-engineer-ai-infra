"""K2 — Counter wrap, poll dilution, and maximum PFC pause at 400 Gb/s (Chapter 18).

Usage: python solve.py --out DIR
Writes result.json and result.md; asserts the answer key (solutions/exercises-key.md).
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def emit(out: Path, result: dict, md: str) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                                     encoding="utf-8", newline="\n")
    (out / "result.md").write_text(md.strip() + "\n", encoding="utf-8", newline="\n")


def close(value: float, key: float, tol: float, what: str) -> None:
    assert abs(value - key) <= tol, f"{what}: computed {value} vs key {key} (tol {tol})"


LINE_BPS = 400e9
BURST_S, POLL_S = 0.002, 60.0
PAUSE_QUANTA, QUANTUM_BITS = 65535, 512


def main(out: Path) -> None:
    bytes_per_s = LINE_BPS / 8
    wrap_s = 2 ** 32 / bytes_per_s
    wraps_per_s = 1 / wrap_s
    burst_b = bytes_per_s * BURST_S
    poll_b = bytes_per_s * POLL_S
    util = burst_b / poll_b
    pause_us = PAUSE_QUANTA * QUANTUM_BITS / LINE_BPS * 1e6
    close(wrap_s, 0.086, 0.0005, "wrap seconds")
    close(wraps_per_s, 11.6, 0.05, "wraps per second")
    close(util * 100, 0.0033, 0.00005, "poll utilization %")
    close(pause_us, 83.9, 0.05, "pause microseconds")
    result = {"exercise": "K2", "evidence_label": "[MODELED]",
              "inputs": {"line_rate_bps": LINE_BPS, "burst_s": BURST_S, "poll_s": POLL_S,
                         "pause_quanta": PAUSE_QUANTA, "quantum_bits": QUANTUM_BITS},
              "answer": {"a_wrap_s": round(wrap_s, 4), "a_wraps_per_s": round(wraps_per_s, 2),
                         "b_burst_bytes": burst_b, "b_poll_bytes": poll_b, "b_utilization_pct": round(util * 100, 5),
                         "c_max_pause_us": round(pause_us, 2)},
              "units": {"time": "s / µs", "data": "bytes"}}
    md = f"""
# K2 result `[MODELED]`

- (a) 2^32 B / {bytes_per_s:.3g} B/s = {wrap_s:.4f} s → {wraps_per_s:.1f} wraps/s
- (b) {burst_b:.3g} B / {poll_b:.3g} B = {util * 100:.4f} %
- (c) {PAUSE_QUANTA} × {QUANTUM_BITS} bit / 400 Gb/s = {pause_us:.1f} µs
"""
    emit(out, result, md)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    main(Path(ap.parse_args().out))
