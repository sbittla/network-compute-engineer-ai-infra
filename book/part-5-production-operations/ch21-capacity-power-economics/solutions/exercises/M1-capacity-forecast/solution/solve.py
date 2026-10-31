"""M1 - capacity forecast, p50 (the lab plan) and p90 (+25 % demand from 2028Q3), with order-by dates.

python solve.py --out DIR.  Reads the package's lab/data/quarterly_plan.csv and assumptions.yaml
[ILLUSTRATIVE]; results [MODELED].  Method (manuscript Sections 21.2, 21.3 and 21.9):
installed = cumulative deliveries - retirements; energizable = floor(kW / 1.428 / 8) × 8; energized = min;
usable = energized × usable fraction; required = demand / 0.85; shortfall when usable < required.
Binding resource: compare the energized GPUs the quarter needs (required / usable fraction) with what is
installed and with what the facility can energize.
"""
import argparse
import json
import math
from pathlib import Path

import pandas as pd
import yaml

DATA = Path(__file__).resolve().parents[4] / "lab" / "data"
P90_UPLIFT = 1.25              # prompt: +25 % demand
P90_FROM = "2028Q3"            # prompt: from 2028Q3 onwards
KEY_P50 = {"2028Q3": (475.8, 494.1, -18.3), "2029Q4": (870.0, 964.7, -94.7)}
KEY_P90 = {"2028Q3": (475.8, 617.6, -141.9), "2029Q2": (890.4, 926.5, -36.1),
           "2029Q3": (870.0, 1058.8, -188.8), "2029Q4": (870.0, 1205.9, -335.9)}
KEY_BINDING = {"p50": {"2028Q3": "power", "2029Q4": "gpus+power"},
               "p90": {"2028Q3": "power", "2029Q2": "power", "2029Q3": "gpus+power", "2029Q4": "gpus+power"}}
KEY_FIRST_ORDER_BY = {"gpus": "2028Q1", "network": "2028Q2", "facility_power": "2027Q3"}
TOL = 0.15                     # GPUs (table values are rounded to 0.1)


def quarter_add(q: str, n: int) -> str:
    idx = int(q[:4]) * 4 + int(q[5]) - 1 + n
    return f"{idx // 4}Q{idx % 4 + 1}"


def forecast(plan: pd.DataFrame, a: dict, uplift: float) -> pd.DataFrame:
    r = a["reserves"]
    uf = (1 - r["maintenance"]) * (1 - r["failure_repair"]) * (1 - r["fragmentation"])
    kw_gpu = a["provisioned_it_kw_per_node"] * (1 + a["network_storage_overhead"]) / a["gpus_per_node"]
    g = a["gpus_per_node"]
    installed = a["initial_installed_gpus"]
    rows = []
    for p in plan.itertuples():
        installed += int(p.gpus_delivered) - int(p.gpus_decommissioned)
        energizable = int(math.floor(p.facility_it_kw / kw_gpu / g)) * g
        energized = min(installed, energizable)
        usable = energized * uf
        demand = (int(p.demand_train_gpus) + int(p.demand_infer_gpus)) * (uplift if p.quarter >= P90_FROM else 1.0)
        required = demand / a["target_allocation"]
        need_energized = required / uf
        if usable >= required:
            binding = ""
        elif installed >= need_energized:
            binding = "power"
        elif energizable >= need_energized:
            binding = "gpus"
        else:
            binding = "gpus+power"
        rows.append({"quarter": p.quarter, "installed": installed, "energizable": energizable, "energized": energized,
                     "stranded": installed - energized, "usable": round(usable, 1), "demand": round(demand, 2),
                     "required": round(required, 1), "gap": round(usable - required, 1),
                     "status": "OK" if usable >= required else "SHORTFALL", "binding": binding,
                     "energized_gpus_needed": math.ceil(need_energized / g) * g})
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    a = yaml.safe_load((DATA / "assumptions.yaml").read_text(encoding="utf-8"))
    plan = pd.read_csv(DATA / "quarterly_plan.csv", keep_default_na=False).drop_duplicates()
    assert not plan.quarter.duplicated().any(), "conflicting duplicate quarters need a human"
    plan = plan.sort_values("quarter").reset_index(drop=True)
    lead = a["lead_time_quarters"]

    summary = {}
    for name, uplift, key in (("p50", 1.0, KEY_P50), ("p90", P90_UPLIFT, KEY_P90)):
        fc = forecast(plan, a, uplift)
        fc.to_csv(out / f"forecast_{name}.csv", index=False, lineterminator="\n")
        short = fc[fc.status == "SHORTFALL"]
        assert list(short.quarter) == list(key), (name, list(short.quarter))
        for q, (u, req, gap) in key.items():
            row = fc[fc.quarter == q].iloc[0]
            assert abs(row.usable - u) <= TOL and abs(row.required - req) <= TOL and abs(row.gap - gap) <= TOL, (name, q)
            assert row.binding == KEY_BINDING[name][q], (name, q, row.binding)
        shortfalls = {}
        for row in short.itertuples():
            res = {"power": ["facility_power"], "gpus": ["gpus", "network"],
                   "gpus+power": ["gpus", "network", "facility_power"]}[row.binding]
            shortfalls[row.quarter] = {"usable": row.usable, "required": row.required, "gap": row.gap,
                                       "binding": row.binding,
                                       "energized_gpus_needed": int(row.energized_gpus_needed),
                                       "order_by": {k: quarter_add(row.quarter, -lead[k]) for k in res}}
        first = short.quarter.iloc[0]
        first_order = {k: quarter_add(first, -v) for k, v in lead.items()}
        assert first_order == KEY_FIRST_ORDER_BY
        summary[name] = {"first_shortfall": first, "order_by_first_shortfall": first_order, "shortfalls": shortfalls}

    result = {"exercise": "M1", "evidence_label": "[MODELED]",
              "inputs": {"p90_uplift": P90_UPLIFT, "p90_from": P90_FROM, "lead_time_quarters": lead,
                         "target_allocation": a["target_allocation"]},
              "steps": {"files": ["forecast_p50.csv", "forecast_p90.csv"]},
              "answer": summary, "units": {"capacity": "GPUs", "dates": "quarters"}, "tolerance_gpus": TOL}
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = ["# M1 - capacity forecast `[MODELED]`", ""]
    for name, s in summary.items():
        md += [f"## {name}", "", f"First shortfall {s['first_shortfall']}; order-by "
               + ", ".join(f"{k} {v}" for k, v in s["order_by_first_shortfall"].items()), "",
               "| Quarter | Usable | Required | Gap | Binding | Energized GPUs needed | Order-by |", "|---|---|---|---|---|---|---|"]
        for q, v in s["shortfalls"].items():
            md.append(f"| {q} | {v['usable']} | {v['required']} | {v['gap']} | {v['binding']} | "
                      f"{v['energized_gpus_needed']} | " + ", ".join(f"{k} {d}" for k, d in v["order_by"].items()) + " |")
        md.append("")
    (out / "result.md").write_text("\n".join(md), encoding="utf-8")


if __name__ == "__main__":
    main()
