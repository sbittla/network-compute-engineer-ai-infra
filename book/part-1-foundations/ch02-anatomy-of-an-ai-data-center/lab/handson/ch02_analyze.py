#!/usr/bin/env python3
"""Chapter 2 hands-on lab: turn the 100 ms telemetry into per-phase power, clock and throttling evidence.

    python ch02_analyze.py results/<run-id>     # writes summary.json and report.md there
"""
from __future__ import annotations

import json
import re
import statistics
import sys
from pathlib import Path

from ch02_telemetry import read_csv, reasons, stats, window

ORION = {"gpu_compute_w": 700, "gpu_comm_w": 300, "tdp_w": 700}  # Section 2.6 [ILLUSTRATIVE]
COUNTERS = ["clocks_event_reasons_counters.sw_power_cap", "clocks_event_reasons_counters.sw_thermal_slowdown",
            "clocks_event_reasons_counters.hw_thermal_slowdown", "clocks_event_reasons_counters.hw_power_brake_slowdown"]


def main() -> None:
    run = Path(sys.argv[1])
    tel = read_csv(run / "ch02_telemetry.csv")
    ph = json.loads((run / "phases.json").read_text())
    cnt = json.loads((run / "counters.json").read_text())
    avail = json.loads((run / "field_availability.json").read_text())
    ctl = (run / "power_controls.txt").read_text()
    P = "power.draw.instant" if "power.draw.instant" in tel[0] else "power.draw"
    limit = next((c["enforced.power.limit"] for c in cnt.values() if isinstance(c.get("enforced.power.limit"), float)), None)
    max_sm = float(avail["clocks.max.sm"].split()[0]) if not avail.get("clocks.max.sm", "U").startswith("U") else None

    def summarize(name: str) -> dict:
        t0, t1 = ph[name]
        rows = window(tel, t0, t1)
        # skip the first 20 % of a long phase for "steady state" numbers; keep all rows for temperature
        steady = [r for r in rows if r["t"] >= t0 + 0.2 * (t1 - t0)] or rows
        masks = [r.get("clocks_event_reasons.active") for r in steady if isinstance(r.get("clocks_event_reasons.active"), int)]
        frac = lambda bit: sum(1 for m in masks if m & bit) / len(masks) if masks else None  # noqa: E731
        d = {"duration_s": t1 - t0, "samples": len(rows),
             "power_w": stats([r.get(P) for r in steady]),
             "power_avg_field_w": stats([r.get("power.draw.average") for r in steady]),
             "sm_clock_mhz": stats([r.get("clocks.sm") for r in steady]),
             "mem_clock_mhz": stats([r.get("clocks.mem") for r in steady]),
             "temp_c": {"start": rows[0].get("temperature.gpu") if rows else None,
                        "end": rows[-1].get("temperature.gpu") if rows else None,
                        "max": max((r.get("temperature.gpu") for r in rows), default=None)},
             "util_gpu_pct": stats([r.get("utilization.gpu") for r in steady]),
             "frac_idle": frac(0x1), "frac_sw_power_cap": frac(0x4), "frac_sw_thermal": frac(0x20),
             "frac_hw_slowdown": frac(0x8 | 0x40 | 0x80),
             "reasons_seen": sorted({x for m in masks for x in reasons(m)})}
        if limit:
            d["power_over_limit"] = d["power_w"].get("median", 0) / limit
        a, b = cnt.get(f"{name}:start"), cnt.get(f"{name}:end")
        if a and b and "error" not in a and "error" not in b:
            d["counter_delta_us"] = {c.split(".")[-1]: b[c] - a[c] for c in COUNTERS
                                     if isinstance(a.get(c), (int, float)) and isinstance(b.get(c), (int, float))}
            d["counter_fraction_of_phase"] = {k: v / 1e6 / (t1 - t0) for k, v in d["counter_delta_us"].items()}
        return d

    names = ["idle", "memory", "compute", "cooldown"] + sorted(k for k in ph if k.startswith("ramp_d")) + ["idle_end"]
    S: dict = {"enforced_power_limit_w": limit, "max_sm_clock_mhz": max_sm, "power_field": P,
               "phases": {n: summarize(n) for n in names}}
    dts = [b["t"] - a["t"] for a, b in zip(tel, tel[1:])]
    S["sampling"] = {"requested_ms": 100, "median_interval_ms": statistics.median(dts) * 1e3,
                     "p95_interval_ms": sorted(dts)[int(0.95 * (len(dts) - 1))] * 1e3, "samples": len(tel)}
    S["fields_unavailable"] = sorted(f for f, v in avail.items() if v.startswith("UNAVAILABLE"))
    S["power_limit_change_permitted"] = not bool(re.search(r"Insufficient Permissions|not supported|Unknown Error|exit [1-9]", ctl.split("$ nvidia-smi -pl")[-1])) if "$ nvidia-smi -pl" in ctl else None

    ph_ = S["phases"]
    # Where does the power limit bind? The lowest ramp duty cycle whose steady-state power reaches 95 % of
    # the enforced limit or whose samples mostly carry the SW Power Cap reason.
    ramp = [(int(n[6:]), ph_[n]) for n in names if n.startswith("ramp_d")]
    # A duty-cycled load is judged by its *mean* power (the energy the power controller averages), not the
    # median of samples that alias with the on/off pattern.
    binds = next((d for d, r in ramp if r["power_w"]["mean"] >= 0.95 * (limit or 1e9) or (r["frac_sw_power_cap"] or 0) >= 0.5), None)
    S["ramp"] = [{"duty_pct": d, "power_w": r["power_w"]["mean"], "power_p95_w": r["power_w"]["p95"],
                  "sm_clock_mhz": r["sm_clock_mhz"]["mean"],
                  "frac_sw_power_cap": r["frac_sw_power_cap"], "temp_max_c": r["temp_c"]["max"]} for d, r in ramp]
    S["power_limit_binds_from_duty_pct"] = binds

    # Square wave: per-cycle high and low plateaus, swing and 10-90 % rise time.
    on = sorted((k for k in ph if k.startswith("square_on_")), key=lambda k: int(k.rsplit("_", 1)[1]))
    highs, lows, rises = [], [], []
    for k in on:
        i = k.rsplit("_", 1)[1]
        t0, t1 = ph[k]
        h = [r[P] for r in window(tel, t0 + 0.4, t1)]
        lo = [r[P] for r in window(tel, ph[f"square_off_{i}"][0] + 0.5, ph[f"square_off_{i}"][1])]
        if h and lo:
            hi_v, lo_v = statistics.median(h), statistics.median(lo)
            highs.append(hi_v); lows.append(lo_v)
            prev = window(tel, t0 - 0.3, t1)
            p10, p90 = lo_v + 0.1 * (hi_v - lo_v), lo_v + 0.9 * (hi_v - lo_v)
            ta = next((r["t"] for r in prev if r["t"] >= t0 - 0.15 and r[P] >= p10), None)
            tb = next((r["t"] for r in prev if r["t"] >= t0 - 0.15 and r[P] >= p90), None)
            if ta is not None and tb is not None:
                rises.append(tb - ta)
    S["square"] = {"cycles": len(highs), "high_w": statistics.median(highs) if highs else None,
                   "low_w": statistics.median(lows) if lows else None,
                   "swing_w": (statistics.median(highs) - statistics.median(lows)) if highs else None,
                   "rise_10_90_s_median": statistics.median(rises) if rises else None,
                   "rise_resolution_s": S["sampling"]["median_interval_ms"] / 1e3}
    if highs:
        S["square"]["low_over_high"] = S["square"]["low_w"] / S["square"]["high_w"]
    S["orion_comparison"] = {"orion_low_over_high": ORION["gpu_comm_w"] / ORION["gpu_compute_w"],
                             "orion_swing_per_gpu_w": ORION["gpu_compute_w"] - ORION["gpu_comm_w"]}
    m, c = ph_["memory"], ph_["compute"]
    S["findings"] = {
        "compute_power_w": c["power_w"]["median"], "memory_power_w": m["power_w"]["median"],
        "idle_power_w": ph_["idle"]["power_w"]["median"],
        "compute_sm_clock_mhz": c["sm_clock_mhz"]["median"], "memory_sm_clock_mhz": m["sm_clock_mhz"]["median"],
        "compute_frac_sw_power_cap": c["frac_sw_power_cap"], "memory_frac_sw_power_cap": m["frac_sw_power_cap"],
        "compute_frac_sw_thermal": c["frac_sw_thermal"],
        "compute_temp_max_c": c["temp_c"]["max"],
        "compute_counter_power_cap_fraction": c.get("counter_fraction_of_phase", {}).get("sw_power_cap"),
        "power_limit_binds_in_compute": (c.get("power_over_limit", 0) >= 0.95) or (c["frac_sw_power_cap"] or 0) >= 0.5,
        "power_limit_binds_in_memory": (m.get("power_over_limit", 0) >= 0.95) or (m["frac_sw_power_cap"] or 0) >= 0.5,
    }
    (run / "summary.json").write_text(json.dumps(S, indent=2) + "\n")
    (run / "report.md").write_text(report(S))
    print((run / "report.md").read_text())


def report(S: dict) -> str:
    f, ph, sq = S["findings"], S["phases"], S["square"]
    pct = lambda v: "n/a" if v is None else f"{100 * v:.0f} %"  # noqa: E731
    L = ["# Chapter 2 hands-on: power, clocks and throttling", "",
         "All values are `[MEASURED]` from `nvidia-smi --query-gpu=... -lms 100` on this machine unless "
         "labelled otherwise. ORION numbers are the chapter's `[ILLUSTRATIVE]` values.", "",
         "## Platform", "",
         f"- Enforced power limit {S['enforced_power_limit_w']} W; maximum SM clock {S['max_sm_clock_mhz']} MHz `[MEASURED]`.",
         f"- Sampling: requested 100 ms, achieved median {S['sampling']['median_interval_ms']:.0f} ms "
         f"(p95 {S['sampling']['p95_interval_ms']:.0f} ms) over {S['sampling']['samples']} samples `[MEASURED]`.",
         f"- Fields this platform does not report: {', '.join(S['fields_unavailable']) or 'none'} `[MEASURED]`.",
         f"- Changing the power limit permitted: {S['power_limit_change_permitted']} `[MEASURED]` (see power_controls.txt).", "",
         "## Steps 2-4: phases (steady state, first 20 % of each phase skipped)", "",
         "| Phase | Power median (W) | p95 (W) | Power / limit | SM clock (MHz) | Mem clock (MHz) | Temp start→max (°C) | SW power cap | SW thermal | Counter: power-cap time / phase |",
         "|---|---:|---:|---:|---:|---:|---|---:|---:|---:|"]
    for n, d in ph.items():
        cf = d.get("counter_fraction_of_phase", {}).get("sw_power_cap")
        L.append(f"| {n} | {d['power_w']['median']:.1f} | {d['power_w']['p95']:.1f} | {d.get('power_over_limit', 0):.2f} | "
                 f"{d['sm_clock_mhz']['median']:.0f} | {d['mem_clock_mhz']['median']:.0f} | "
                 f"{d['temp_c']['start']:.0f}→{d['temp_c']['max']:.0f} | {pct(d['frac_sw_power_cap'])} | "
                 f"{pct(d['frac_sw_thermal'])} | {pct(cf)} |")
    L += ["", "## Step 5: where the power limit binds (GEMM duty-cycle ramp)", "",
          "| Duty cycle | Power mean (W) | Power p95 (W) | SM clock mean (MHz) | SW power cap |", "|---:|---:|---:|---:|---:|"]
    for r in S["ramp"]:
        L.append(f"| {r['duty_pct']} % | {r['power_w']:.1f} | {r['power_p95_w']:.1f} | {r['sm_clock_mhz']:.0f} | {pct(r['frac_sw_power_cap'])} |")
    b = S["power_limit_binds_from_duty_pct"]
    L += ["", f"The limit binds from **{b} % duty** `[MEASURED]`." if b else "The limit did not bind in the ramp `[MEASURED]`.", "",
          "## Step 6: the step-boundary swing (1 s compute, 1 s idle)", "",
          f"- High {sq['high_w']:.1f} W, low {sq['low_w']:.1f} W, swing {sq['swing_w']:.1f} W per GPU; low/high = "
          f"{sq['low_over_high']:.2f} `[MEASURED]` over {sq['cycles']} cycles.",
          (f"- 10-90 % rise: within one sample ({sq['rise_resolution_s']:.2f} s) `[MEASURED]`: the true edge is faster "
           "than a 100 ms sampler can resolve (Table 2.5 puts it at tens of milliseconds)."
           if (sq['rise_10_90_s_median'] or 0) < sq['rise_resolution_s'] else
           f"- 10-90 % rise time {sq['rise_10_90_s_median']:.2f} s `[MEASURED]` at a sampling resolution of {sq['rise_resolution_s']:.2f} s."),
          f"- ORION (Section 2.6): 700 W compute, 300 W exposed communication, low/high = "
          f"{S['orion_comparison']['orion_low_over_high']:.2f}, 400 W swing per GPU `[ILLUSTRATIVE]`.", "",
          "## Findings", "",
          f"- Compute phase: {f['compute_power_w']:.1f} W at SM {f['compute_sm_clock_mhz']:.0f} MHz, SW power cap in "
          f"{pct(f['compute_frac_sw_power_cap'])} of samples `[MEASURED]`: the power limit "
          f"{'binds' if f['power_limit_binds_in_compute'] else 'does not bind'}.",
          f"- Memory phase: {f['memory_power_w']:.1f} W at SM {f['memory_sm_clock_mhz']:.0f} MHz, SW power cap in "
          f"{pct(f['memory_frac_sw_power_cap'])} `[MEASURED]`: the limit "
          f"{'binds' if f['power_limit_binds_in_memory'] else 'does not bind'}.",
          f"- Idle {f['idle_power_w']:.1f} W; peak temperature in the compute phase {f['compute_temp_max_c']:.0f} °C, "
          f"SW thermal slowdown in {pct(f['compute_frac_sw_thermal'])} of its samples `[MEASURED]`.",
          f"- Violation counter for the compute phase: power-capped for {pct(f['compute_counter_power_cap_fraction'])} of the "
          f"phase, against the flag in {pct(f['compute_frac_sw_power_cap'])} of samples `[MEASURED]`. Where these disagree, "
          "the platform's counter is not measuring what Section 2.6 assumes; trust the flag and the clock.", ""]
    return "\n".join(L)


if __name__ == "__main__":
    main()
