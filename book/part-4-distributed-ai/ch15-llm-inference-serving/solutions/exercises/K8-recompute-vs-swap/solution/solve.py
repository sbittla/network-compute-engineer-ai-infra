"""K8 -- Cost of preempting a 10k-token sequence on a TP = 2 FP8 replica: recompute vs swap. [MODELED]

Usage: python solve.py --out DIR
Inputs: lab/data/configs.yaml (model, FP8 peak, BF16 KV, MFU 0.40); prompt (10,000 tokens, TP = 2);
[ILLUSTRATIVE] PCIe Gen5 x16 at 50 GB/s achievable per GPU per direction.
"""
import argparse
import json
from pathlib import Path

import yaml

DATA = Path(__file__).resolve().parents[4] / "lab" / "data"
TOKENS = 10_000
TP = 2
PCIE_BPS = 50e9


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    cfg = yaml.safe_load((DATA / "configs.yaml").read_text(encoding="utf-8"))
    m, g = cfg["model"], cfg["gpu"]
    mfu = cfg["serving_configs"][1]["prefill_mfu"]
    kvpt = 2 * m["n_layers"] * m["n_kv_heads"] * m["head_dim"] * m["kv_bytes_per_elem"]
    per_token = 2 * float(m["n_params"]) / (TP * float(g["fp8_peak_flops"]) * mfu)
    recompute = TOKENS * per_token
    kv_total = TOKENS * kvpt
    per_gpu = kv_total / TP
    swap_one_way = per_gpu / PCIE_BPS
    # Key K8: 88.4 us/token -> 0.88 s; 3.28 GB, 1.64 GB per GPU, ≈ 33 ms each way.
    assert abs(per_token * 1e6 - 88.4) < 0.05 and abs(recompute - 0.884) < 0.001
    assert abs(kv_total / 1e9 - 3.28) < 0.005 and abs(per_gpu / 1e9 - 1.64) < 0.005
    assert abs(swap_one_way * 1e3 - 33) < 0.5

    result = {"inputs": {"tokens": TOKENS, "tp": TP, "mfu": mfu, "kv_bytes_per_token": kvpt, "pcie_Bps": PCIE_BPS},
              "steps": {"prefill_us_per_token": round(per_token * 1e6, 2), "kv_bytes": kv_total},
              "answer": {"recompute_s": round(recompute, 3), "swap_GB_total": round(kv_total / 1e9, 2),
                         "swap_GB_per_gpu": round(per_gpu / 1e9, 2), "swap_one_way_ms": round(swap_one_way * 1e3, 1),
                         "swap_round_trip_ms": round(2 * swap_one_way * 1e3, 1)},
              "units": {"time": "s or ms", "bytes": "GB (1e9 B)"}, "evidence_label": "[MODELED]"}
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = (f"# K8 result `[MODELED]`\n\n- Recompute: 10,000 × {per_token*1e6:.1f} µs = {recompute:.2f} s\n"
          f"- Swap: {kv_total/1e9:.2f} GB ({per_gpu/1e9:.2f} GB per GPU) at 50 GB/s = {swap_one_way*1e3:.1f} ms each way\n")
    (out / "result.md").write_text(md, encoding="utf-8")


if __name__ == "__main__":
    main()
