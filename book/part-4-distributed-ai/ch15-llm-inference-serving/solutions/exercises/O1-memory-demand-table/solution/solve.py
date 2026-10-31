"""O1 -- Memory demand (weights + KV) for T-tp4-fp8 vs batch and sequence length. [MODELED]

Usage: python solve.py --out DIR
Inputs: lab/data/configs.yaml (T-tp4-fp8, model, GPU); prompt (B = 16/64/128; 1k/4k/16k; 288 GB usable).
"""
import argparse
import json
import math
from pathlib import Path

import yaml

DATA = Path(__file__).resolve().parents[4] / "lab" / "data"
BATCHES = (16, 64, 128)
SEQS = (1024, 4096, 16384)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    cfg = yaml.safe_load((DATA / "configs.yaml").read_text(encoding="utf-8"))
    m, g = cfg["model"], cfg["gpu"]
    sc = next(s for s in cfg["serving_configs"] if s["name"] == "T-tp4-fp8")
    kvpt = 2 * m["n_layers"] * m["n_kv_heads"] * m["head_dim"] * m["kv_bytes_per_elem"]
    usable = sc["tp"] * float(g["hbm_bytes"]) * sc["mem_fraction"]
    w = float(sc["weight_bytes"])
    budget = usable - w - sc["tp"] * float(sc["reserve_bytes_per_gpu"])
    pool = int(budget // (sc["block_tokens"] * kvpt))
    table, over, max_seqs = {}, [], {}
    for L in SEQS:
        max_seqs[L] = pool // math.ceil(L / sc["block_tokens"])
        for b in BATCHES:
            kv = b * L * kvpt
            table[f"{L}x{b}"] = {"kv_GB": round(kv / 1e9, 1), "total_GB": round((w + kv) / 1e9, 1)}
            if w + kv > usable:
                over.append(f"{L}x{b}")
    # Key O1: usable 288 GB, KV budget 210 GB; 413.6 and 757.2 GB exceed; max seqs 625/156/39.
    assert abs(usable - 288e9) < 1 and abs(budget - 210e9) < 1
    assert table["16384x64"]["total_GB"] == 413.6 and table["16384x128"]["total_GB"] == 757.2
    assert table["4096x128"]["total_GB"] == 241.8 and table["1024x16"]["total_GB"] == 75.4
    assert over == ["16384x64", "16384x128"]
    assert [max_seqs[L] for L in SEQS] == [625, 156, 39]

    result = {"inputs": {"batches": list(BATCHES), "seq_lengths": list(SEQS), "kv_bytes_per_token": kvpt,
                         "weights_B": w, "usable_B": usable},
              "steps": {"kv_budget_B": budget, "pool_blocks": pool},
              "answer": {"table": table, "exceeds_usable": over, "max_seqs": {str(k): v for k, v in max_seqs.items()}},
              "units": {"memory": "GB (1e9 B)"}, "evidence_label": "[MODELED]"}
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# O1 memory demand, T-tp4-fp8 `[MODELED]`", "", "| Seq | B=16 | B=64 | B=128 | Max seqs |", "|---|---|---|---|---|"]
    for L in SEQS:
        cells = []
        for b in BATCHES:
            k = f"{L}x{b}"
            cells.append(f"{table[k]['total_GB']} GB" + (" (exceeds)" if k in over else ""))
        lines.append(f"| {L:,} | " + " | ".join(cells) + f" | {max_seqs[L]} |")
    lines += ["", "KV grows as B × context and dominates the 70 GB of weights at long context.", ""]
    (out / "result.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
