#!/usr/bin/env python3
"""T1 — test ranking scores and the NCCL ACK-timeout arithmetic for the periodic-stall case.

Usage: python solve.py --out DIR   (writes result.json and result.md; asserts the answer key)
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path


def r(x: float, nd: int = 4) -> float:
    return round(float(x), nd)


def write(out: Path, result: dict, md: str) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                                     encoding="utf-8")
    (out / "result.md").write_text(md.rstrip() + "\n", encoding="utf-8")


RISK_MULT = {"low": 1.0, "medium": 2.0, "high": 5.0}          # manuscript Section 22.3.4
TESTS = [  # (name, info_value, cost_hours, risk) [ILLUSTRATIVE] estimates, exercises-key.md T1
    ("correlate long steps with local_ack_timeout_err and FEC uncorrectable (existing telemetry)", 0.8, 0.5, "low"),
    ("module DOM diagnostics on both ends (ethtool -m, switch transceiver)", 0.6, 0.5, "low"),
    ("ib_write_bw on drained orion-n15 and a peer, rail 3", 0.7, 3.0, "medium"),
]
IB_TIMEOUT_UNIT_US = 4.096                                     # InfiniBand local ACK timeout unit
NCCL_IB_TIMEOUT = {"2.23+": 20, "<=2.22": 18}                  # docs/VERIFIED_FACTS.md
FEC_CORR_BAD, FEC_CORR_OTHERS = 1.9e9, (1e6, 4e6)              # per 10 min (prompt)
STALL_S = (6.0, 9.0)                                           # observed long-step excess (prompt)
KEY_SCORES = [1.6, 1.2, 0.117]
KEY_TIMEOUT_S = {"2.23+": 4.3, "<=2.22": 1.07}


def main(out: Path) -> None:
    scored = sorted(({"test": n, "info": i, "cost_h": c, "risk": k, "score": i / (c * RISK_MULT[k])}
                     for n, i, c, k in TESTS), key=lambda t: -t["score"])
    for t, want in zip(scored, KEY_SCORES):
        assert abs(t["score"] - want) <= 0.001, (t, want)
    tmo = {v: IB_TIMEOUT_UNIT_US * 2 ** e / 1e6 for v, e in NCCL_IB_TIMEOUT.items()}
    for v, want in KEY_TIMEOUT_S.items():
        assert abs(tmo[v] - want) <= 0.01, (v, tmo[v])
    # one or two timeouts on the critical path must bracket the observed 6-9 s with the 2.23+ default
    lo, hi = tmo["2.23+"], 2 * tmo["2.23+"]
    assert lo <= STALL_S[1] and hi >= STALL_S[0]
    ratio = (FEC_CORR_BAD / FEC_CORR_OTHERS[1], FEC_CORR_BAD / FEC_CORR_OTHERS[0])
    assert ratio[0] > 400                                       # key: "about 500x other ports" (lower bound)
    result = {"id": "T1", "evidence_label": "ILLUSTRATIVE", "units": "score (dimensionless); s; ratio",
              "inputs": {"tests": TESTS, "risk_mult": RISK_MULT, "nccl_ib_timeout": NCCL_IB_TIMEOUT,
                         "fec_corrected_bad": FEC_CORR_BAD, "fec_corrected_others": FEC_CORR_OTHERS},
              "steps": {"ranked": [{**t, "score": r(t["score"], 3)} for t in scored],
                        "fec_ratio_range": [r(ratio[0], 0), r(ratio[1], 0)]},
              "answer": {"timeout_s": {k: r(v, 3) for k, v in tmo.items()},
                         "one_to_two_timeouts_s": [r(lo, 2), r(hi, 2)], "scores": [r(t["score"], 3) for t in scored]}}
    md = ["# T1 — scores and timeout arithmetic `[ILLUSTRATIVE]`", "", "| Rank | Test | Score |", "|---|---|---|"]
    md += [f"| {i} | {t['test']} | {t['score']:.3f} |" for i, t in enumerate(scored, 1)]
    md += ["", f"ACK timeout per retry: {tmo['2.23+']:.2f} s (NCCL 2.23+, value 20), {tmo['<=2.22']:.2f} s (≤ 2.22, value 18).",
           f"One or two timeouts on the critical path: {lo:.1f}–{hi:.1f} s, bracketing the observed 6–9 s stalls.",
           f"FEC corrected codewords on Ethernet28 are {ratio[0]:,.0f}–{ratio[1]:,.0f}× the other ports."]
    write(out, result, "\n".join(md))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    main(ap.parse_args().out)
