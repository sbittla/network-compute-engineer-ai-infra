#!/usr/bin/env python3
"""Chapter 21 hands-on lab: energy per unit of work and cost per useful GPU-hour from your measurements.

    python ch21_analyze.py results/<run-id> [cost_inputs.json]   # writes summary.json and report.md

Energy of a job = integral of GPU board power over its wall time (trapezoid on the ~100 ms samples).
Cost per useful GPU-hour follows Section 21.4's ladder: nominal $/GPU-h divided by usable x allocated x
goodput. The book's ORION figure ($3.00 nominal -> $4.72 useful) is reproduced beside yours.
"""
from __future__ import annotations

import json
import re
import shutil
import statistics
import sys
from pathlib import Path

from ch21_telemetry import energy_j, read_csv, window

HERE = Path(__file__).resolve().parent


def exit_ok(ctl: str, flag: str):
    """True/False from the '(exit N)' line after '$ nvidia-smi <flag> ...' in controls.txt; None if not tried."""
    m = re.search(r"\$ nvidia-smi " + re.escape(flag) + r"[^\n]*\n\(exit (\d+)\)", ctl)
    return None if m is None else m.group(1) == "0"


def main() -> None:
    run = Path(sys.argv[1])
    cost_path = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE / "cost_inputs.json"
    # The inputs used become part of the evidence. An explicit inputs file replaces the stored one.
    if len(sys.argv) > 2 or not (run / "cost_inputs.json").exists():
        shutil.copy(cost_path, run / "cost_inputs.json")
    C = json.loads((run / "cost_inputs.json").read_text())
    Y, O = C["yours"], C["orion"]
    tel = read_csv(run / "ch21_telemetry.csv")
    jobs = json.loads((run / "jobs.json").read_text())
    model = json.loads((run / "model.json").read_text())
    ctl = (run / "controls.txt").read_text()
    fpt = model["flop_per_token_6N"]

    idle = jobs["idle"]
    p_idle = energy_j(tel, idle["t0"], idle["t1"]) / idle["wall_s"]
    J: dict[str, dict] = {}
    for name, j in jobs.items():
        if name == "idle":
            continue
        e = energy_j(tel, j["t0"], j["t1"])
        rows = window(tel, j["t0"], j["t1"])
        avg_field = [r["power.draw.average"] for r in rows if isinstance(r.get("power.draw.average"), float)]
        J[name] = {
            "batch": j["batch"], "tokens": j["tokens"], "wall_s": j["wall_s"], "busy_s": j["busy_s"],
            "busy_fraction": j["busy_s"] / j["wall_s"], "samples": len(rows),
            "energy_j": e, "avg_power_w": e / j["wall_s"],
            "avg_power_from_average_field_w": statistics.mean(avg_field) if avg_field else None,
            "energy_above_idle_j": e - p_idle * j["wall_s"],
            "j_per_token": e / j["tokens"], "tokens_per_j": j["tokens"] / e,
            "kwh_per_million_tokens": e / j["tokens"] * 1e6 / 3.6e6,
            "tokens_per_s_wall": j["tokens"] / j["wall_s"], "tokens_per_s_busy": j["tokens"] / j["busy_s"],
            "achieved_tflops_busy": fpt * j["tokens"] / j["busy_s"] / 1e12,
            "tflop_per_j": fpt * j["tokens"] / e / 1e12,
            "sm_clock_mhz_median": statistics.median([r["clocks.sm"] for r in rows]) if rows else None,
            "sw_power_cap_fraction": (sum(1 for r in rows if isinstance(r.get("clocks_event_reasons.active"), int)
                                          and r["clocks_event_reasons.active"] & 0x4) / len(rows)) if rows else None,
            "enforced_limit_w": j.get("limits", {}).get("enforced.power.limit"),
        }
    full = J["intensity_b16"]
    for name, x in J.items():
        if name.startswith("duty_"):
            x["extra_energy_vs_full_duty_j"] = x["energy_j"] - full["energy_j"]
            x["extra_energy_fraction"] = x["energy_j"] / full["energy_j"] - 1

    # ---- cost per useful GPU-hour ----------------------------------------------------------------------
    orion_useful = O["usd_per_nominal_gpu_hour"] / (O["usable_fraction"] * O["allocated_fraction"] * O["goodput"])
    orion_step_usd = orion_useful * O["gpus"] * O["step_s"] / 3600
    orion = {"usd_per_nominal_gpu_hour": O["usd_per_nominal_gpu_hour"], "usd_per_useful_gpu_hour": orion_useful,
             "usd_per_million_tokens": orion_step_usd / (O["tokens_per_step"] / 1e6),
             "usd_per_pflop": orion_step_usd / (O["flop_per_step"] / 1e15),
             "it_tflop_per_j": O["flop_per_step"] / (O["it_kwh_per_step"] * 3.6e6) / 1e12,
             "facility_kwh_per_million_tokens": O["it_kwh_per_step"] * O["pue"] / (O["tokens_per_step"] / 1e6),
             "electricity_share_of_tco": O["electricity_share_of_tco"]}

    capex_h = Y["hardware_usd"] / (Y["amortization_years"] * 8760)
    alloc = Y["allocated_fraction"] * Y["usable_fraction"]

    def yours(x: dict) -> dict:
        p_work = x["avg_power_w"] + Y["host_power_w"]
        p_rest = p_idle + Y["host_power_w"]
        energy_h = (alloc * p_work + (1 - alloc) * p_rest) * Y["pue"] / 1000 * Y["electricity_usd_per_kwh"]
        nominal = capex_h + energy_h
        useful = nominal / (alloc * x["busy_fraction"])
        tok_per_useful_h = x["tokens_per_s_busy"] * 3600
        return {"usd_per_nominal_gpu_hour": nominal, "capex_usd_per_hour": capex_h, "energy_usd_per_hour": energy_h,
                "electricity_share": energy_h / nominal, "goodput_measured": x["busy_fraction"],
                "usd_per_useful_gpu_hour": useful, "usd_per_million_tokens": useful / (tok_per_useful_h / 1e6),
                "usd_per_pflop": useful / (x["achieved_tflops_busy"] * 3600 / 1000),
                "orion_rate_with_this_goodput": O["usd_per_nominal_gpu_hour"] / (O["usable_fraction"] * O["allocated_fraction"] * x["busy_fraction"])}

    cost = {name: yours(x) for name, x in J.items() if name == "intensity_b16" or name.startswith("duty_")}
    best = max((n for n in J if n.startswith("intensity_")), key=lambda n: J[n]["tokens_per_j"])
    S = {"idle_power_w": p_idle, "jobs": J, "cost_yours": cost, "cost_orion": orion,
         "most_efficient_intensity_job": best,
         "efficiency_gain_b16_vs_b1": J["intensity_b16"]["tokens_per_j"] / J["intensity_b1"]["tokens_per_j"],
         "power_limit_change_permitted": exit_ok(ctl, "-pl"),
         "clock_lock_probe": {None: "not attempted", True: "permitted", False: "refused"}[exit_ok(ctl, "-lgc")],
         "cap_sweep_run": any(n.startswith("cap_") for n in J),
         "inputs": C}
    (run / "summary.json").write_text(json.dumps(S, indent=2) + "\n")
    (run / "report.md").write_text(report(S))
    print((run / "report.md").read_text())


def report(S: dict) -> str:
    J, Cy, Co, Y = S["jobs"], S["cost_yours"], S["cost_orion"], S["inputs"]["yours"]
    L = ["# Chapter 21 hands-on: performance per watt and cost per useful GPU-hour", "",
         "Power, energy, throughput and busy fraction are `[MEASURED]` (board power from nvidia-smi at ~100 ms; "
         "energy = ∫P dt). FLOP counts and costs are `[MODELED]`; your cost inputs are `[ASSUMPTION]` "
         "(cost_inputs.json); ORION figures are the chapter's `[MODELED]` values.", "",
         "## Step 1: what you can vary here", "",
         f"- Power limit change permitted: **{S['power_limit_change_permitted']}**; clock lock: **{S['clock_lock_probe']}** "
         f"`[MEASURED]` (controls.txt). Power-cap sweep run: {S['cap_sweep_run']}.",
         f"- Idle board power {S['idle_power_w']:.1f} W `[MEASURED]`.", "",
         "## Steps 2-3: the same job (fixed tokens) at different intensity and busy fraction", "",
         "| Job | Batch | Busy fraction | Wall (s) | Avg power (W) | Energy (kJ) | J/token | Tokens/J | TFLOP/J | Tokens/s (wall) | SM clock (MHz) | Power cap |",
         "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for n, x in J.items():
        L.append(f"| {n} | {x['batch']} | {x['busy_fraction']:.2f} | {x['wall_s']:.1f} | {x['avg_power_w']:.1f} | "
                 f"{x['energy_j'] / 1e3:.2f} | {x['j_per_token'] * 1e3:.2f} m | {x['tokens_per_j']:.0f} | "
                 f"{x['tflop_per_j']:.3f} | {x['tokens_per_s_wall']:,.0f} | {x['sm_clock_mhz_median']:.0f} | "
                 f"{100 * (x['sw_power_cap_fraction'] or 0):.0f} % |")
    b1, b16 = J["intensity_b1"], J["intensity_b16"]
    L += ["", f"- Batch 16 does the job with {S['efficiency_gain_b16_vs_b1']:.2f}× the tokens per joule of batch 1 "
          f"(higher power, much shorter time) `[MEASURED]`."]
    for n, x in J.items():
        if n.startswith("duty_"):
            L.append(f"- {n}: busy {x['busy_fraction']:.2f}, energy +{100 * x['extra_energy_fraction']:.0f} % for the same tokens "
                     f"(idle-but-allocated watts) `[MEASURED]`.")
    L += ["", "## Step 4: cost per useful GPU-hour, yours beside ORION's", "",
          f"Your inputs `[ASSUMPTION]`: ${Y['hardware_usd']:,} over {Y['amortization_years']} years, "
          f"${Y['electricity_usd_per_kwh']}/kWh, PUE {Y['pue']}, host power {Y['host_power_w']} W, "
          f"allocated {Y['allocated_fraction']:.2f} of owned hours.", "",
          "| Case | Nominal $/GPU-h | Goodput | $/useful GPU-h | $/M tokens | $/PFLOP | Electricity share |",
          "|---|---:|---:|---:|---:|---:|---:|",
          f"| ORION (book, Section 21.4) `[MODELED]` | {Co['usd_per_nominal_gpu_hour']:.2f} | 0.88 | "
          f"{Co['usd_per_useful_gpu_hour']:.2f} | {Co['usd_per_million_tokens']:.2f} (70B) | {Co['usd_per_pflop']:.4f} | "
          f"{100 * Co['electricity_share_of_tco']:.0f} % |"]
    for n, c in Cy.items():
        L.append(f"| Yours, {n} | {c['usd_per_nominal_gpu_hour']:.4f} | {c['goodput_measured']:.2f} | "
                 f"{c['usd_per_useful_gpu_hour']:.3f} | {c['usd_per_million_tokens']:.3f} (63M) | {c['usd_per_pflop']:.4f} | "
                 f"{100 * c['electricity_share']:.0f} % |")
    L += ["", "ORION's $3.00 rate with your measured goodput in place of 0.88 `[MODELED]`: " +
          ", ".join(f"{n} → ${c['orion_rate_with_this_goodput']:.2f}" for n, c in Cy.items()) + ".", "",
          "## Energy per unit of work against ORION", "",
          f"- ORION W-TRAIN: {Co['it_tflop_per_j']:.2f} TFLOP/J at the IT load (whole node, 40 % MFU) and "
          f"{Co['facility_kwh_per_million_tokens']:.2f} facility kWh per million tokens of a 70B model `[MODELED]`.",
          f"- This GPU at batch 16: {b16['tflop_per_j']:.3f} TFLOP/J (board only) and "
          f"{b16['kwh_per_million_tokens']:.4f} kWh per million tokens of a 63M model `[MEASURED]`; "
          f"at batch 1: {b1['tflop_per_j']:.3f} TFLOP/J.",
          "- Compare per FLOP, not per token: a token of a 70B model is ≈ 1,100× the work of a token of this model.", ""]
    return "\n".join(L)


if __name__ == "__main__":
    main()
