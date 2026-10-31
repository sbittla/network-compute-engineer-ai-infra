"""O3 -- Compare L-tp8-bf16 and T-tp4-fp8; recommend per objective; find flip conditions. [MODELED]

Usage: python solve.py --out DIR
Inputs: lab/data/configs.yaml. Model: lab Part A compare_serving_configs (saturated batch =
min(max_batch, max_seqs at capacity_seq_tokens); TPOT at context prompt + output/2).
"""
import argparse
import json
import math
from pathlib import Path

import yaml

DATA = Path(__file__).resolve().parents[4] / "lab" / "data"


def evaluate(cfg: dict) -> dict:
    m, g, w = cfg["model"], cfg["gpu"], cfg["workload"]
    kvpt = 2 * m["n_layers"] * m["n_kv_heads"] * m["head_dim"] * m["kv_bytes_per_elem"]
    ctx = w["prompt_tokens"] + w["output_tokens"] / 2
    rows = {}
    for sc in cfg["serving_configs"]:
        budget = sc["tp"] * float(g["hbm_bytes"]) * sc["mem_fraction"] - float(sc["weight_bytes"]) \
            - sc["tp"] * float(sc["reserve_bytes_per_gpu"])
        pool = int(budget // (sc["block_tokens"] * kvpt))
        mx = pool // math.ceil(w["capacity_seq_tokens"] / sc["block_tokens"])
        b = min(sc["max_batch"], mx)
        tpot = sc["step_overhead_s"] + (float(sc["weight_bytes"]) + b * ctx * kvpt) / \
            (sc["tp"] * float(g["hbm_bw"]) * sc["hbm_efficiency"])
        peak = float(g["fp8_peak_flops"] if sc["weight_dtype"] == "fp8" else g["bf16_peak_flops"])
        rows[sc["name"]] = {"max_seqs": mx, "batch": b, "pool_blocks": pool, "tpot_ms": round(tpot * 1e3, 2),
                            "tok_s_node": round(b / tpot * sc["replicas_per_node"]),
                            "prefill_ms": round(2 * float(m["n_params"]) * w["prompt_tokens"] /
                                                (sc["tp"] * peak * sc["prefill_mfu"]) * 1e3, 1),
                            "meets_tpot_slo": tpot <= w["tpot_slo_s"], "max_batch": sc["max_batch"],
                            "block_tokens": sc["block_tokens"]}
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    cfg = yaml.safe_load((DATA / "configs.yaml").read_text(encoding="utf-8"))
    rows = evaluate(cfg)
    ok = {k: v for k, v in rows.items() if v["meets_tpot_slo"]}
    latency = min(ok, key=lambda k: ok[k]["tpot_ms"])
    throughput = max(ok, key=lambda k: ok[k]["tok_s_node"])
    L, T = rows["L-tp8-bf16"], rows["T-tp4-fp8"]
    # Key O3: TPOT 11.7 vs 20.2 ms; 2,740 vs 12,678 tokens/s/node (4.6×).
    assert latency == "L-tp8-bf16" and throughput == "T-tp4-fp8"
    assert abs(L["tpot_ms"] - 11.7) < 0.05 and abs(T["tpot_ms"] - 20.2) < 0.05
    assert abs(L["tok_s_node"] - 2740) < 1 and abs(T["tok_s_node"] - 12678) < 1
    assert abs(T["tok_s_node"] / L["tok_s_node"] - 4.6) < 0.05
    # Flip (i): the TPOT SLO below which T fails at its saturated batch.
    slo_flip_ms = T["tpot_ms"]
    # Flip (ii): smallest capacity sequence length at which T's batch is KV-capped below max_batch.
    blocks_needed = T["pool_blocks"] // T["max_batch"] + 1
    seq_flip = (blocks_needed - 1) * T["block_tokens"] + 1
    assert T["pool_blocks"] // math.ceil(seq_flip / 16) < T["max_batch"] <= T["pool_blocks"] // math.ceil((seq_flip - 1) / 16)
    assert seq_flip == 4993, seq_flip   # 4,992 tokens = 312 blocks still allows 128
    seqs_16k = T["pool_blocks"] // (16384 // 16)
    assert seqs_16k == 39

    result = {"inputs": {"yaml": "lab/data/configs.yaml"},
              "steps": {"table": rows},
              "answer": {"latency": latency, "throughput": throughput,
                         "throughput_ratio": round(T["tok_s_node"] / L["tok_s_node"], 2),
                         "flip_tpot_slo_ms": slo_flip_ms, "flip_seq_tokens": seq_flip, "t_max_seqs_16k": seqs_16k,
                         "flip_quality": "FP8 weights unacceptable excludes T"},
              "units": {"tpot": "ms", "throughput": "tokens/s per node"}, "evidence_label": "[MODELED]"}
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# O3 comparison `[MODELED]`", "", "| Config | Max seqs | Batch | TPOT | tokens/s/node | Prefill |", "|---|---|---|---|---|---|"]
    for k, v in rows.items():
        lines.append(f"| {k} | {v['max_seqs']} | {v['batch']} | {v['tpot_ms']} ms | {v['tok_s_node']:,} | {v['prefill_ms']} ms |")
    lines += ["", f"Latency: {latency}; throughput: {throughput} ({T['tok_s_node']/L['tok_s_node']:.1f}×)",
              f"Flips: TPOT SLO < {slo_flip_ms} ms; sequences > {seq_flip - 1} tokens cap T below batch 128 "
              f"({seqs_16k} at 16k); FP8 quality.", ""]
    (out / "result.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
