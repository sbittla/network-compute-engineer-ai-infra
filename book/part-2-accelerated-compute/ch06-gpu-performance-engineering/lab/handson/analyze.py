#!/usr/bin/env python3
"""Ch 6 hands-on: apply the pre-registered protocol to the raw runs and write summary.json and report.md.

    python3 analyze.py results/<run-id>  [--threshold 1.0]

Pre-registered before any data is seen (Section 6.6):
  - warm-up: the first `warmup` iterations of every run are discarded (they stay in runs.jsonl);
  - unit of replication: the run; each run is summarised by its median iteration time;
  - primary statistic: difference in arm means of run medians, % of the baseline arm's mean (stats.py);
  - band: 95 % percentile bootstrap over runs; test: exact permutation test of the same statistic;
  - noise floor: the A/A comparison (base vs aa), the largest of |point|, |band bounds|;
  - practical threshold: 1 %;
  - clock rule: a run is excluded if its median SM clock is < 95 % of its own arm's median run clock, or if
    thermal or hardware slowdown is active in > 5 % of its telemetry samples. The peer clock is per arm
    because a change to the kernels can move the sustained clock (Section 6.5, Pitfall).
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stats  # noqa: E402

LABEL = {"base": "AdamW foreach (baseline)", "aa": "A/A: identical to baseline", "fused": "AdamW fused",
         "zero": "zero_grad(set_to_none=False)"}


def load_telemetry(p: Path) -> list[dict]:
    rows = []
    if not p.exists():
        return rows
    rd = csv.reader(p.open())
    hdr = next(rd, None)
    for r in rd:
        if len(r) < 11:
            continue
        try:
            t = dt.datetime.strptime(r[0].strip(), "%Y/%m/%d %H:%M:%S.%f").timestamp()
            def num(x):
                try:
                    return float(x.strip().split()[0])
                except (ValueError, IndexError):
                    return float("nan")
            rows.append({"t": t, "sm": num(r[1]), "mem": num(r[2]), "temp": num(r[3]), "power": num(r[4]),
                         "util": num(r[5]), "active": r[6].strip(), "sw_power_cap": r[7].strip() == "Active",
                         "hw_slowdown": r[8].strip() == "Active", "sw_thermal": r[9].strip() == "Active",
                         "hw_thermal": r[10].strip() == "Active"})   # the alternative is "Not Active"
        except ValueError:
            continue
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--threshold", type=float, default=1.0)
    a = ap.parse_args()
    out = Path(a.out)
    runs = [json.loads(x) for x in (out / "runs.jsonl").read_text().splitlines() if x.strip()]
    tel = load_telemetry(out / "telemetry.csv")

    per_run = []
    for r in runs:
        w = r["warmup"]
        steady = r["ms"][w:]
        samples = [t for t in tel if r["t_loop"] <= t["t"] <= r["t_end"]]
        clocks = [t["sm"] for t in samples if t["sm"] == t["sm"]]
        slow = sum(1 for t in samples if t["hw_slowdown"] or t["sw_thermal"] or t["hw_thermal"])
        per_run.append({"arm": r["arm"], "run": r["run"], "order": r["order"], "median_ms": statistics.median(steady),
                        "first_iter_ms": r["ms"][0], "warmup_mean_ms": statistics.mean(r["ms"][:w]) if w else None,
                        "iqr_ms": statistics.quantiles(steady, n=4)[2] - statistics.quantiles(steady, n=4)[0],
                        "samples": len(samples), "sm_clock_mhz": statistics.median(clocks) if clocks else None,
                        "max_temp_c": max((t["temp"] for t in samples), default=None),
                        "slowdown_frac": slow / len(samples) if samples else 0.0,
                        "sw_power_cap_frac": (sum(t["sw_power_cap"] for t in samples) / len(samples)) if samples else 0.0})
    arms = sorted({p["arm"] for p in per_run}, key=lambda x: list(LABEL).index(x) if x in LABEL else 99)
    excluded = []
    for arm in arms:
        rs = [p for p in per_run if p["arm"] == arm]
        clk = [p["sm_clock_mhz"] for p in rs if p["sm_clock_mhz"]]
        peer = statistics.median(clk) if clk else None
        for p in rs:
            p["peer_clock_mhz"] = peer
            reason = ""
            if peer and p["sm_clock_mhz"] and p["sm_clock_mhz"] < 0.95 * peer:
                reason = f"clock {p['sm_clock_mhz']:.0f} < 95 % of arm peer {peer:.0f} MHz"
            elif p["slowdown_frac"] > 0.05:
                reason = f"thermal/hardware slowdown in {100 * p['slowdown_frac']:.0f} % of samples"
            p["excluded"] = reason
            if reason:
                excluded.append({"arm": arm, "run": p["run"], "reason": reason})
    kept = {arm: [p["median_ms"] for p in per_run if p["arm"] == arm and not p["excluded"]] for arm in arms}

    s: dict = {"lab": "ch06-handson", "run_id": out.name, "threshold_pct": a.threshold, "excluded_runs": excluded}
    naive = json.loads((out / "step1_naive.json").read_text().strip().splitlines()[-1])
    s["step1_naive"] = naive
    firsts = [p["first_iter_ms"] / p["median_ms"] for p in per_run]
    s["step2_warmup"] = {"first_over_steady_median": statistics.median(firsts), "max": max(firsts),
                         "runs": len(firsts)}
    s["arms"] = {}
    for arm in arms:
        rs = [p for p in per_run if p["arm"] == arm]
        s["arms"][arm] = {"what": LABEL.get(arm, arm), "runs": len(rs), "kept": len(kept[arm]),
                          "run_medians_ms": [p["median_ms"] for p in rs],
                          "mean_of_run_medians_ms": statistics.mean(kept[arm]) if kept[arm] else None,
                          "median_iqr_ms": statistics.median(p["iqr_ms"] for p in rs),
                          "sm_clock_mhz": statistics.median([p["sm_clock_mhz"] for p in rs if p["sm_clock_mhz"]] or [0]),
                          "max_temp_c": max((p["max_temp_c"] or 0) for p in rs),
                          "sw_power_cap_frac": statistics.mean(p["sw_power_cap_frac"] for p in rs)}
    aa = stats.noise_floor(kept["base"], kept["aa"])
    s["aa"] = aa
    floor = aa["noise_floor_pct"]
    s["decisions"] = {arm: stats.compare(kept["base"], kept[arm], floor, a.threshold)
                      for arm in arms if arm not in ("base", "aa")}
    s["sigma_run_pct"] = 100 * statistics.stdev(kept["base"]) / statistics.mean(kept["base"])
    s["mde_pct"] = {"n_runs": len(kept["base"]), "at_n": stats.mde_pct(kept["base"]),
                    "at_10": stats.mde_pct(kept["base"], 10)}
    # Step 5: what three runs per arm could have told you (the first three runs of each arm, same statistic)
    if "fused" in kept:
        b3, f3 = kept["base"][:3], kept["fused"][:3]
        s["three_runs"] = {"change_pct": stats.change_pct(b3, f3), "perm_p": stats.permutation_p(b3, f3),
                           "p_floor": stats.p_floor(3, 3)}
    tel_all = [t for t in tel]
    reasons = {}
    for t in tel_all:
        reasons[t["active"]] = reasons.get(t["active"], 0) + 1
    s["telemetry"] = {"samples": len(tel_all), "clocks_event_reasons_active": reasons}
    s["roofline"] = json.loads((out / "step6_roofline.json").read_text().strip().splitlines()[-1])
    s["per_run"] = per_run
    (out / "summary.json").write_text(json.dumps(s, indent=2))
    report(out, s)
    print(f"wrote {out / 'summary.json'} and {out / 'report.md'}")
    return 0


def report(out: Path, s: dict) -> None:
    n = s["step1_naive"]
    L = [f"# Ch 6 hands-on: benchmark it properly — `{out.name}`", "",
         "Every number is `[MEASURED]` on the machine in `environment.json` unless labelled otherwise; the step is named.", "",
         "## Step 1 — four ways to time one BF16 GEMM (n = 4096)", "",
         "| Method | Time (ms) | Implied TFLOP/s |", "|---|---|---|",
         f"| A: host timer, no synchronize | {n['A_nosync_ms']:.3f} | {n['A_tflops']:.1f} |",
         f"| B: one cold call, synchronized | {n['B_cold_single_ms']:.3f} | {n['B_tflops']:.1f} |",
         f"| C: mean of 20 incl. the first | {n['C_mean_with_first_ms']:.3f} | {n['C_tflops']:.1f} |",
         f"| D: CUDA events, warm-up dropped, median of 50 | {n['D_events_median_ms']:.3f} | {n['D_tflops']:.1f} |", "",
         f"All `[MEASURED, step 1]`. Vendor-class BF16 dense peak at the {n['clocks_max_sm_mhz']:.0f} MHz maximum clock: "
         f"{n['bf16_peak_tflops_at_max_clock']:.1f} TFLOP/s `[MODELED]`.", "",
         "## Step 2 — warm-up", "",
         f"First iteration / steady median, median over {s['step2_warmup']['runs']} runs: **{s['step2_warmup']['first_over_steady_median']:.2f}×** "
         f"(max {s['step2_warmup']['max']:.2f}×) `[MEASURED, step 2]`.", "",
         "## Steps 3–4 — the protocol: arms, clocks, A/A floor", "",
         "| Arm | What | Runs (kept) | Mean of run medians (ms) | Median IQR within a run (ms) | SM clock (MHz) | Max temp (°C) | sw_power_cap share |",
         "|---|---|---|---|---|---|---|---|"]
    for arm, d in s["arms"].items():
        L.append(f"| {arm} | {d['what']} | {d['runs']} ({d['kept']}) | {d['mean_of_run_medians_ms']:.3f} | {d['median_iqr_ms']:.3f} | "
                 f"{d['sm_clock_mhz']:.0f} | {d['max_temp_c']:.0f} | {100 * d['sw_power_cap_frac']:.0f} % |")
    aa = s["aa"]
    L += ["", f"Excluded runs (pre-registered clock rule): {len(s['excluded_runs'])} {s['excluded_runs'] or ''} `[MEASURED, step 4]`.", "",
          f"A/A (base vs aa): {aa['change_pct']:+.2f} %, band [{aa['band_pct'][0]:+.2f} %, {aa['band_pct'][1]:+.2f} %], "
          f"p = {aa['perm_p']:.3f}: noise floor **{aa['noise_floor_pct']:.2f} %** `[MEASURED, step 4]`. "
          f"σ_run = {s['sigma_run_pct']:.2f} %; MDE ≈ {s['mde_pct']['at_n']:.2f} % at {s['mde_pct']['n_runs']} runs per arm, "
          f"{s['mde_pct']['at_10']:.2f} % at 10 `[MODELED from MEASURED σ_run]`.", "",
          "## Step 5 — decisions (one statistic: difference in arm means of run medians, % of baseline)", "",
          "| Candidate vs base | Change | 95 % bootstrap band | Exact permutation p (floor) | Cliff's δ (runs) | Bar = max(floor, threshold) | Decision |",
          "|---|---|---|---|---|---|---|"]
    for arm, c in s["decisions"].items():
        L.append(f"| {s['arms'][arm]['what']} | {c['change_pct']:+.2f} % | [{c['band_pct'][0]:+.2f} %, {c['band_pct'][1]:+.2f} %] | "
                 f"{c['perm_p']:.4f} ({c['p_floor']:.4f}) | {c['cliffs_delta_runs']:+.2f} | {c['decision_bar_pct']:.2f} % | **{c['decision']}** |")
    if "three_runs" in s:
        t = s["three_runs"]
        L += ["", f"With only the first three runs per arm, the fused comparison gives {t['change_pct']:+.2f} % and p = {t['perm_p']:.3f}: "
              f"the floor for 3 + 3 runs is {t['p_floor']:.2f}, so three runs can never reach p < 0.05 `[MEASURED, step 5]`."]
    r = s["roofline"]
    L += ["", "## Step 6 — empirical roofline", "",
          f"- Copy (256 MiB, read + write): **{r['measured_copy_gbs']:.0f} GB/s** against a {r['spec_dram_gbs'] or float('nan'):.0f} GB/s "
          f"bus-width × data-rate spec `[MEASURED, step 6]` (spec `[MODELED]`).",
          f"- Square BF16 GEMM: n = 4096 {r['square_gemm']['4096']['tflops']:.1f}, n = 8192 {r['square_gemm']['8192']['tflops']:.1f} TFLOP/s "
          f"against {r['spec_bf16_tflops_at_max_clock'] or float('nan'):.1f} at the maximum clock; SM clock right after: "
          f"{r['sm_clock_after_gemm_mhz']:.0f} MHz `[MEASURED, step 6]`.",
          (f"- Sustained n = 8192 GEMM for {r['square_gemm']['8192']['sustained']['seconds']:.1f} s: **{r['sustained_gemm_tflops']:.1f} TFLOP/s** at a median "
           f"SM clock of **{r['sustained_gemm_sm_clock_mhz']:.0f} MHz** and {r['sustained_gemm_power_w']:.0f} W `[MEASURED, step 6]`. The BF16 peak at that clock is "
           f"{r['bf16_tflops_at_sustained_clock']:.1f} TFLOP/s `[MODELED]`, so the GEMM is at "
           f"{100 * r['sustained_gemm_tflops'] / r['bf16_tflops_at_sustained_clock']:.0f} % of its clock-adjusted peak and "
           f"{100 * r['sustained_gemm_tflops'] / r['spec_bf16_tflops_at_max_clock']:.0f} % of the maximum-clock figure."
           if r.get("bf16_tflops_at_sustained_clock") else "- Sustained GEMM clock not recorded."),
          f"- Measured ridge point: {r['measured_ridge_flop_per_byte']:.0f} FLOP/B `[MEASURED, step 6]`.", "",
          "| K | AI (FLOP/B) | Time (ms) | TFLOP/s | GB/s | Bound | % of attainable |", "|---|---|---|---|---|---|---|"]
    for x in r["sweep"]:
        L.append(f"| {x['K']} | {x['ai_flop_per_byte']:.1f} | {x['ms']:.3f} | {x['tflops']:.2f} | {x['gbs']:.0f} | {x['bound']} | {x['pct_of_attainable']:.0f} % |")
    L += ["", f"Telemetry: {s['telemetry']['samples']} samples; clock-event reasons seen: {s['telemetry']['clocks_event_reasons_active']} `[MEASURED]`.", ""]
    (out / "report.md").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    sys.exit(main())
