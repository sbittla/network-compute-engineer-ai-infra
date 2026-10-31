"""13.5 -- DP reduction overlap window with PP + gradient accumulation (W-TRAIN). [MODELED]

Usage: python solve.py --out DIR
Inputs: manuscript Section 13.6 and the Chapter 11 step model.
"""
import argparse
import json
from pathlib import Path

COMPUTE_S = 13.9          # pipeline compute per step (Chapter 11)
MICRO_BATCHES = 128       # micro-batches per step
BACKWARD_SHARE = 2 / 3    # backward is ≈ 2× forward FLOPs
DP_BYTES = 7.66e9         # DP bytes per GPU per step (Table 13.1)
NIC_BPS = 45e9            # effective NIC bandwidth, B/s (Section 13.11)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    per_mb = COMPUTE_S / MICRO_BATCHES
    window = per_mb * BACKWARD_SHARE
    t_comm = DP_BYTES / NIC_BPS
    exposed = max(0.0, t_comm - window)
    # Key 13.5: window ≈ 72 ms vs ≈ 170 ms DP -> ≈ 100 ms exposed (manuscript: ≈ 98 ms). Tolerance 1-2 ms.
    assert abs(window * 1e3 - 72) < 1.0, window
    assert abs(t_comm * 1e3 - 170) < 1.0, t_comm
    assert abs(exposed * 1e3 - 98) < 2.0, exposed

    result = {
        "inputs": {"compute_s": COMPUTE_S, "micro_batches": MICRO_BATCHES,
                   "backward_share": round(BACKWARD_SHARE, 4), "dp_bytes": DP_BYTES, "nic_Bps": NIC_BPS},
        "steps": {"per_microbatch_ms": round(per_mb * 1e3, 1), "window_ms": round(window * 1e3, 1),
                  "dp_comm_ms": round(t_comm * 1e3, 1)},
        "answer": {"window_ms": round(window * 1e3, 1), "exposed_ms": round(exposed * 1e3, 1)},
        "units": {"time": "ms"},
        "evidence_label": "[MODELED]",
    }
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = (f"# 13.5 result `[MODELED]`\n\n"
          f"- Window = {COMPUTE_S} s / {MICRO_BATCHES} × 2/3 = {per_mb*1e3:.1f} ms × 2/3 = {window*1e3:.1f} ms\n"
          f"- DP all-reduce = {DP_BYTES/1e9:.2f} GB / {NIC_BPS/1e9:.0f} GB/s = {t_comm*1e3:.1f} ms\n"
          f"- Exposed = max(0, {t_comm*1e3:.1f} - {window*1e3:.1f}) = {exposed*1e3:.1f} ms per step\n")
    (out / "result.md").write_text(md, encoding="utf-8")


if __name__ == "__main__":
    main()
