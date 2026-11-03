"""M2 - two hall designs on useful throughput per $ and per facility MW, with sensitivity and break-even.

python solve.py --out DIR.  Reads the package's lab/data/designs.yaml and assumptions.yaml [ILLUSTRATIVE];
results [MODELED].  Method (manuscript Sections 21.4-21.5): nodes = min(power fit, cooling fit);
useful units = nodes × 8 × per-GPU throughput × comm efficiency × usable fraction × 0.85 × 0.88;
TCO per Table 21.3 with staff scaled by nodes / 32 and each design's PUE.
"""
import argparse
import json
from pathlib import Path

import yaml

DATA = Path(__file__).resolve().parents[4] / "lab" / "data"
HOURS = 8760
THROUGHPUT_SWEEP = (1.6, 1.8, 1.86, 2.0, 2.2, 2.4)     # B per-GPU throughput vs A
PRICE_SWEEP = (0.06, 0.08, 0.12, 0.15, 0.20)           # $/kWh, applied to both designs
KEY = {"A": {"nodes": 87, "useful": 442.3, "per_musd": 26.69, "per_mw": 395.6},
       "B": {"nodes": 62, "useful": 644.9, "per_musd": 31.49, "per_mw": 645.0}}
KEY_B_AT_1_8 = 25.8
KEY_BREAK_EVEN = 1.86
KEY_SLOW_NET_REL = 1.64          # B per-GPU throughput if its network does not scale (2:1)
KEY_SLOW_NET_PER_MUSD = 25.2     # below A's 26.69
TOL = 0.06


def evaluate(d: dict, dz: dict, a: dict, usd_per_kwh: float, rel: float | None = None) -> dict:
    ov = a["network_storage_overhead"]
    pr = a["prices"]
    r = a["reserves"]
    uf = (1 - r["maintenance"]) * (1 - r["failure_repair"]) * (1 - r["fragmentation"])
    per_node_kw = d["provisioned_it_kw_per_node"] * (1 + ov)
    n_power = int(dz["facility_it_kw"] // per_node_kw)
    n_cool = (int(dz["liquid_cooling_kw_available"] // (d["provisioned_it_kw_per_node"] * d["liquid_fraction"]))
              if d["liquid_fraction"] > 0 else None)
    n = min(n_power, n_cool) if n_cool is not None else n_power
    rel = d["rel_throughput_per_gpu"] if rel is None else rel
    useful = n * d["gpus_per_node"] * rel * d["comm_efficiency"] * uf * a["target_allocation"] * a["goodput"]
    hw = n * (d["node_capex_usd"] + d["network_capex_per_node_usd"] + d.get("cooling_capex_per_node_usd", 0))
    comp = {"capex": hw / pr["amortization_years"],
            "power": n * d["sustained_it_kw_per_node"] * (1 + ov) * d["pue"] * HOURS * usd_per_kwh,
            "space": n * per_node_kw * pr["colo_usd_per_kw_month"] * 12,
            "support": pr["support_fraction_of_hw_capex"] * hw,
            "staff": pr["staff_usd_per_year"] * n / 32}
    total = sum(comp.values())
    fac_mw = n * d["sustained_it_kw_per_node"] * (1 + ov) * d["pue"] / 1000
    return {"nodes": n, "nodes_power_fit": n_power, "nodes_cooling_fit": n_cool, "gpus": n * d["gpus_per_node"],
            "useful_units": round(useful, 1), "tco_musd": round(total / 1e6, 3),
            "power_share": round(comp["power"] / total, 3), "per_musd": round(useful / (total / 1e6), 2),
            "per_facility_mw": round(useful / fac_mw, 1), "usd_per_gpu_year": round(total / (n * d["gpus_per_node"])),
            "usd_per_useful_unit_year": round(total / useful), "facility_mw": round(fac_mw, 3)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    a = yaml.safe_load((DATA / "assumptions.yaml").read_text(encoding="utf-8"))
    dz = yaml.safe_load((DATA / "designs.yaml").read_text(encoding="utf-8"))
    A, B = dz["designs"]
    base_price = a["prices"]["electricity_usd_per_kwh"]

    base = {"A": evaluate(A, dz, a, base_price), "B": evaluate(B, dz, a, base_price)}
    for k in ("A", "B"):
        for f, kf in (("nodes", "nodes"), ("useful_units", "useful"), ("per_musd", "per_musd"),
                      ("per_facility_mw", "per_mw")):
            assert abs(base[k][f] - KEY[k][kf]) <= (0 if f == "nodes" else TOL * max(1, KEY[k][kf] / 100)), (k, f)
    tp_rows = []
    for rel in THROUGHPUT_SWEEP:
        b = evaluate(B, dz, a, base_price, rel)
        tp_rows.append({"b_rel_throughput": rel, "b_per_musd": b["per_musd"], "a_per_musd": base["A"]["per_musd"],
                        "winner": "B" if b["per_musd"] > base["A"]["per_musd"] else "A"})
    b18 = next(r for r in tp_rows if r["b_rel_throughput"] == 1.8)["b_per_musd"]
    assert abs(b18 - KEY_B_AT_1_8) <= TOL
    break_even = B["rel_throughput_per_gpu"] * base["A"]["per_musd"] / base["B"]["per_musd"]
    assert abs(break_even - KEY_BREAK_EVEN) <= 0.01
    price_rows = []
    for p in PRICE_SWEEP:
        ea, eb = evaluate(A, dz, a, p), evaluate(B, dz, a, p)
        price_rows.append({"usd_per_kwh": p, "a_per_musd": ea["per_musd"], "b_per_musd": eb["per_musd"],
                           "b_over_a": round(eb["per_musd"] / ea["per_musd"], 3),
                           "a_power_share": ea["power_share"], "b_power_share": eb["power_share"]})
    assert all(r["b_over_a"] > 1 for r in price_rows), "electricity alone should not flip the ranking"
    # network does not speed up with compute: B's step relative to A's = compute / 2.2 + leaf-local comm
    # + spine-crossing comm × oversubscription (manuscript Section 21.5, "Two further caveats")
    f_exp, f_spine, oversub = 0.15, 0.5, 2
    step_1to1 = (1 - f_exp) / B["rel_throughput_per_gpu"] + f_exp
    step_2to1 = (1 - f_exp) / B["rel_throughput_per_gpu"] + f_exp * (1 - f_spine) + f_exp * f_spine * oversub
    rel_slow_net = 1 / step_2to1                  # per-GPU throughput vs A, communication efficiency included
    b_slow_net = base["B"]["per_musd"] * rel_slow_net / (B["rel_throughput_per_gpu"] * B["comm_efficiency"])
    assert abs(1 / step_1to1 - KEY_BREAK_EVEN) <= 0.01
    assert abs(rel_slow_net - KEY_SLOW_NET_REL) <= 0.01
    assert abs(b_slow_net - KEY_SLOW_NET_PER_MUSD) <= 0.1 and b_slow_net < base["A"]["per_musd"]

    sens_lines = ["parameter,value,a_per_musd,b_per_musd,winner"]
    sens_lines += [f"b_rel_throughput,{r['b_rel_throughput']},{r['a_per_musd']},{r['b_per_musd']},{r['winner']}"
                   for r in tp_rows]
    sens_lines += [f"usd_per_kwh,{r['usd_per_kwh']},{r['a_per_musd']},{r['b_per_musd']},"
                   f"{'B' if r['b_over_a'] > 1 else 'A'}" for r in price_rows]
    (out / "sensitivity.csv").write_text("\n".join(sens_lines) + "\n", encoding="utf-8")

    result = {"exercise": "M2", "evidence_label": "[MODELED]",
              "inputs": {"facility_it_kw": dz["facility_it_kw"], "liquid_cooling_kw": dz["liquid_cooling_kw_available"],
                         "base_usd_per_kwh": base_price, "throughput_sweep": list(THROUGHPUT_SWEEP),
                         "price_sweep": list(PRICE_SWEEP)},
              "steps": {"throughput_sensitivity": tp_rows, "price_sensitivity": price_rows,
                        "slow_network_step_vs_a_1to1": round(step_1to1, 3),
                        "slow_network_step_vs_a_2to1": round(step_2to1, 3),
                        "slow_network_rel_throughput": round(rel_slow_net, 3)},
              "answer": {"comparison": base, "break_even_b_rel_throughput": round(break_even, 3),
                         "b_per_musd_at_1_8x": b18, "b_per_musd_slow_network": round(b_slow_net, 1)},
              "units": {"useful_units": "HX8-GPU equivalents of useful work", "per_musd": "useful units per $M/yr",
                        "per_facility_mw": "useful units per facility MW"},
              "tolerance": TOL}
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = ["# M2 - two designs `[MODELED]`", "",
          "| Metric | A | B |", "|---|---|---|"]
    for f in ("nodes_power_fit", "nodes_cooling_fit", "nodes", "gpus", "useful_units", "tco_musd", "per_musd",
              "per_facility_mw", "usd_per_gpu_year", "usd_per_useful_unit_year", "power_share"):
        md.append(f"| {f} | {base['A'][f]} | {base['B'][f]} |")
    md += ["", f"Break-even: 2.2 × {base['A']['per_musd']} / {base['B']['per_musd']} = **{break_even:.2f}×**", "",
           f"If B's network does not scale with compute: step at 2:1 = {step_2to1:.3f} of A's -> "
           f"{rel_slow_net:.2f}× per GPU -> **{b_slow_net:.1f} per $M** (below A's {base['A']['per_musd']})", "",
           "| B per-GPU throughput | B per $M | A per $M | Winner |", "|---|---|---|---|"]
    md += [f"| {r['b_rel_throughput']} | {r['b_per_musd']} | {r['a_per_musd']} | {r['winner']} |" for r in tp_rows]
    md += ["", "| $/kWh | A per $M | B per $M | B / A |", "|---|---|---|---|"]
    md += [f"| {r['usd_per_kwh']} | {r['a_per_musd']} | {r['b_per_musd']} | {r['b_over_a']} |" for r in price_rows]
    md.append("")
    (out / "comparison.md").write_text("\n".join(md), encoding="utf-8")
    (out / "result.md").write_text("\n".join(md), encoding="utf-8")


if __name__ == "__main__":
    main()
