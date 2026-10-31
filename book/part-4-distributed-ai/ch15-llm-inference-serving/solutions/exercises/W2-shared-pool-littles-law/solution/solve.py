"""W2 -- Sizing a shared T-tp4-fp8 pool for document QA (25 req/s, 4,096 in / 512 out). [MODELED]

Usage: python solve.py --out DIR
Inputs: prompt (rate, lengths, SLOs, 6/8/10/12 replicas) and lab/data/configs.yaml (T-tp4-fp8 and model).
Model: manuscript Section 15.7 / lab compare_designs, shared pool: rho = r t_p; TTFT = t_p + M/D/1 wait;
TPOT (1 - rho) = t_d(B), B = r × out × TPOT, t_d at average context prompt + out/2.
"""
import argparse
import json
import math
from pathlib import Path

import yaml

DATA = Path(__file__).resolve().parents[4] / "lab" / "data"
RATE, PROMPT, OUT = 25.0, 4096, 512
POOLS = (6, 8, 10, 12)
CHOICE = 10
D_MODEL = 64 * 128      # 64 query heads × head_dim 128 (W-INFER)
KEY = {8: (0.566, 0.299, 54.8, 87.7), 10: (0.453, 0.256, 29.7, 38.0), 12: (0.377, 0.236, 22.7, 24.2)}


def fixed_point(r, t_fix, c, rho):
    """Solve TPOT (1 - rho) = t_fix + c r OUT TPOT; None when unstable."""
    denom = (1 - rho) - c * r * OUT
    return None if denom <= 0 else t_fix / denom


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    cfg = yaml.safe_load((DATA / "configs.yaml").read_text(encoding="utf-8"))
    m, g = cfg["model"], cfg["gpu"]
    sc = next(s for s in cfg["serving_configs"] if s["name"] == "T-tp4-fp8")
    kvpt = 2 * m["n_layers"] * m["n_kv_heads"] * m["head_dim"] * m["kv_bytes_per_elem"]
    eff_flops = sc["tp"] * float(g["fp8_peak_flops"]) * sc["prefill_mfu"]
    t_p = 2 * float(m["n_params"]) * PROMPT / eff_flops
    t_attn = 2 * m["n_layers"] * PROMPT ** 2 * D_MODEL / eff_flops   # 2 × L × P^2 × d_model
    bw = sc["tp"] * float(g["hbm_bw"]) * sc["hbm_efficiency"]
    t_fix = sc["step_overhead_s"] + float(sc["weight_bytes"]) / bw
    ctx = PROMPT + OUT / 2
    c = ctx * kvpt / bw
    rows = {}
    for n in POOLS:
        r = RATE / n
        rho = r * t_p
        ttft = t_p + rho * t_p / (2 * (1 - rho))
        tpot = fixed_point(r, t_fix, c, rho)
        rows[n] = {"lambda_r": round(r, 3), "rho": round(rho, 4), "ttft_s": round(ttft, 3),
                   "tpot_ms": None if tpot is None else round(tpot * 1e3, 1),
                   "batch": None if tpot is None else round(r * OUT * tpot, 1),
                   "decode_demand": round(c * r * OUT, 3), "free_fraction": round(1 - rho, 3)}
    # Key W2 checks (tolerances: rho 0.001, TTFT 1 ms, TPOT 0.1 ms, B 0.2).
    assert abs(t_p * 1e3 - 181.1) < 0.1 and abs(RATE * t_p - 4.53) < 0.005 and abs(t_attn * 1e3 - 6.9) < 0.1
    assert abs(c * 1e3 - 0.15203) < 1e-5
    assert rows[6]["tpot_ms"] is None and abs(rows[6]["ttft_s"] - 0.460) < 0.001
    for n, (rho, ttft, tpot, b) in KEY.items():
        rr = rows[n]
        assert abs(rr["rho"] - rho) < 0.001 and abs(rr["ttft_s"] - ttft) < 0.001, rr
        assert abs(rr["tpot_ms"] - tpot) < 0.1 and abs(rr["batch"] - b) < 0.2, rr
    b_ch = rows[CHOICE]["batch"]
    itl_worst = t_fix + c * b_ch + t_p
    per_seq_blocks = math.ceil((PROMPT + OUT) / sc["block_tokens"])
    budget = sc["tp"] * float(g["hbm_bytes"]) * sc["mem_fraction"] - float(sc["weight_bytes"]) \
        - sc["tp"] * float(sc["reserve_bytes_per_gpu"])
    max_seqs = int(budget // (sc["block_tokens"] * kvpt)) // per_seq_blocks
    assert abs(itl_worst * 1e3 - 197) < 1 and per_seq_blocks == 288 and max_seqs == 139

    result = {"inputs": {"rate": RATE, "prompt": PROMPT, "out": OUT, "pools": list(POOLS)},
              "steps": {"t_p_ms": round(t_p * 1e3, 1), "attention_term_ms": round(t_attn * 1e3, 1),
                        "prefill_demand_replica_s_per_s": round(RATE * t_p, 2), "t_fix_ms": round(t_fix * 1e3, 3),
                        "c_ms_per_seq": round(c * 1e3, 5)},
              "answer": {"table": {str(k): v for k, v in rows.items()}, "unstable": [6], "choice": CHOICE,
                         "choice_with_spares": CHOICE + 2, "itl_worst_unchunked_ms": round(itl_worst * 1e3, 1),
                         "kv_blocks_per_seq": per_seq_blocks, "kv_max_seqs": max_seqs},
              "units": {"ttft": "s", "tpot": "ms", "batch": "sequences"}, "evidence_label": "[MODELED]"}
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# W2 result `[MODELED]`", "", f"t_p = {t_p*1e3:.1f} ms; demand = {RATE*t_p:.2f} replica-s/s", "",
             "| Replicas | lambda_r | rho | Mean TTFT | Mean TPOT | B |", "|---|---|---|---|---|---|"]
    for n, rr in rows.items():
        tp = "unstable" if rr["tpot_ms"] is None else f"{rr['tpot_ms']} ms"
        lines.append(f"| {n} | {rr['lambda_r']} | {rr['rho']:.3f} | {rr['ttft_s']:.3f} s | {tp} | {rr['batch'] or '-'} |")
    lines += ["", f"Choice {CHOICE} (+2 spares); worst unchunked ITL {itl_worst*1e3:.0f} ms; "
              f"KV: {per_seq_blocks} blocks/seq -> {max_seqs} sequences per replica", ""]
    (out / "result.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
