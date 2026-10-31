"""O4 -- 10 req/s with 8,192-token prompts: shared vs disaggregated (RDMA, TCP), per-layer overlap, FP8 KV. [MODELED]

Usage: python solve.py --out DIR
Inputs: lab/data/configs.yaml with the prompt's change (request_rate 10, prompt 8,192, output 256).
Model: lab Part C compare_designs (Section 15.10), linear prefill.
"""
import argparse
import copy
import json
import math
from pathlib import Path

import yaml

DATA = Path(__file__).resolve().parents[4] / "lab" / "data"
CHANGE = {"request_rate": 10.0, "prompt_tokens": 8192, "output_tokens": 256}


def md1(rho, s):
    return math.inf if rho >= 1 else rho * s / (2 * (1 - rho))


def designs(cfg: dict) -> dict:
    g, m, d = cfg["gpu"], cfg["model"], cfg["disaggregation"]
    sc = next(s for s in cfg["serving_configs"] if s["name"] == d["replica_config"])
    kvpt = 2 * m["n_layers"] * m["n_kv_heads"] * m["head_dim"] * m["kv_bytes_per_elem"]
    lam, P, O = d["request_rate"], d["prompt_tokens"], d["output_tokens"]
    ctx = P + O / 2
    t_p = 2 * float(m["n_params"]) * P / (sc["tp"] * float(g["fp8_peak_flops"]) * sc["prefill_mfu"])
    bw = sc["tp"] * float(g["hbm_bw"]) * sc["hbm_efficiency"]
    t_fix = sc["step_overhead_s"] + float(sc["weight_bytes"]) / bw
    c = ctx * kvpt / bw
    kv = P * kvpt
    agg = lam * kv * 8 / 1e9
    rows = {}
    n = d["shared_replicas"]
    rho = lam / n * t_p
    r = lam / n
    tpot = t_fix / ((1 - rho) - c * r * O)
    b = r * O * tpot
    rows["shared"] = {"rho": rho, "ttft_s": t_p + md1(rho, t_p), "tpot_ms": tpot * 1e3,
                      "itl_worst_ms": (t_fix + c * b + t_p) * 1e3, "link_util_pct": 0.0, "kv_transfer_ms": 0.0}
    npf, nd = d["prefill_replicas"], d["decode_replicas"]
    rho = lam / npf * t_p
    rd = lam / nd
    td = t_fix / (1 - c * rd * O)
    for name, t in d["transports"].items():
        ach = t["link_gbps"] * t["links_per_replica"] * t["efficiency"]
        t_kv = t["fixed_latency_s"] + kv / (ach * 1e9 / 8)
        rows[f"disagg-{name}"] = {"rho": rho, "ttft_s": t_p + md1(rho, t_p), "tpot_ms": (td + t_kv / (O - 1)) * 1e3,
                                  "itl_worst_ms": (td + t_kv) * 1e3, "link_util_pct": 100 * agg / nd / ach,
                                  "kv_transfer_ms": t_kv * 1e3,
                                  "per_layer_ms": kv / m["n_layers"] / (ach * 1e9 / 8) * 1e3}
    return {"t_p_s": t_p, "kv_bytes": kv, "agg_Gbps": agg, "per_decode_Gbps": agg / nd,
            "prefill_per_layer_ms": t_p / m["n_layers"] * 1e3, "rows": rows}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    base = yaml.safe_load((DATA / "configs.yaml").read_text(encoding="utf-8"))
    cfg = copy.deepcopy(base)
    cfg["disaggregation"].update(CHANGE)
    bf = designs(cfg)
    fp8 = copy.deepcopy(cfg)
    fp8["model"]["kv_bytes_per_elem"] = 1
    f8 = designs(fp8)
    R = bf["rows"]
    # Key O4 checks (tolerances in the units shown).
    checks = [(bf["kv_bytes"], 2_684_354_560, 0), (bf["agg_Gbps"], 214.7, 0.05), (bf["per_decode_Gbps"], 107.4, 0.05),
              (R["disagg-rdma"]["kv_transfer_ms"], 15.8, 0.05), (R["disagg-tcp"]["kv_transfer_ms"], 215.7, 0.05),
              (R["shared"]["rho"], 0.453, 0.001), (R["shared"]["ttft_s"], 0.512, 0.001), (R["shared"]["tpot_ms"], 23.0, 0.05),
              (R["shared"]["itl_worst_ms"], 375, 0.5), (R["disagg-rdma"]["rho"], 0.604, 0.001),
              (R["disagg-rdma"]["ttft_s"], 0.638, 0.001), (R["disagg-rdma"]["tpot_ms"], 16.7, 0.05),
              (R["disagg-rdma"]["itl_worst_ms"], 32.5, 0.05), (R["disagg-tcp"]["tpot_ms"], 17.5, 0.05),
              (R["disagg-tcp"]["itl_worst_ms"], 232, 0.5), (R["disagg-rdma"]["link_util_pct"], 7.9, 0.05),
              (R["disagg-tcp"]["link_util_pct"], 107, 0.5), (bf["prefill_per_layer_ms"], 4.53, 0.005),
              (R["disagg-rdma"]["per_layer_ms"], 0.20, 0.005), (R["disagg-tcp"]["per_layer_ms"], 2.68, 0.005),
              (f8["agg_Gbps"], 107.4, 0.05), (f8["per_decode_Gbps"], 53.7, 0.05),
              (f8["rows"]["disagg-rdma"]["kv_transfer_ms"], 7.9, 0.05), (f8["rows"]["disagg-tcp"]["kv_transfer_ms"], 108, 0.5),
              (f8["rows"]["disagg-tcp"]["link_util_pct"], 54, 0.5)]
    for got, want, tol in checks:
        assert abs(got - want) <= tol, (got, want)
    assert R["disagg-tcp"]["per_layer_ms"] < bf["prefill_per_layer_ms"]   # uncontended TCP could hide per layer

    def rnd(d):
        return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in d.items()}
    result = {"inputs": {"change": CHANGE, "yaml": "lab/data/configs.yaml"},
              "steps": {"t_p_ms": round(bf["t_p_s"] * 1e3, 1), "prefill_per_layer_ms": round(bf["prefill_per_layer_ms"], 2)},
              "answer": {"kv_bytes_per_request": bf["kv_bytes"], "aggregate_Gbps": round(bf["agg_Gbps"], 1),
                         "per_decode_replica_Gbps": round(bf["per_decode_Gbps"], 1),
                         "designs": {k: rnd(v) for k, v in R.items()},
                         "fp8_kv": {"aggregate_Gbps": round(f8["agg_Gbps"], 1),
                                    "rdma_ms": round(f8["rows"]["disagg-rdma"]["kv_transfer_ms"], 1),
                                    "tcp_ms": round(f8["rows"]["disagg-tcp"]["kv_transfer_ms"], 1),
                                    "tcp_util_pct": round(f8["rows"]["disagg-tcp"]["link_util_pct"], 1)}},
              "units": {"bandwidth": "Gb/s", "time": "ms or s"}, "evidence_label": "[MODELED]"}
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# O4 result `[MODELED]`", "", f"KV/request {bf['kv_bytes']:,} B; aggregate {bf['agg_Gbps']:.1f} Gb/s", "",
             "| Design | rho | TTFT | TPOT | Worst ITL | Link util |", "|---|---|---|---|---|---|"]
    for k, v in R.items():
        lines.append(f"| {k} | {v['rho']:.3f} | {v['ttft_s']:.3f} s | {v['tpot_ms']:.1f} ms | {v['itl_worst_ms']:.1f} ms | "
                     f"{v['link_util_pct']:.1f} % |")
    lines += ["", f"Per layer: prefill {bf['prefill_per_layer_ms']:.2f} ms; RDMA {R['disagg-rdma']['per_layer_ms']:.2f} ms; "
              f"TCP {R['disagg-tcp']['per_layer_ms']:.2f} ms",
              f"FP8 KV: {f8['agg_Gbps']:.1f} Gb/s; RDMA {f8['rows']['disagg-rdma']['kv_transfer_ms']:.1f} ms; "
              f"TCP {f8['rows']['disagg-tcp']['kv_transfer_ms']:.0f} ms", ""]
    (out / "result.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
