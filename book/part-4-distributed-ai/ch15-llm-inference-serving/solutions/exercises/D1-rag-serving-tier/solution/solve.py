"""D1 -- RAG serving tier: disaggregated P/D sizing, KV network budget, transport, shared alternative. [MODELED]

Usage: python solve.py --out DIR
Inputs: prompt (20 req/s, 8,192 in / 300 out, TTFT p95 <= 1.5 s, TPOT p95 <= 40 ms, T-tp4-fp8, quadratic
attention term included) and lab/data/configs.yaml (model, GPU, T-tp4-fp8, RDMA/TCP transports).
Approximation used for p95 TTFT: t_p + 3 × mean M/D/1 wait (stated in answer.md).
"""
import argparse
import json
import math
from pathlib import Path

import yaml

DATA = Path(__file__).resolve().parents[4] / "lab" / "data"
RATE, PROMPT, OUT = 20.0, 8192, 300
D_MODEL = 64 * 128
P_SWEEP, D_SWEEP = (11, 12, 13), (3, 4, 5)
CHOICE_P, CHOICE_D = 13, 4
SHARED_N, CHUNK = 16, 512


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    cfg = yaml.safe_load((DATA / "configs.yaml").read_text(encoding="utf-8"))
    m, g, dis = cfg["model"], cfg["gpu"], cfg["disaggregation"]
    sc = next(s for s in cfg["serving_configs"] if s["name"] == "T-tp4-fp8")
    kvpt = 2 * m["n_layers"] * m["n_kv_heads"] * m["head_dim"] * m["kv_bytes_per_elem"]
    eff = sc["tp"] * float(g["fp8_peak_flops"]) * sc["prefill_mfu"]
    t_lin = 2 * float(m["n_params"]) * PROMPT / eff
    t_att = 2 * m["n_layers"] * PROMPT ** 2 * D_MODEL / eff
    t_p = t_lin + t_att
    bw = sc["tp"] * float(g["hbm_bw"]) * sc["hbm_efficiency"]
    t_fix = sc["step_overhead_s"] + float(sc["weight_bytes"]) / bw
    c = (PROMPT + OUT / 2) * kvpt / bw

    prefill = {}
    for p in P_SWEEP:
        rho = RATE / p * t_p
        wq = rho * t_p / (2 * (1 - rho))
        prefill[p] = {"rho": round(rho, 3), "ttft_mean_s": round(t_p + wq, 3), "ttft_p95_approx_s": round(t_p + 3 * wq, 2)}
    decode = {}
    for d in D_SWEEP:
        r = RATE / d
        tpot = t_fix / (1 - c * r * OUT)
        decode[d] = {"tpot_ms": round(tpot * 1e3, 1), "batch": round(r * OUT * tpot, 1)}
    budget = sc["tp"] * float(g["hbm_bytes"]) * sc["mem_fraction"] - float(sc["weight_bytes"]) \
        - sc["tp"] * float(sc["reserve_bytes_per_gpu"])
    blocks_seq = math.ceil((PROMPT + OUT) / sc["block_tokens"])
    fit_bf16 = int(budget // (sc["block_tokens"] * kvpt)) // blocks_seq
    fit_fp8 = int(budget // (sc["block_tokens"] * kvpt / 2)) // blocks_seq
    nodes = math.ceil((CHOICE_P + CHOICE_D) / sc["replicas_per_node"]) + 1

    kv_req = PROMPT * kvpt
    agg = RATE * kv_req * 8 / 1e9
    per_dec = agg / CHOICE_D
    tr = {}
    for name, t in dis["transports"].items():
        ach = t["link_gbps"] * t["links_per_replica"] * t["efficiency"]
        t_kv = t["fixed_latency_s"] + kv_req / (ach * 1e9 / 8)
        tr[name] = {"achievable_Gbps": ach, "util_pct": round(100 * per_dec / ach, 1), "transfer_ms": round(t_kv * 1e3, 1),
                    "per_layer_ms": round(kv_req / m["n_layers"] / (ach * 1e9 / 8) * 1e3, 2)}
    prefill_per_layer = t_p / m["n_layers"]

    rho_s = RATE / SHARED_N * t_p
    ttft_s = t_p + rho_s * t_p / (2 * (1 - rho_s))
    r_s = RATE / SHARED_N
    tpot_s = t_fix / ((1 - rho_s) - c * r_s * OUT)
    b_s = r_s * OUT * tpot_s
    itl_s = t_fix + c * b_s + t_p
    chunk_ms = CHUNK * 2 * float(m["n_params"]) / eff * 1e3
    lost_seqs = decode[CHOICE_D]["batch"]
    reprefill = lost_seqs * t_p
    rho_minus1 = RATE / (CHOICE_P - 1) * t_p

    # Key D1 checks (tolerances in the units shown).
    checks = [(t_lin * 1e3, 362.2, 0.1), (t_att * 1e3, 27.8, 0.1), (t_p * 1e3, 390.0, 0.1), (RATE * t_p, 7.80, 0.01),
              (prefill[11]["ttft_mean_s"], 0.865, 0.001), (prefill[12]["ttft_mean_s"], 0.752, 0.001),
              (prefill[13]["ttft_mean_s"], 0.682, 0.001), (prefill[11]["ttft_p95_approx_s"], 1.82, 0.01),
              (prefill[12]["ttft_p95_approx_s"], 1.48, 0.01), (prefill[13]["ttft_p95_approx_s"], 1.27, 0.01),
              (decode[3]["tpot_ms"], 25.1, 0.05), (decode[4]["tpot_ms"], 18.6, 0.05), (decode[5]["tpot_ms"], 16.1, 0.05),
              (decode[3]["batch"], 50.2, 0.05), (decode[4]["batch"], 27.9, 0.05), (decode[5]["batch"], 19.3, 0.05),
              (blocks_seq, 531, 0), (fit_bf16, 75, 0), (fit_fp8, 150, 0), (nodes, 10, 0),
              (kv_req / 1e9, 2.684, 0.001), (agg, 429.5, 0.1), (per_dec, 107.4, 0.1),
              (tr["rdma"]["util_pct"], 7.9, 0.05), (tr["rdma"]["transfer_ms"], 15.8, 0.05), (tr["tcp"]["util_pct"], 107.4, 0.1),
              (tr["rdma"]["per_layer_ms"], 0.2, 0.01), (prefill_per_layer * 1e3, 4.9, 0.05),
              (rho_s, 0.4875, 0.0001), (ttft_s, 0.575, 0.001), (tpot_s * 1e3, 26.0, 0.1), (itl_s * 1e3, 403, 1),
              (chunk_ms, 22.6, 0.05), (reprefill, 11, 0.2), (rho_minus1, 0.65, 0.001)]
    for got, want, tol in checks:
        assert abs(got - want) <= tol, (got, want)
    assert tr["tcp"]["util_pct"] > 100 and tr["rdma"]["per_layer_ms"] < prefill_per_layer * 1e3

    result = {"inputs": {"rate": RATE, "prompt": PROMPT, "out": OUT, "replica": "T-tp4-fp8"},
              "steps": {"t_p_linear_ms": round(t_lin * 1e3, 1), "t_p_attention_ms": round(t_att * 1e3, 1),
                        "t_p_ms": round(t_p * 1e3, 1), "prefill_demand": round(RATE * t_p, 2),
                        "c_ms_per_seq": round(c * 1e3, 4), "blocks_per_seq": blocks_seq},
              "answer": {"prefill_pool": {str(k): v for k, v in prefill.items()},
                         "decode_pool": {str(k): v for k, v in decode.items()},
                         "choice": {"prefill": CHOICE_P, "decode": CHOICE_D, "nodes_incl_spare": nodes},
                         "kv_fit_per_replica": {"bf16": fit_bf16, "fp8": fit_fp8},
                         "network": {"kv_GB_per_request": round(kv_req / 1e9, 3), "aggregate_Gbps": round(agg, 1),
                                     "per_decode_replica_Gbps": round(per_dec, 1), "transports": tr,
                                     "prefill_per_layer_ms": round(prefill_per_layer * 1e3, 2), "decision": "rdma"},
                         "shared_alternative": {"replicas": SHARED_N, "rho": round(rho_s, 4), "ttft_s": round(ttft_s, 3),
                                                "tpot_ms": round(tpot_s * 1e3, 1), "itl_worst_ms": round(itl_s * 1e3),
                                                "chunk_512_ms": round(chunk_ms, 1)},
                         "failures": {"decode_loss_seqs": round(lost_seqs), "reprefill_replica_s": round(reprefill, 1),
                                      "prefill_loss_rho": round(rho_minus1, 3)}},
              "units": {"time": "s or ms", "bandwidth": "Gb/s"}, "evidence_label": "[MODELED]"}
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# D1 sizing `[MODELED]`", "", f"t_p = {t_lin*1e3:.1f} + {t_att*1e3:.1f} = {t_p*1e3:.1f} ms", "",
             "| P | rho | mean TTFT | ≈ p95 TTFT |", "|---|---|---|---|"]
    lines += [f"| {p} | {v['rho']} | {v['ttft_mean_s']} s | {v['ttft_p95_approx_s']} s |" for p, v in prefill.items()]
    lines += ["", "| D | TPOT | B |", "|---|---|---|"]
    lines += [f"| {d} | {v['tpot_ms']} ms | {v['batch']} |" for d, v in decode.items()]
    lines += ["", f"Choice {CHOICE_P}P + {CHOICE_D}D -> {nodes} nodes incl. spare",
              f"KV {kv_req/1e9:.3f} GB/req; aggregate {agg:.1f} Gb/s; RDMA {tr['rdma']['util_pct']} % "
              f"({tr['rdma']['transfer_ms']} ms); TCP {tr['tcp']['util_pct']} % (infeasible)", ""]
    (out / "result.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
