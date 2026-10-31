"""D1 — hot spares (fixed world size) vs elastic training (drop DP replicas), per fleet node (Section 19.7).

    python solve.py --out DIR

Model (stated assumptions):
  * job MTBF M = 1,536 / 512 h = 180 min; τ = 19 min; δ = 1 min (Section 19.1); Young's goodput.
  * failures 8/day, MTTR 5 days -> nodes in repair ~ Poisson(40) (canonical, REFERENCE_CLUSTER.md).
  * A: p99 pool outside the partition (k = 55), restart R = 15 min; capacity factor = 512 / (512 + k).
  * B: no spares, re-shard R = 5 min; one DP replica = 8 nodes (TP = 8, PP = 8, DP = 64).
    - re-packed: floor((512 − 40) / 8) replicas survive.
    - not re-packed, expected: failed nodes placed at random -> E[replicas hit] = 64 (1 − C(504,40)/C(512,40)).
    - not re-packed, worst: 40 failures in 40 distinct replicas.
  Useful throughput per fleet node = goodput × fraction of fleet doing training.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

NODES, NODE_MTBF_H, MTTR_D = 512, 1536.0, 5
TAU, DELTA, R_A, R_B = 19.0, 1.0, 15.0, 5.0
REPLICA_NODES, DP = 8, 64
P99 = 0.99

# solutions/exercises-key.md, D1 table
KEY = {"A": 0.733, "B_repacked": 0.799, "B_expected": 0.450, "B_worst": 0.325, "pool": 55,
       "replicas_repacked": 59, "replicas_lost_expected": 30.8}
TOL = 0.0015


def goodput(r: float, m: float) -> float:
    return 1 - (DELTA / TAU + (TAU / 2 + r) / m)


def poisson_quantile(mean: float, p: float) -> int:
    term, total, k = math.exp(-mean), math.exp(-mean), 0
    while total < p:
        k += 1
        term *= mean / k
        total += term
    return k


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    m = NODE_MTBF_H / NODES * 60
    in_repair = NODES * 24 / NODE_MTBF_H * MTTR_D          # 40
    pool = poisson_quantile(in_repair, P99)
    g_a, g_b = goodput(R_A, m), goodput(R_B, m)
    cap_a = NODES / (NODES + pool)
    n_rep = int(in_repair)
    repacked = (NODES - n_rep) // REPLICA_NODES
    lost_exp = DP * (1 - math.comb(NODES - REPLICA_NODES, n_rep) / math.comb(NODES, n_rep))
    rows = {
        "A_hot_spares": {"goodput": g_a, "capacity_factor": cap_a},
        "B_repacked": {"goodput": g_b, "capacity_factor": repacked / DP},
        "B_not_repacked_expected": {"goodput": g_b, "capacity_factor": (DP - lost_exp) / DP},
        "B_not_repacked_worst": {"goodput": g_b, "capacity_factor": (DP - n_rep) / DP},
    }
    for v in rows.values():
        v["useful_per_fleet_node"] = v["goodput"] * v["capacity_factor"]

    assert pool == KEY["pool"] and repacked == KEY["replicas_repacked"]
    assert abs(lost_exp - KEY["replicas_lost_expected"]) < 0.05, lost_exp
    for name, key in (("A_hot_spares", "A"), ("B_repacked", "B_repacked"),
                      ("B_not_repacked_expected", "B_expected"), ("B_not_repacked_worst", "B_worst")):
        assert abs(rows[name]["useful_per_fleet_node"] - KEY[key]) < TOL, (name, rows[name])
    # divisibility: 59 is prime, so no global batch sized for 64 replicas splits evenly
    assert all(repacked % d for d in range(2, repacked))
    divisors_of_64_at_or_below = [d for d in (56, 48, 32) if d <= repacked]

    result = {
        "exercise": "D1",
        "inputs": {"nodes": NODES, "node_mtbf_h": NODE_MTBF_H, "mttr_days": MTTR_D, "tau_min": TAU,
                   "delta_min": DELTA, "r_a_min": R_A, "r_b_min": R_B, "replica_nodes": REPLICA_NODES, "dp": DP},
        "steps": {"job_mtbf_min": round(m, 2), "mean_nodes_in_repair": in_repair, "p99_pool": pool,
                  "replicas_repacked": repacked, "replicas_lost_expected_not_repacked": round(lost_exp, 2),
                  "dp_59_is_prime": True, "fallback_dp_options": divisors_of_64_at_or_below},
        "answer": {k: {kk: round(vv, 3) for kk, vv in v.items()} for k, v in rows.items()},
        "units": "useful (goodput-weighted) training throughput per fleet node, fraction of one node",
        "evidence_label": "[MODELED] from [ILLUSTRATIVE] reliability inputs",
        "tolerance": TOL,
    }
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                                     encoding="utf-8")
    md = ["# D1 — Hot spares vs elastic training `[MODELED]`", "",
          f"M = {m:.0f} min; mean in repair = {in_repair:g}; p99 pool = {pool}; "
          f"re-packed replicas = ⌊{NODES - n_rep}/8⌋ = {repacked}; expected replicas lost unpacked = {lost_exp:.1f}", "",
          "| Option | Goodput | Capacity factor | Useful per fleet node |", "|---|---|---|---|"]
    md += [f"| {k} | {v['goodput']:.3f} | {v['capacity_factor']:.3f} | {v['useful_per_fleet_node']:.3f} |"
           for k, v in rows.items()]
    (out / "result.md").write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
