"""Exercise 5.9: deterministic Section 5.9 all-reduce model with one bad path.

Usage: python solve.py --out DIR
Formula (Section 5.9): t_r = 2(n-1)/n x (S/R) / min_i b_i;  t = max_r t_r + alpha;  busbw = 2(n-1)/n x S / t.
Inputs (prompt): S = 1 GiB, n = 256, R = 8, alpha = 0.2 ms, no variance; PIX 48 GB/s (Table 5.4),
Gen5 x8 NIC 27 GB/s achievable, host-staged cap 18 GB/s (Table 5.4).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

S = 2**30
N = 256
R = 8
ALPHA_S = 0.2e-3
CASES = {  # slowest-ring bandwidth in GB/s; which rings are affected
    "a_all_pix": (48.0, 0),
    "b_one_gen5_x8_nic": (27.0, 1),
    "c_one_node_no_gdr": (18.0, 8),
}
KEY = {"a_all_pix": 370.7, "b_one_gen5_x8_nic": 211.7, "c_one_node_no_gdr": 142.1}   # exercises-key.md 5.9
TOL = 0.1  # GB/s


def model(slowest_GBps: float) -> tuple[float, float]:
    factor = 2 * (N - 1) / N
    t = factor * (S / R) / (slowest_GBps * 1e9) + ALPHA_S
    return t, factor * S / t / 1e9


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    factor = 2 * (N - 1) / N
    ans = {}
    for k, (bw, rings) in CASES.items():
        t, busbw = model(bw)
        assert abs(busbw - KEY[k]) < TOL, (k, busbw)
        ans[k] = {"slowest_path_GBps": bw, "rings_affected": rings, "t_ms": round(t * 1e3, 3), "busbw_GBps": round(busbw, 1)}
    loss = 1 - ans["c_one_node_no_gdr"]["busbw_GBps"] / ans["a_all_pix"]["busbw_GBps"]
    assert abs(loss - 0.62) < 0.01
    res = {"exercise": "5.9", "evidence_label": "MODELED",
           "inputs": {"S_bytes": S, "n": N, "R": R, "alpha_ms": ALPHA_S * 1e3},
           "steps": {"ring_factor": round(factor, 5), "bytes_per_ring": S // R,
                     "ring_bytes_moved": round(factor * S / R)},
           "answer": {**ans, "d_busbw_loss_fraction": round(loss, 3), "d_nodes_affected_fraction": round(1 / 32, 4)},
           "units": {"time": "ms", "busbw": "GB/s"}}
    (out / "result.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = ["# Exercise 5.9 — one bad path `[MODELED]`", "",
          f"Ring factor 2 × 255 / 256 = {factor:.5f}; bytes per ring = {S // R:,} B; moved per ring = {factor * S / R:,.0f} B.", "",
          "| Case | Slowest path | t | busbw |", "|---|---|---|---|"]
    for k, v in ans.items():
        md.append(f"| {k} | {v['slowest_path_GBps']:.0f} GB/s | {v['t_ms']:.3f} ms | {v['busbw_GBps']:.1f} GB/s |")
    md += ["", f"(d) One node of 32 (3.1 %) without GDR costs {loss * 100:.0f} % of busbw: every ring visits every node."]
    (out / "result.md").write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
