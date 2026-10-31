"""Exercise 4.7: Little's law for the layernorm backward kernel vs the bytes HBM needs in flight.

Usage: python solve.py --out DIR
Inputs: Section 4.3 (600 ns loaded latency [ILLUSTRATIVE], 3.35 TB/s, 132 SMs); lab kernel
layernorm_bwd_fused_kernel (256 threads, 168 registers -> 8 warps resident per SM, 12.5 %);
about 3.25 outstanding 128-B requests per warp (vectorized 16-B loads), as stated in the key.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HBM_BPS = 3.35e12
LATENCY_S = 600e-9
SMS = 132
WARPS_RESIDENT = 8         # 12.5 % of 64 warps (one 256-thread block per SM)
REQ_PER_WARP = 3.25
REQ_B = 128
KEY_FRACTION = 0.22        # exercises-key.md 4.7: "3.3 / 15.2 ~ 22 % of HBM bandwidth"
KEY_NEEDED_B = 15_200      # "~ 15.2 KB needed"
TOL = 0.01                 # absolute tolerance on the fraction; 1 % relative on bytes


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    needed_gpu = HBM_BPS * LATENCY_S
    needed_sm = needed_gpu / SMS
    in_flight = WARPS_RESIDENT * REQ_PER_WARP * REQ_B
    frac = in_flight / needed_sm
    one_req = WARPS_RESIDENT * 1 * REQ_B / needed_sm
    assert abs(needed_sm - KEY_NEEDED_B) / KEY_NEEDED_B < 0.01, needed_sm
    assert abs(frac - KEY_FRACTION) < TOL, frac
    assert abs(one_req - 0.07) < 0.005, one_req
    res = {"exercise": "4.7", "evidence_label": "MODELED",
           "inputs": {"hbm_Bps": HBM_BPS, "latency_s": LATENCY_S, "sms": SMS, "warps_resident": WARPS_RESIDENT,
                      "requests_per_warp": REQ_PER_WARP, "request_bytes": REQ_B},
           "steps": {"needed_in_flight_gpu_B": round(needed_gpu), "needed_in_flight_per_sm_B": round(needed_sm, 1),
                     "in_flight_per_sm_B": in_flight, "fraction_one_request_per_warp": round(one_req, 4)},
           "answer": {"fraction_of_hbm": round(frac, 4), "attainable_TBps": round(frac * HBM_BPS / 1e12, 3)},
           "units": {"bytes": "B", "bandwidth": "TB/s"}}
    (out / "result.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = f"""# Exercise 4.7 — Little's law for the layernorm backward `[MODELED]`

- Needed in flight (GPU) = 3.35 × 10¹² B/s × 600 × 10⁻⁹ s = {needed_gpu:,.0f} B
- Needed per SM = {needed_gpu:,.0f} / {SMS} = {needed_sm:,.1f} B
- Layernorm in flight per SM = {WARPS_RESIDENT} warps × {REQ_PER_WARP} × {REQ_B} B = {in_flight:,.0f} B
- Fraction of HBM bandwidth = {in_flight:,.0f} / {needed_sm:,.1f} = {frac * 100:.1f} % (≈ {frac * 3.35:.2f} TB/s)
- With one 128-B request per warp: {one_req * 100:.1f} %
"""
    (out / "result.md").write_text(md, encoding="utf-8")


if __name__ == "__main__":
    main()
