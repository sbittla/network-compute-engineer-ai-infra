"""W1 -- Long-context tier: TP = 8, FP8 weights (70 GB), FP8 vs BF16 KV. [MODELED]

Usage: python solve.py --out DIR
Inputs: prompt (TP 8, 70 GB weights, mem_fraction 0.90, 2 GB reserve, 16-token blocks, 8,192-token
sequences; B = 64 at 6,000 tokens, efficiency 0.70, overhead 3 ms) and lab/data/configs.yaml (model, GPU).
"""
import argparse
import json
import math
from pathlib import Path

import yaml

DATA = Path(__file__).resolve().parents[4] / "lab" / "data"
TP, W, MEM_FRAC, RESERVE, BLOCK = 8, 70e9, 0.90, 2e9, 16
SEQ = 8192
B, CTX, EFF, OVH = 64, 6000, 0.70, 0.003


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    cfg = yaml.safe_load((DATA / "configs.yaml").read_text(encoding="utf-8"))
    m, g = cfg["model"], cfg["gpu"]
    kv_bf16 = 2 * m["n_layers"] * m["n_kv_heads"] * m["head_dim"] * 2
    kv_fp8 = kv_bf16 // 2
    budget = TP * float(g["hbm_bytes"]) * MEM_FRAC - W - TP * RESERVE
    per_seq = math.ceil(SEQ / BLOCK)
    res = {}
    for name, kv in (("fp8", kv_fp8), ("bf16", kv_bf16)):
        blocks = int(budget // (BLOCK * kv))
        res[name] = {"blocks": blocks, "max_seqs": blocks // per_seq}
    bw = TP * float(g["hbm_bw"])
    step_bytes = W + B * CTX * kv_fp8
    lb = step_bytes / bw
    plan = OVH + step_bytes / (bw * EFF)
    # Key W1: 490 GB; FP8 186,920 blocks -> 365; BF16 93,460 -> 182; 132.915e9 B; 4.96 ms / 12,905 tokens/s;
    # 10.08 ms / 6,346 tokens/s. Tolerances: exact integers, 0.01 ms, 2 tokens/s.
    assert abs(budget - 490e9) < 1 and res["fp8"] == {"blocks": 186920, "max_seqs": 365}
    assert res["bf16"] == {"blocks": 93460, "max_seqs": 182}
    assert abs(step_bytes - 132.915e9) < 1e6
    assert abs(lb * 1e3 - 4.96) < 0.01 and abs(B / lb - 12905) < 30
    assert abs(plan * 1e3 - 10.08) < 0.01 and abs(B / plan - 6346) < 2

    result = {"inputs": {"tp": TP, "weight_bytes": W, "mem_fraction": MEM_FRAC, "reserve_per_gpu": RESERVE,
                         "block_tokens": BLOCK, "seq_tokens": SEQ, "batch": B, "ctx": CTX, "eff": EFF, "overhead_s": OVH},
              "steps": {"kv_bytes_fp8": kv_fp8, "kv_bytes_bf16": kv_bf16, "blocks_per_seq": per_seq,
                        "step_bytes": step_bytes},
              "answer": {"kv_budget_GB": round(budget / 1e9, 1), "fp8": res["fp8"], "bf16": res["bf16"],
                         "lower_bound_ms": round(lb * 1e3, 2), "lower_bound_tok_s": round(B / lb),
                         "planning_ms": round(plan * 1e3, 2), "planning_tok_s": round(B / plan)},
              "units": {"budget": "GB (1e9 B)", "time": "ms", "throughput": "tokens/s"}, "evidence_label": "[MODELED]"}
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = (f"# W1 result `[MODELED]`\n\n- Budget = 576e9 - 70e9 - 16e9 = {budget/1e9:.0f} GB\n"
          f"- (a) FP8 KV: {res['fp8']['blocks']:,} blocks -> {res['fp8']['max_seqs']} × 8,192-token sequences\n"
          f"- (b) BF16 KV: {res['bf16']['blocks']:,} blocks -> {res['bf16']['max_seqs']}\n"
          f"- (c) bytes/step {step_bytes/1e9:.3f} GB; lower bound {lb*1e3:.2f} ms ({B/lb:,.0f} tokens/s); "
          f"planning {plan*1e3:.2f} ms ({B/plan:,.0f} tokens/s)\n")
    (out / "result.md").write_text(md, encoding="utf-8")


if __name__ == "__main__":
    main()
