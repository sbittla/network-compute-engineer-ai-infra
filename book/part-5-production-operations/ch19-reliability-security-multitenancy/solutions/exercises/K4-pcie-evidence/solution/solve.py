"""K4 — PCIe Gen5 bandwidth at x16 versus a downtrained x8 link (Chapter 19, Section 19.3).

    python solve.py --out DIR

Gen5 signals at 32 GT/s per lane with 128b/130b encoding. Achievable fractions follow
docs/VERIFIED_FACTS.md ("PCIe Gen5 achievable bandwidth": x16 ≈ 400–440 Gb/s = 50–55 GB/s;
x8 ≈ 200–220 Gb/s = 25–27.5 GB/s). The NIC is a 400 Gb/s backend NIC (Reference Cluster).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

GT_PER_LANE = 32.0             # PCIe Gen5, GT/s per lane (LnkCap/LnkSta "Speed 32GT/s")
ENCODING = 128.0 / 130.0       # Gen3+ line code
ACHIEVABLE_X16_GBPS = (50.0, 55.0)   # VERIFIED_FACTS.md, GB/s per direction
NIC_GBITS = 400.0              # backend NIC line rate, Gb/s

# solutions/exercises-key.md, K4: x16 ≈ 63 GB/s; x8 ≈ 31.5 GB/s theoretical, ≈ 25–27 achievable
KEY_X16, KEY_X8 = 63.0, 31.5
TOL_GBS = 0.1


def theoretical_gbs(width: int) -> float:
    return GT_PER_LANE * width * ENCODING / 8.0   # GB/s per direction


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    x16, x8 = theoretical_gbs(16), theoretical_gbs(8)
    ach_x8 = tuple(v * 8 / 16 for v in ACHIEVABLE_X16_GBPS)
    nic_gbs = NIC_GBITS / 8.0
    assert abs(x16 - KEY_X16) < TOL_GBS + 0.05, x16
    assert abs(x8 - KEY_X8) < TOL_GBS, x8
    assert 25.0 <= ach_x8[0] and ach_x8[1] <= 27.5, ach_x8
    assert x8 < nic_gbs < x16, "x8 must fall below the NIC line rate"

    result = {
        "exercise": "K4",
        "inputs": {"gt_per_lane": GT_PER_LANE, "encoding": "128b/130b", "nic_gbits": NIC_GBITS,
                   "achievable_x16_gbs": list(ACHIEVABLE_X16_GBPS)},
        "steps": {"x16_theoretical_gbs": round(x16, 2), "x8_theoretical_gbs": round(x8, 2),
                  "x8_achievable_gbs": [round(v, 2) for v in ach_x8], "nic_line_rate_gbs": round(nic_gbs, 2),
                  "x8_fraction_of_nic": round(x8 / nic_gbs, 3)},
        "answer": "x16 ≈ 63 GB/s per direction (≈ 50–55 achievable); x8 ≈ 31.5 GB/s (≈ 25–27.5 achievable), "
                  "below the 50 GB/s a 400 Gb/s NIC needs: the rail runs at roughly half rate",
        "units": "GB/s per direction",
        "evidence_label": "[MODELED] from [VENDOR-SPEC] link rates",
        "tolerance_gbs": TOL_GBS,
    }
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                                     encoding="utf-8")
    md = ["# K4 — PCIe x16 vs x8 `[MODELED]`", "",
          "| Link | Theoretical (GB/s/dir) | Achievable (GB/s/dir) |", "|---|---|---|",
          f"| Gen5 x16 | 32 × 16 × 128/130 / 8 = {x16:.1f} | {ACHIEVABLE_X16_GBPS[0]:.0f}–{ACHIEVABLE_X16_GBPS[1]:.0f} |",
          f"| Gen5 x8 | 32 × 8 × 128/130 / 8 = {x8:.1f} | {ach_x8[0]:.0f}–{ach_x8[1]:.1f} |", "",
          f"A 400 Gb/s NIC needs {nic_gbs:.0f} GB/s; at x8 it is capped at ≈ {x8 / nic_gbs * 100:.0f} % of line rate "
          "theoretical, about half in practice."]
    (out / "result.md").write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
