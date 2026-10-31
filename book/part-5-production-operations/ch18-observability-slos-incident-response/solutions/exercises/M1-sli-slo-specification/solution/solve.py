"""M1 — Error budgets and canon-derived targets for ORION's SLO spec (Chapter 18).

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


WINDOW_MIN = 30 * 24 * 60
NODE_MTBF_H, JOB_NODES_16, ATTEMPT_H = 1536.0, 16, 24.0
MEAN_IN_REPAIR = 2.5             # Section 16.9: lambda 0.5/day x 5-day repair
CLUSTER_SLO, AVAIL_SLO, THROUGHPUT_SLO, LATENCY_SLO = 0.995, 0.999, 0.99, 0.95
RPM = 3000
PROBES = 8 * 720                  # one probe per rail per hour
LINK_WINDOWS = 256 * (WINDOW_MIN // 5)


def poisson_cdf(k: int, lam: float) -> float:
    return sum(math.exp(-lam) * lam ** i / math.factorial(i) for i in range(k + 1))


def main(out: Path) -> None:
    budgets = {"cluster_availability_min": (1 - CLUSTER_SLO) * WINDOW_MIN,
               "inference_availability_min": (1 - AVAIL_SLO) * WINDOW_MIN,
               "training_throughput_min_per_job": (1 - THROUGHPUT_SLO) * WINDOW_MIN,
               "inference_latency_slow_requests": (1 - LATENCY_SLO) * RPM * WINDOW_MIN,
               "fabric_failed_probes": 0.01 * PROBES,
               "fabric_bad_link_windows": 0.001 * LINK_WINDOWS}
    interruptions = WINDOW_MIN / 60 / (NODE_MTBF_H / 32)
    budgets["recovery_slow_per_month_256gpu_job"] = 0.05 * interruptions
    p16 = math.exp(-ATTEMPT_H / (NODE_MTBF_H / JOB_NODES_16))
    p32 = math.exp(-ATTEMPT_H / (NODE_MTBF_H / 32))
    p_le = {k: poisson_cdf(k, MEAN_IN_REPAIR) for k in (1, 7, 8)}
    repair_share = {k: (1 - p_le[k]) / (1 - CLUSTER_SLO) for k in (7, 8)}
    close(budgets["cluster_availability_min"], 216, 1e-6, "cluster budget")
    close(budgets["inference_availability_min"], 43.2, 1e-6, "availability budget")
    close(budgets["training_throughput_min_per_job"], 432, 1e-6, "throughput budget")
    close(p16, 0.78, 0.005, "16-node 24 h survival")
    close(p32, 0.61, 0.005, "32-node 24 h survival")
    close(p_le[1], 0.29, 0.005, "P(<=1)")
    close(p_le[7], 0.996, 0.0005, "P(<=7)")
    close(p_le[8], 0.9989, 0.00005, "P(<=8)")
    close(repair_share[7], 0.85, 0.015, "repair share of budget at 7 down")
    result = {"exercise": "M1", "evidence_label": "[MODELED]",
              "inputs": {"window_min": WINDOW_MIN, "node_mtbf_h": NODE_MTBF_H, "mean_in_repair": MEAN_IN_REPAIR,
                         "requests_per_min": RPM, "probes": PROBES, "link_windows": LINK_WINDOWS},
              "answer": {"budgets": {k: round(v, 2) for k, v in budgets.items()},
                         "p_uninterrupted_24h": {"16_nodes": round(p16, 4), "32_nodes": round(p32, 4)},
                         "p_nodes_in_repair_at_most": {str(k): round(v, 4) for k, v in p_le.items()},
                         "repair_share_of_cluster_budget": {str(k): round(v, 3) for k, v in repair_share.items()}},
              "units": {"budgets": "minutes / requests / probes / link-windows per 30 days"}}
    lines = "\n".join(f"- {k}: {v:,.2f}" for k, v in budgets.items())
    md = f"""
# M1 budgets and derived targets `[MODELED]`

{lines}
- P(no interruption in 24 h): 16 nodes {p16:.2f}, 32 nodes {p32:.2f}
- Poisson(2.5) nodes in repair: P(≤1) {p_le[1]:.3f}, P(≤7) {p_le[7]:.4f}, P(≤8) {p_le[8]:.4f}
- repair share of the 0.5 % budget: 7 down {repair_share[7] * 100:.0f} %, 8 down {repair_share[8] * 100:.0f} %
"""
    emit(out, result, md)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    main(Path(ap.parse_args().out))
