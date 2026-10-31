"""O5 -- Speculative decoding: expected tokens, memory-bound speedup, and roofline-derived verify cost at B = 128. [MODELED]

Usage: python solve.py --out DIR
Inputs: prompt (alpha 0.6/0.8/0.9, k 2/4/8, draft cost 0.05, B = 128, 20.2 ms decode step on T-tp4-fp8) and
lab/data/configs.yaml (T-tp4-fp8, model, GPU). E = (1 - a^(k+1)) / (1 - a) (Leviathan et al.).
"""
import argparse
import json
from pathlib import Path

import yaml

DATA = Path(__file__).resolve().parents[4] / "lab" / "data"
ALPHAS = (0.6, 0.8, 0.9)
KS = (2, 4, 8)
DRAFT = 0.05
B = 128
KEY_E = {(0.6, 2): 1.96, (0.6, 4): 2.31, (0.6, 8): 2.48, (0.8, 2): 2.44, (0.8, 4): 3.36, (0.8, 8): 4.33,
         (0.9, 2): 2.71, (0.9, 4): 4.10, (0.9, 8): 6.13}
KEY_S1 = {(0.6, 2): 1.78, (0.6, 4): 1.92, (0.6, 8): 1.77, (0.8, 2): 2.22, (0.8, 4): 2.80, (0.8, 8): 3.09,
          (0.9, 2): 2.46, (0.9, 4): 3.41, (0.9, 8): 4.38}
KEY_SV = {(0.6, 2): 1.78, (0.6, 4): 1.32, (0.6, 8): 0.81, (0.8, 2): 2.22, (0.8, 4): 1.92, (0.8, 8): 1.41,
          (0.9, 2): 2.46, (0.9, 4): 2.34, (0.9, 8): 1.99}
KEY_V = {2: 1.00, 4: 1.55, 8: 2.67}


def expected(a: float, k: int) -> float:
    return (1 - a ** (k + 1)) / (1 - a)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    cfg = yaml.safe_load((DATA / "configs.yaml").read_text(encoding="utf-8"))
    m, g, w = cfg["model"], cfg["gpu"], cfg["workload"]
    sc = next(s for s in cfg["serving_configs"] if s["name"] == "T-tp4-fp8")
    kvpt = 2 * m["n_layers"] * m["n_kv_heads"] * m["head_dim"] * m["kv_bytes_per_elem"]
    ctx = w["prompt_tokens"] + w["output_tokens"] / 2
    hbm_s = (float(sc["weight_bytes"]) + B * ctx * kvpt) / (sc["tp"] * float(g["hbm_bw"]) * sc["hbm_efficiency"])
    step = hbm_s + sc["step_overhead_s"]
    per_tok = 2 * float(m["n_params"]) / (sc["tp"] * float(g["fp8_peak_flops"]) * sc["prefill_mfu"])
    v = {}
    for k in KS:
        compute = B * (k + 1) * per_tok
        v[k] = (max(compute, hbm_s) + sc["step_overhead_s"]) / step
    E = {(a, k): expected(a, k) for a in ALPHAS for k in KS}
    S1 = {(a, k): E[(a, k)] / (DRAFT * k + 1) for a in ALPHAS for k in KS}
    SV = {(a, k): E[(a, k)] / (DRAFT * k + v[k]) for a in ALPHAS for k in KS}
    # Key O5 checks: tables to 2 decimals (tolerance 0.006), v_k to 0.01, step 20.2 ms.
    assert abs(step * 1e3 - 20.2) < 0.05 and abs(hbm_s * 1e3 - 17.19) < 0.01
    for key in E:
        assert abs(E[key] - KEY_E[key]) < 0.006 and abs(S1[key] - KEY_S1[key]) < 0.006, key
        assert abs(SV[key] - KEY_SV[key]) < 0.006, (key, SV[key])
    for k in KS:
        assert abs(v[k] - KEY_V[k]) < 0.01, (k, v[k])
    interactive_k = 4
    throughput_k = max(KS, key=lambda k: min(SV[(a, k)] for a in ALPHAS))
    assert throughput_k == 2 and SV[(0.6, 8)] < 1

    def tbl(d):
        return {f"a={a},k={k}": round(x, 2) for (a, k), x in d.items()}
    result = {"inputs": {"alphas": list(ALPHAS), "ks": list(KS), "draft_cost": DRAFT, "batch": B},
              "steps": {"decode_step_ms": round(step * 1e3, 2), "hbm_ms": round(hbm_s * 1e3, 2),
                        "compute_us_per_token": round(per_tok * 1e6, 2),
                        "verify_compute_ms": {str(k): round(B * (k + 1) * per_tok * 1e3, 2) for k in KS}},
              "answer": {"expected_tokens": tbl(E), "speedup_memory_bound": tbl(S1),
                         "verify_cost": {str(k): round(x, 2) for k, x in v.items()}, "speedup_B128": tbl(SV),
                         "recommend_interactive_k": interactive_k, "recommend_throughput_k": throughput_k},
              "units": {"speedup": "x vs plain decoding", "time": "ms"}, "evidence_label": "[MODELED]"}
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# O5 result `[MODELED]`", ""]
    for title, d in (("Expected tokens E", E), ("Speedup, verify cost 1", S1), ("Speedup at B = 128", SV)):
        lines += [f"## {title}", "", "| alpha \\ k | 2 | 4 | 8 |", "|---|---|---|---|"]
        lines += [f"| {a} | " + " | ".join(f"{d[(a, k)]:.2f}" for k in KS) + " |" for a in ALPHAS]
        lines.append("")
    lines += [f"v_k = " + ", ".join(f"k={k}: {v[k]:.2f}" for k in KS),
              f"Interactive k = {interactive_k}; throughput tier k = {throughput_k}", ""]
    (out / "result.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
