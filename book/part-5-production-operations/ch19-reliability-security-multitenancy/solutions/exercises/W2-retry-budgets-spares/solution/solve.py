"""W2 — RC retry budget after the NCCL_IB_TIMEOUT default change, and Poisson spare sizing (Section 19.4, 19.7).

    python solve.py --out DIR

Per-attempt local ACK timeout = 4.096 µs × 2^timeout; budget ≈ (retry_cnt + 1) × per-attempt
(docs/VERIFIED_FACTS.md: default 18 up to NCCL 2.22, 20 from 2.23). Spare pool: nodes in repair ~
Poisson(failures/day × MTTR); smallest k with P(X ≤ k) ≥ 0.99 (Chapter 16 method).
Flap durations are read from the prompt (they match the lab's events.jsonl link-down/up pairs).
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

ACK_UNIT_S = 4.096e-6
TIMEOUT_OLD, TIMEOUT_NEW = 18, 20      # NCCL ≤ 2.22 / ≥ 2.23
RETRY_CNT = 7
FLAPS_S = (14, 6, 5, 14)               # prompt (lab incident flaps, in order)
JOB_GPUS = 4096                         # prompt (b)
WATCHDOG_S = 600                        # PyTorch NCCL default process-group timeout
NODE_MTBF_H = 1536.0                    # REFERENCE_CLUSTER.md
PARTITION_NODES = 512
MTTR_DAYS = (3, 5)                      # prompt (c); 5 is canonical
TARGET = 0.99

# solutions/exercises-key.md, W2
KEY = {"per_attempt_s": 4.295, "budget_s": 34.4, "old_budget_s": 8.6, "extra_delay_s": 25.8,
       "extra_gpu_h": 29.3, "watchdog_gpu_h": 683.0, "failures_per_day": 8.0,
       "pool": {3: (24.0, 36, 0.070), 5: (40.0, 55, 0.107)}}
REL_TOL = 0.005


def poisson_cdf(k: int, mean: float) -> float:
    term, total = math.exp(-mean), 0.0
    for i in range(k + 1):
        if i:
            term *= mean / i
        total += term
    return total


def quantile(mean: float, p: float) -> int:
    k = 0
    while poisson_cdf(k, mean) < p:
        k += 1
    return k


def close(a: float, b: float, tol: float = REL_TOL) -> bool:
    return abs(a - b) <= tol * abs(b)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    per_new = ACK_UNIT_S * 2 ** TIMEOUT_NEW
    budget_new = (RETRY_CNT + 1) * per_new
    budget_old = (RETRY_CNT + 1) * ACK_UNIT_S * 2 ** TIMEOUT_OLD
    survived_new = [f < budget_new for f in FLAPS_S]
    survived_old = [f < budget_old for f in FLAPS_S]
    extra = budget_new - budget_old
    extra_gpu_h = extra * JOB_GPUS / 3600
    watchdog_gpu_h = WATCHDOG_S * JOB_GPUS / 3600

    per_day = PARTITION_NODES * 24 / NODE_MTBF_H
    pools = {}
    for d in MTTR_DAYS:
        mean = per_day * d
        k = quantile(mean, TARGET)
        pools[d] = {"mean_in_repair": round(mean, 2), "k_p99": k, "p_le_k": round(poisson_cdf(k, mean), 4),
                    "p_le_mean": round(poisson_cdf(int(mean), mean), 3),
                    "fraction_of_partition": round(k / PARTITION_NODES, 4)}

    assert close(per_new, KEY["per_attempt_s"]) and close(budget_new, KEY["budget_s"], 0.01)
    assert close(budget_old, KEY["old_budget_s"], 0.01)
    assert all(survived_new) and survived_old == [False, True, True, False]
    assert close(extra, KEY["extra_delay_s"], 0.01) and close(extra_gpu_h, KEY["extra_gpu_h"], 0.01)
    assert close(watchdog_gpu_h, KEY["watchdog_gpu_h"], 0.01)
    assert per_day == KEY["failures_per_day"]
    for d, (mean, k, frac) in KEY["pool"].items():
        assert pools[d]["mean_in_repair"] == mean and pools[d]["k_p99"] == k, (d, pools[d])
        assert abs(pools[d]["fraction_of_partition"] - frac) < 0.0006, (d, pools[d])

    result = {
        "exercise": "W2",
        "inputs": {"ack_unit_s": ACK_UNIT_S, "nccl_ib_timeout": [TIMEOUT_OLD, TIMEOUT_NEW], "retry_cnt": RETRY_CNT,
                   "flaps_s": list(FLAPS_S), "job_gpus": JOB_GPUS, "watchdog_s": WATCHDOG_S,
                   "node_mtbf_h": NODE_MTBF_H, "partition_nodes": PARTITION_NODES, "mttr_days": list(MTTR_DAYS),
                   "target_quantile": TARGET},
        "steps": {"a_per_attempt_s": round(per_new, 3), "a_budget_s": round(budget_new, 2),
                  "old_budget_s": round(budget_old, 2), "a_survived_timeout20": survived_new,
                  "survived_timeout18": survived_old, "b_extra_detection_delay_s": round(extra, 2),
                  "b_extra_gpu_h_per_dead_peer": round(extra_gpu_h, 1),
                  "b_watchdog_gpu_h_for_comparison": round(watchdog_gpu_h, 1),
                  "c_failures_per_day": per_day},
        "answer": {"a_budget_s": round(budget_new, 1), "a_all_flaps_survived": all(survived_new),
                   "b_extra_gpu_h": round(extra_gpu_h, 1),
                   "c_pools": {f"mttr_{d}d": v for d, v in pools.items()}},
        "units": {"time": "s", "cost": "GPU-h", "pool": "nodes"},
        "evidence_label": "[MODELED] from [VENDOR-SPEC] defaults and [ILLUSTRATIVE] reliability inputs",
        "tolerance": f"relative {REL_TOL}–0.01; Poisson quantiles exact",
    }
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                                     encoding="utf-8")
    md = ["# W2 — Retry budgets and spares `[MODELED]`", "",
          f"(a) 4.096 µs × 2^20 = {per_new:.3f} s; budget = 8 × {per_new:.3f} = {budget_new:.1f} s "
          f"(was {budget_old:.1f} s at timeout 18). Flaps {list(FLAPS_S)} s survived: {survived_new}",
          f"(b) dead peer reported {extra:.1f} s later: {extra:.1f} s × {JOB_GPUS:,} GPUs = {extra_gpu_h:.1f} GPU-h "
          f"per event (watchdog: {watchdog_gpu_h:.0f} GPU-h)",
          f"(c) failures/day = 512 × 24 / 1,536 = {per_day:g}", "",
          "| MTTR | Mean in repair | p99 pool k | P(X ≤ k) | % of 512 |", "|---|---|---|---|---|"]
    md += [f"| {d} d | {v['mean_in_repair']:g} | {v['k_p99']} | {v['p_le_k']:.3f} | "
           f"{v['fraction_of_partition'] * 100:.1f} % |" for d, v in pools.items()]
    (out / "result.md").write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
