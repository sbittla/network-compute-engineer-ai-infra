"""K1 — job MTBF and interruptions per day versus job size (Chapter 19, Section 19.1).

    python solve.py --out DIR

Inputs are the Reference Cluster canon (docs/REFERENCE_CLUSTER.md, "Reliability assumptions"):
node MTBF ≈ 1,536 node-hours `[ILLUSTRATIVE]`. A synchronous job fails when any node fails, so
failure rates add: MTBF_job = MTBF_node / N. Results are `[MODELED]`.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

NODE_MTBF_H = 1536.0          # REFERENCE_CLUSTER.md, reliability assumptions
JOB_SIZES = (8, 32, 128, 512)  # prompt
HOURS_PER_DAY = 24.0

# solutions/exercises-key.md, K1 table: nodes -> (job MTBF h, interruptions/day)
KEY = {8: (192.0, 0.125), 32: (48.0, 0.5), 128: (12.0, 2.0), 512: (3.0, 8.0)}
TOL = 1e-9


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    rows = []
    for n in JOB_SIZES:
        mtbf = NODE_MTBF_H / n
        per_day = HOURS_PER_DAY / mtbf
        rows.append({"nodes": n, "gpus": 8 * n, "job_mtbf_h": round(mtbf, 4),
                     "interruptions_per_day": round(per_day, 4)})
        k_mtbf, k_day = KEY[n]
        assert abs(mtbf - k_mtbf) < TOL, (n, mtbf)
        assert abs(per_day - k_day) < TOL, (n, per_day)

    result = {
        "exercise": "K1",
        "inputs": {"node_mtbf_h": NODE_MTBF_H, "job_sizes_nodes": list(JOB_SIZES)},
        "formula": "MTBF_job = MTBF_node / N ; interruptions/day = 24 h / MTBF_job",
        "answer": rows,
        "units": {"job_mtbf_h": "hours", "interruptions_per_day": "1/day"},
        "evidence_label": "[MODELED] from [ILLUSTRATIVE] inputs",
        "tolerance": TOL,
    }
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md = ["# K1 — Scale and MTBF `[MODELED]`", "",
          f"MTBF_job = {NODE_MTBF_H:,.0f} node-h / N; interruptions/day = 24 / MTBF_job", "",
          "| Nodes | GPUs | Job MTBF (h) | Interruptions/day |", "|---|---|---|---|"]
    md += [f"| {r['nodes']} | {r['gpus']:,} | {r['job_mtbf_h']:g} | {r['interruptions_per_day']:g} |" for r in rows]
    (out / "result.md").write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
