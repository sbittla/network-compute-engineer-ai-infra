"""W1 - ORION-256 TCO with 5-year amortization, PUE 1.25, $0.12/kWh, allocation 0.80, goodput 0.90.

python solve.py --out DIR.  Unchanged inputs are read from the package's lab/data/assumptions.yaml
[ILLUSTRATIVE]; the prompt's changes are named constants below. Results [MODELED].
Method (manuscript Section 21.4, Table 21.1a): capex/yr + power + space + support + staff; cost per GPU-hour
on each rung: nominal, allocated = nominal × usable fraction × allocation, useful = allocated × goodput.
"""
import argparse
import json
from pathlib import Path

import yaml

DATA = Path(__file__).resolve().parents[4] / "lab" / "data"
HOURS = 8760
NODES = 32                         # ORION-256
SERVER_USD = 320_000               # Section 21.4 / lab README Task 3
NETWORK_USD = 85_000
STORAGE_USD = 2_000_000            # fixed capex
# prompt changes
AMORTIZATION_YEARS = 5
PUE = 1.25
USD_PER_KWH = 0.12
ALLOCATION = 0.80
GOODPUT = 0.90
KEY = {"capex": 2.992e6, "power": 0.400e6, "space": 0.570e6, "support": 1.197e6, "staff": 0.960e6,
       "total": 6.119e6, "usd_per_nominal": 2.73, "usd_per_allocated": 4.01, "usd_per_useful": 4.46}
TOL_USD = 1_000                    # per component, $/yr (key is given to $1k)
TOL_UNIT = 0.005                   # $/GPU-h


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    a = yaml.safe_load((DATA / "assumptions.yaml").read_text(encoding="utf-8"))
    pr, ov, r = a["prices"], a["network_storage_overhead"], a["reserves"]

    hw = NODES * (SERVER_USD + NETWORK_USD) + STORAGE_USD
    capex = hw / AMORTIZATION_YEARS
    it_sustained_kw = NODES * a["sustained_it_kw_per_node"] * (1 + ov)
    power = it_sustained_kw * PUE * HOURS * USD_PER_KWH
    prov_kw = NODES * a["provisioned_it_kw_per_node"] * (1 + ov)
    space = prov_kw * pr["colo_usd_per_kw_month"] * 12
    support = pr["support_fraction_of_hw_capex"] * hw
    staff = pr["staff_usd_per_year"]
    total = capex + power + space + support + staff
    usable = (1 - r["maintenance"]) * (1 - r["failure_repair"]) * (1 - r["fragmentation"])
    nominal_h = NODES * a["gpus_per_node"] * HOURS
    alloc_frac = usable * ALLOCATION
    per_nom = total / nominal_h
    per_alloc = per_nom / alloc_frac
    per_useful = per_alloc / GOODPUT
    # common mistake: replace the 0.85 inside the usable fraction instead of applying 0.80 after it
    wrong_useful = per_nom / ALLOCATION / GOODPUT

    comps = {"capex": capex, "power": power, "space": space, "support": support, "staff": staff, "total": total}
    for k, v in comps.items():
        assert abs(v - KEY[k]) <= (TOL_USD if k != "total" else 2 * TOL_USD), (k, v)
    for k, v in (("usd_per_nominal", per_nom), ("usd_per_allocated", per_alloc), ("usd_per_useful", per_useful)):
        assert abs(v - KEY[k]) <= TOL_UNIT, (k, v)

    result = {
        "exercise": "W1", "evidence_label": "[MODELED]",
        "inputs": {"nodes": NODES, "hardware_capex_usd": hw, "amortization_years": AMORTIZATION_YEARS, "pue": PUE,
                   "usd_per_kwh": USD_PER_KWH, "allocation": ALLOCATION, "goodput": GOODPUT,
                   "usable_fraction": round(usable, 4), "colo_usd_per_kw_month": pr["colo_usd_per_kw_month"],
                   "support_fraction": pr["support_fraction_of_hw_capex"], "staff_usd": staff},
        "steps": {"it_sustained_kw": round(it_sustained_kw, 2), "provisioned_kw": round(prov_kw, 2),
                  "nominal_gpu_h": nominal_h, "allocated_fraction": round(alloc_frac, 4),
                  "shares": {k: round(v / total, 3) for k, v in comps.items() if k != "total"},
                  "wrong_useful_if_allocation_replaces_usable": round(wrong_useful, 2)},
        "answer": {"components_usd_per_year": {k: round(v) for k, v in comps.items()},
                   "usd_per_nominal_gpu_h": round(per_nom, 2), "usd_per_allocated_gpu_h": round(per_alloc, 2),
                   "usd_per_useful_gpu_h": round(per_useful, 2)},
        "units": {"components": "USD per year", "unit_costs": "USD per GPU-hour"},
        "tolerance": {"component_usd": TOL_USD, "unit_cost_usd": TOL_UNIT},
    }
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = ["# W1 - TCO under different assumptions `[MODELED]`", "",
          "| Component | Formula | $/yr |", "|---|---|---|",
          f"| Capex | ${hw / 1e6:.2f}M / {AMORTIZATION_YEARS} | {capex:,.0f} |",
          f"| Power | {it_sustained_kw:.2f} kW × {PUE} × {HOURS} h × ${USD_PER_KWH} | {power:,.0f} |",
          f"| Space | {prov_kw:.2f} kW × ${pr['colo_usd_per_kw_month']} × 12 | {space:,.0f} |",
          f"| Support | {pr['support_fraction_of_hw_capex']} × ${hw / 1e6:.2f}M | {support:,.0f} |",
          f"| Staff | 4 FTE | {staff:,.0f} |",
          f"| **Total** | | **{total:,.0f}** |", "",
          f"- nominal: {total:,.0f} / {nominal_h:,} GPU-h = **${per_nom:.2f}**",
          f"- allocated: {per_nom:.4f} / ({usable:.4f} × {ALLOCATION}) = ${per_alloc:.2f}",
          f"- useful: {per_alloc:.4f} / {GOODPUT} = **${per_useful:.2f}**", ""]
    (out / "result.md").write_text("\n".join(md), encoding="utf-8")


if __name__ == "__main__":
    main()
