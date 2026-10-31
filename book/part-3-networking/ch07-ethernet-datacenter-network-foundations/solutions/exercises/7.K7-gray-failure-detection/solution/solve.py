"""7.K7 — Gray-failure detection time: BFD 300 ms x 3 versus BGP 3 s / 9 s timers.

Usage: python solve.py --out DIR

Timers from manuscript Table 7.7. A gray failure keeps the link up, so loss-of-signal never fires;
detection waits for the liveness protocol to miss `multiplier` consecutive packets (BFD) or for the
BGP hold timer to expire. [ILLUSTRATIVE timers; MODELED arithmetic]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

BFD_TX_INTERVAL_MS = 300
BFD_MULTIPLIER = 3
BGP_KEEPALIVE_S, BGP_HOLD_S = 3, 9
KEY = {"bfd_s": 0.9, "bgp_s": 9.0}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    bfd_s = BFD_TX_INTERVAL_MS * BFD_MULTIPLIER / 1000
    bgp_worst_s = float(BGP_HOLD_S)                       # hold timer restarts on every keepalive
    bgp_best_s = float(BGP_HOLD_S - BGP_KEEPALIVE_S)      # failure just before a keepalive was due
    ratio = bgp_worst_s / bfd_s

    assert abs(bfd_s - KEY["bfd_s"]) < 1e-9 and abs(bgp_worst_s - KEY["bgp_s"]) < 1e-9

    result = {
        "exercise": "7.K7", "evidence_label": "[MODELED]",
        "inputs": {"bfd_interval_ms": BFD_TX_INTERVAL_MS, "bfd_multiplier": BFD_MULTIPLIER,
                   "bgp_keepalive_s": BGP_KEEPALIVE_S, "bgp_hold_s": BGP_HOLD_S},
        "steps": {"bgp_detection_range_s": [bgp_best_s, bgp_worst_s], "bgp_over_bfd": round(ratio, 1)},
        "answer": {"bfd_detection_s": bfd_s, "bgp_detection_upper_bound_s": bgp_worst_s},
        "units": "s", "tolerance": "1e-9 s",
    }
    md = f"""# 7.K7 — result

- BFD: {BFD_TX_INTERVAL_MS} ms × {BFD_MULTIPLIER} = **{bfd_s:.1f} s** `[MODELED]`
- BGP hold timer ({BGP_KEEPALIVE_S} s / {BGP_HOLD_S} s): between {bgp_best_s:.0f} s and **{bgp_worst_s:.0f} s** after the last keepalive received
- BGP-only detection is ≈ {ratio:.0f}× slower
"""
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (out / "result.md").write_text(md, encoding="utf-8", newline="\n")
    print("7.K7 ok:", bfd_s, bgp_worst_s)


if __name__ == "__main__":
    main()
