"""K1 -- Arithmetic intensity of decode (B = 32) and a 2,048-token prefill vs the BF16 ridge. [MODELED]

Usage: python solve.py --out DIR
Inputs: lab/data/configs.yaml (W-INFER model and H100-class GPU constants); the prompt (B = 32, 2,048 tokens).
"""
import argparse
import json
from pathlib import Path

import yaml

DATA = Path(__file__).resolve().parents[4] / "lab" / "data"
BATCH = 32
PROMPT = 2048
N_HEADS = 64          # W-INFER query heads (docs/REFERENCE_CLUSTER.md)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    cfg = yaml.safe_load((DATA / "configs.yaml").read_text(encoding="utf-8"))
    n = float(cfg["model"]["n_params"])
    g = cfg["gpu"]
    ridge = float(g["bf16_peak_flops"]) / float(g["hbm_bw"])
    weight_bytes = 2 * n                                  # BF16 weights streamed once per step
    decode = 2 * n * BATCH / weight_bytes                 # FLOP per weight byte
    group = N_HEADS // cfg["model"]["n_kv_heads"]         # query heads served by each KV head
    attn = group * 2 / cfg["model"]["kv_bytes_per_elem"]  # 2 FLOP per MAC per query head / bytes per element
    prefill = 2 * n * PROMPT / weight_bytes
    # Key K1: decode ≈ 32 FLOP/B, attention ≈ 8 FLOP/B, prefill ≈ 2,048 FLOP/B, ridge ≈ 295 FLOP/B.
    assert abs(decode - 32) < 1e-9 and abs(attn - 8) < 1e-9 and abs(prefill - 2048) < 1e-9
    assert abs(ridge - 295) < 1, ridge
    assert decode < ridge and attn < ridge and prefill > ridge

    result = {"inputs": {"n_params": n, "batch": BATCH, "prompt_tokens": PROMPT, "gqa_group": group,
                         "bf16_peak_flops": float(g["bf16_peak_flops"]), "hbm_bw": float(g["hbm_bw"])},
              "steps": {"ridge_flop_per_B": round(ridge, 1)},
              "answer": {"decode_flop_per_B": decode, "attention_flop_per_B": attn, "prefill_flop_per_B": prefill,
                         "ridge_flop_per_B": round(ridge, 1), "decode_bound": "HBM bandwidth",
                         "prefill_bound": "compute"},
              "units": {"intensity": "FLOP/B"}, "evidence_label": "[MODELED]"}
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = (f"# K1 result `[MODELED]`\n\n- Ridge = 989e12 / 3.35e12 = {ridge:.0f} FLOP/B\n"
          f"- Decode B=32: 2N × 32 / 2N = {decode:.0f} FLOP/B (attention with GQA {attn:.0f} FLOP/B) -> memory-bound\n"
          f"- Prefill 2,048: {prefill:.0f} FLOP/B -> compute-bound\n")
    (out / "result.md").write_text(md, encoding="utf-8")


if __name__ == "__main__":
    main()
