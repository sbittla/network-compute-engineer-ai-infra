#!/usr/bin/env python3
"""W2 — weak-scaling efficiency, straggler model and minimum detectable effect.

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


SEQ_PER_DP = 128                  # 256 sequences at DP = 2 (manuscript 22.10)
SEQ_LEN = 4096                    # tokens per sequence
STEP_S = {64: 17.38, 128: 17.62, 256: 17.90}          # prompt, medians [ILLUSTRATIVE]
DP = {64: 2, 128: 4, 256: 8}
NODES = {64: 8, 128: 16, 256: 32}
SIGMA_NODE_S = 0.5                                     # per-node jitter (prompt)
EMAX = {8: 1.42, 16: 1.77, 32: 2.07}                   # expected max of n normals, in sigma (prompt)
GRAD_GB = 70e9 / 32 * 2 / 1e9                          # BF16 gradients per GPU, 4.375 GB (Section 22.5.2)
NIC_GBPS = 45.0                                        # achieved GB/s per NIC [ILLUSTRATIVE]
HIDE_S = 0.07                                          # last micro-batch backward that can hide DP comm
SIGMA_RUN_S = 0.11                                     # run-to-run sigma of per-job means (prompt)
CLAIM_S = 0.15                                         # vendor claim at 256 GPUs
Z_SUM = 2.8                                            # z_0.975 + z_0.80 = 1.96 + 0.84
N_ARM = 5
KEY = {"E128_pct": 98.6, "E256_pct": 97.1, "strag16_s": 0.175, "strag32_s": 0.325, "mde5_s": 0.195,
       "n_req": 9}                                     # exercises-key.md W2


def main(out: Path) -> None:
    tok = {n: DP[n] * SEQ_PER_DP * SEQ_LEN for n in STEP_S}
    thr = {n: tok[n] / STEP_S[n] for n in STEP_S}
    eff = {n: thr[n] / ((n / 64) * thr[64]) for n in STEP_S}
    strag = {n: (EMAX[NODES[n]] - EMAX[8]) * SIGMA_NODE_S for n in (128, 256)}
    gap = {n: STEP_S[n] - STEP_S[64] for n in (128, 256)}
    ring = {n: 2 * (DP[n] - 1) / DP[n] * GRAD_GB for n in STEP_S}
    exposed = {n: max(0.0, ring[n] / NIC_GBPS - HIDE_S) for n in STEP_S}
    dp_extra = {n: exposed[n] - exposed[64] for n in (128, 256)}
    unexpl = {n: gap[n] - strag[n] - dp_extra[n] for n in (128, 256)}
    mde5 = Z_SUM * SIGMA_RUN_S * math.sqrt(2 / N_ARM)
    n_exact = 2 * (Z_SUM * SIGMA_RUN_S / CLAIM_S) ** 2
    n_req = math.ceil(n_exact)
    assert abs(100 * eff[128] - KEY["E128_pct"]) <= 0.05 and abs(100 * eff[256] - KEY["E256_pct"]) <= 0.05
    assert abs(strag[128] - KEY["strag16_s"]) < 1e-9 and abs(strag[256] - KEY["strag32_s"]) < 1e-9
    assert abs(mde5 - KEY["mde5_s"]) <= 0.001 and mde5 > CLAIM_S
    assert n_req == KEY["n_req"]
    assert abs(unexpl[256] - 0.12) <= 0.01, unexpl[256]           # Section 22.10.5: ~0.12 s unexplained
    result = {"id": "W2", "evidence_label": "MODELED", "units": "tokens/s; %; s",
              "inputs": {"step_s": STEP_S, "dp": DP, "sigma_node_s": SIGMA_NODE_S, "emax_sigma": EMAX,
                         "sigma_run_s": SIGMA_RUN_S, "claim_s": CLAIM_S, "n_per_arm": N_ARM},
              "steps": {"tokens_per_step": tok, "tokens_per_s": {n: r(v, 0) for n, v in thr.items()},
                        "tokens_per_s_per_gpu": {n: r(v / n, 1) for n, v in thr.items()},
                        "gap_s": {n: r(v, 3) for n, v in gap.items()},
                        "straggler_s": {n: r(v, 3) for n, v in strag.items()},
                        "ring_GB": {n: r(v, 3) for n, v in ring.items()},
                        "dp_exposed_s": {n: r(v, 3) for n, v in exposed.items()},
                        "unexplained_s": {n: r(v, 3) for n, v in unexpl.items()},
                        "n_exact": r(n_exact, 3)},
              "answer": {"E_weak_pct": {n: r(100 * v, 1) for n, v in eff.items()}, "mde_n5_s": r(mde5, 3),
                         "detectable_with_5": mde5 <= CLAIM_S, "runs_per_arm_required": n_req}}
    md = ["# W2 — scaling and detectability `[MODELED]`", "", "| GPUs | Tokens/s | E_weak |", "|---|---|---|"]
    md += [f"| {n} | {thr[n]:,.0f} | {100 * eff[n]:.1f} % |" for n in STEP_S]
    md += ["", f"Straggler share: {strag[128]:.3f} of {gap[128]:.2f} s (16 nodes); {strag[256]:.3f} of {gap[256]:.2f} s "
           f"(32 nodes). After DP exposure, unexplained {unexpl[128]:.3f} s and {unexpl[256]:.3f} s.", "",
           f"MDE(n = 5) = {mde5:.3f} s > {CLAIM_S} s → not detectable; n = {n_exact:.2f} → {n_req} runs per arm."]
    write(out, result, "\n".join(md))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    main(ap.parse_args().out)
