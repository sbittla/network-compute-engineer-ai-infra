"""K2 — PFC pause quantum and maximum single-frame pause at 100 and 400 Gb/s, plus the refresh rate.

Usage: python solve.py --out DIR

1 quantum = 512 bit-times (IEEE 802.1Qbb, manuscript Section 9.4); max quanta per frame = 65,535.
The refresh rate assumes the pausing device re-sends at half the pause lifetime (illustrative
"half-life refresh" policy; real refresh policy is implementation-specific). [MODELED]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

QUANTUM_BITS = 512
MAX_QUANTA = 65_535
RATES_GBPS = (100, 400)
KEY = {100: {"quantum_ns": 5.12, "max_us": 335.5}, 400: {"quantum_ns": 1.28, "max_us": 83.9}}
KEY_REFRESH_400 = 23_800   # frames/s, solutions/exercises-key.md K2 (approximate)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    res = {}
    for r in RATES_GBPS:
        q_ns = QUANTUM_BITS / r                     # bits / (Gb/s) = ns
        max_us = MAX_QUANTA * q_ns / 1000
        refresh = 1 / (max_us / 2 * 1e-6)           # frames/s with half-life refresh
        res[r] = {"quantum_ns": round(q_ns, 4), "max_pause_us": round(max_us, 2), "half_life_refresh_per_s": round(refresh)}
        assert abs(q_ns - KEY[r]["quantum_ns"]) < 1e-9 and abs(max_us - KEY[r]["max_us"]) < 0.05, (r, q_ns, max_us)
    assert abs(res[400]["half_life_refresh_per_s"] - KEY_REFRESH_400) / KEY_REFRESH_400 < 0.01

    result = {"exercise": "K2", "evidence_label": "[MODELED]",
              "inputs": {"quantum_bits": QUANTUM_BITS, "max_quanta": MAX_QUANTA, "rates_gbps": list(RATES_GBPS)},
              "answer": {f"{r}G": v for r, v in res.items()},
              "units": "ns, µs, frames/s", "tolerance": "±0.05 µs; refresh ±1 %"}
    rows = "\n".join(f"| {r} Gb/s | 512 / {r} = {v['quantum_ns']} ns | 65,535 × {v['quantum_ns']} ns = {v['max_pause_us']} µs | ≈ {v['half_life_refresh_per_s']:,} /s |"
                     for r, v in res.items())
    md = f"""# K2 — result `[MODELED]`

| Rate | Quantum | Max single-frame pause | Sustained-pause frame rate (half-life refresh) |
|---|---|---|---|
{rows}
"""
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (out / "result.md").write_text(md, encoding="utf-8", newline="\n")
    print("K2 ok")


if __name__ == "__main__":
    main()
