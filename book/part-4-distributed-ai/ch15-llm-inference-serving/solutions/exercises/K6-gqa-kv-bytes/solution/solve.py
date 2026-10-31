"""K6 -- KV bytes per token with and without GQA, and the effect on concurrency. [MODELED]

Usage: python solve.py --out DIR
Inputs: lab/data/configs.yaml (W-INFER, T-tp4-fp8); 64 query heads (prompt); 4,096-token sequences.
"""
import argparse
import json
import math
from pathlib import Path

import yaml

DATA = Path(__file__).resolve().parents[4] / "lab" / "data"
Q_HEADS = 64
SEQ = 4096


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    cfg = yaml.safe_load((DATA / "configs.yaml").read_text(encoding="utf-8"))
    m, g = cfg["model"], cfg["gpu"]
    sc = next(s for s in cfg["serving_configs"] if s["name"] == "T-tp4-fp8")
    kv_gqa = 2 * m["n_layers"] * m["n_kv_heads"] * m["head_dim"] * m["kv_bytes_per_elem"]
    kv_mha = 2 * m["n_layers"] * Q_HEADS * m["head_dim"] * m["kv_bytes_per_elem"]
    budget = sc["tp"] * float(g["hbm_bytes"]) * sc["mem_fraction"] - float(sc["weight_bytes"]) \
        - sc["tp"] * float(sc["reserve_bytes_per_gpu"])
    per_seq = math.ceil(SEQ / sc["block_tokens"])
    seqs = {}
    for name, kv in (("gqa", kv_gqa), ("no_gqa", kv_mha)):
        blocks = int(budget // (sc["block_tokens"] * kv))
        seqs[name] = {"blocks": blocks, "max_seqs": blocks // per_seq}
    # Key K6: 327,680 vs 2,621,440 B (8×); 156 -> 19 sequences of 4k per TP=4 FP8 replica.
    assert kv_gqa == 327_680 and kv_mha == 2_621_440 and kv_mha // kv_gqa == 8
    assert seqs["gqa"]["max_seqs"] == 156 and seqs["no_gqa"]["max_seqs"] == 19

    result = {"inputs": {"layers": m["n_layers"], "kv_heads": m["n_kv_heads"], "q_heads": Q_HEADS,
                         "head_dim": m["head_dim"], "bytes_per_elem": m["kv_bytes_per_elem"], "seq_tokens": SEQ},
              "steps": {"formula": "2 × layers × kv_heads × head_dim × bytes", "kv_budget_B": budget,
                        "blocks_per_seq": per_seq},
              "answer": {"kv_bytes_per_token_gqa": kv_gqa, "kv_bytes_per_token_no_gqa": kv_mha,
                         "ratio": kv_mha // kv_gqa, "concurrency": seqs},
              "units": {"kv": "B/token", "budget": "B"}, "evidence_label": "[MODELED]"}
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = (f"# K6 result `[MODELED]`\n\n- With GQA: 2 × 80 × 8 × 128 × 2 = {kv_gqa:,} B/token\n"
          f"- Without GQA: 2 × 80 × 64 × 128 × 2 = {kv_mha:,} B/token (8×)\n"
          f"- T-tp4-fp8 (210 GB KV): {seqs['gqa']['max_seqs']} vs {seqs['no_gqa']['max_seqs']} sequences of 4,096 tokens\n")
    (out / "result.md").write_text(md, encoding="utf-8")


if __name__ == "__main__":
    main()
