#!/usr/bin/env python3
"""Check a Ch 6 hands-on evidence bundle:  python check.py results/<run-id>

Recomputes the protocol's statistics from the raw runs independently of analyze.py/stats.py and checks that
the bundle is complete, follows the protocol (separate processes, interleaved, warm-up dropped, >= 5 runs per
arm, telemetry for the session) and is physically sensible (no GEMM above the BF16 peak, no copy above the DRAM
spec, the no-synchronize timer reads impossibly fast, the warm-up iteration is slower). Standard library only.
"""
from __future__ import annotations

import itertools
import json
import math
import statistics
import sys
from pathlib import Path

REQUIRED = ["environment.json", "summary.json", "report.md", "step1_naive.json", "runs.jsonl", "telemetry.csv",
            "schedule.txt", "step6_roofline.json"]
results: list[bool] = []


def check(ok, what: str, why: str = "") -> None:
    results.append(bool(ok))
    print(f"{'PASS' if ok else 'FAIL'}  {what}" + ("" if ok or not why else f"  — {why}"))


def perm_p(a, b):
    pooled = a + b
    obs = abs(sum(b) / len(b) - sum(a) / len(a))
    hits = tot = 0
    for idx in itertools.combinations(range(len(pooled)), len(b)):
        sb = sum(pooled[i] for i in idx)
        sa = sum(pooled) - sb
        tot += 1
        hits += abs(sb / len(b) - sa / len(a)) >= obs - 1e-12
    return hits / tot


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    d = Path(sys.argv[1])
    if not d.is_dir():
        print(f"FAIL  bundle directory {d} does not exist")
        return 1
    missing = [f for f in REQUIRED if not (d / f).exists()]
    check(not missing, "bundle complete", f"missing: {', '.join(missing)}")
    if missing:
        return 1
    env = json.loads((d / "environment.json").read_text())
    check(env.get("gpu") and env.get("captured_at"), "environment.json names the GPU and the time")
    check("[MEASURED" in (d / "report.md").read_text(), "report.md labels its numbers [MEASURED]")
    s = json.loads((d / "summary.json").read_text())

    # Step 1
    n = s["step1_naive"]
    peak = n["bf16_peak_tflops_at_max_clock"]
    check(n["D_tflops"] <= 1.05 * peak, "step 1: the protocol's timer gives a GEMM rate below the BF16 peak",
          f"{n['D_tflops']:.1f} vs peak {peak:.1f} TFLOP/s")
    check(n["A_nosync_ms"] < 0.5 * n["D_events_median_ms"], "step 1: the no-synchronize timer reads far too fast",
          f"A {n['A_nosync_ms']:.3f} ms vs D {n['D_events_median_ms']:.3f} ms")
    check(n["B_cold_single_ms"] > n["D_events_median_ms"], "step 1: a single cold call is slower than the steady median")

    # Raw runs: protocol compliance
    runs = [json.loads(x) for x in (d / "runs.jsonl").read_text().splitlines() if x.strip()]
    arms: dict[str, list[dict]] = {}
    for r in runs:
        arms.setdefault(r["arm"], []).append(r)
    check({"base", "aa"} <= set(arms) and len(arms) >= 3, "runs: a baseline, an A/A arm and at least one candidate",
          f"arms {sorted(arms)}")
    check(min(len(v) for v in arms.values()) >= 5, "runs: >= 5 separate-process runs per arm",
          f"{ {k: len(v) for k, v in arms.items()} }")
    check(all(r["warmup"] >= 5 and r["iters"] >= 50 and len(r["ms"]) == r["warmup"] + r["iters"] for r in runs),
          "runs: >= 5 warm-up and >= 50 timed iterations recorded per run")
    order = [r["arm"] for r in sorted(runs, key=lambda r: r["order"])]
    longest = max(len(list(g)) for _, g in itertools.groupby(order))
    check(longest <= 2, "runs: arms interleaved (never more than two consecutive runs of one arm)", f"longest block {longest}")
    starts = [r["t_loop"] for r in sorted(runs, key=lambda r: r["order"])]
    check(all(b > a for a, b in zip(starts, starts[1:])), "runs: one process after another (no overlap)")
    tel_lines = (d / "telemetry.csv").read_text().splitlines()
    span = runs[-1]["t_end"] - runs[0]["t_loop"] if runs else 0
    check(len(tel_lines) - 1 >= 0.5 * span / 0.1, "telemetry: ~10 samples/s for the whole session",
          f"{len(tel_lines) - 1} samples over {span:.0f} s")
    firsts = [r["ms"][0] / statistics.median(r["ms"][r["warmup"]:]) for r in runs]
    check(statistics.median(firsts) > 1.0, "step 2: the first iteration is slower than the steady median",
          f"median ratio {statistics.median(firsts):.2f}")
    check(all(0.05 < x < 10_000 for r in runs for x in r["ms"]), "runs: iteration times physically plausible")

    # Statistics recomputed independently
    excl = {(e["arm"], e["run"]) for e in s["excluded_runs"]}
    med = {a: [statistics.median(r["ms"][r["warmup"]:]) for r in v if (a, r["run"]) not in excl] for a, v in arms.items()}
    for a in arms:
        check(abs(statistics.mean(med[a]) - s["arms"][a]["mean_of_run_medians_ms"]) < 1e-6,
              f"stats: summary's mean of run medians matches the raw runs ({a})")
    base = med["base"]
    aa_pt = 100 * (statistics.mean(med["aa"]) - statistics.mean(base)) / statistics.mean(base)
    check(abs(aa_pt - s["aa"]["change_pct"]) < 1e-6, "stats: A/A point recomputed")
    lo, hi = s["aa"]["band_pct"]
    check(abs(s["aa"]["noise_floor_pct"] - max(abs(aa_pt), abs(lo), abs(hi))) < 1e-9 and lo <= aa_pt <= hi,
          "stats: noise floor = max(|A/A point|, |band bounds|), band contains the point")
    for arm, c in s["decisions"].items():
        pt = 100 * (statistics.mean(med[arm]) - statistics.mean(base)) / statistics.mean(base)
        p = perm_p(base, med[arm])
        floor = 2 / math.comb(len(base) + len(med[arm]), len(med[arm]))
        check(abs(pt - c["change_pct"]) < 1e-6 and abs(p - c["perm_p"]) < 1e-9,
              f"stats: {arm}: point and exact permutation p recomputed", f"{pt:.4f}/{p:.5f} vs {c['change_pct']:.4f}/{c['perm_p']:.5f}")
        check(p >= floor - 1e-12 and c["band_pct"][0] <= pt <= c["band_pct"][1], f"stats: {arm}: p >= its floor, band contains the point")
        bar = max(s["aa"]["noise_floor_pct"], s["threshold_pct"])
        want = ("not_significant" if p >= 0.05 else "real_but_below_threshold" if abs(pt) < bar
                else "improvement" if pt < 0 else "regression")
        check(c["decision"] == want, f"stats: {arm}: decision follows Table 6.6", f"{c['decision']} vs {want}")
    if "three_runs" in s:
        check(s["three_runs"]["perm_p"] >= 0.1 - 1e-12, "stats: three runs per arm cannot reach p < 0.05 (floor 0.1)")

    # Roofline
    r = s["roofline"]
    if r.get("spec_bf16_tflops_at_max_clock"):
        check(r["measured_bf16_roof_tflops"] <= 1.05 * r["spec_bf16_tflops_at_max_clock"],
              "roofline: GEMM rate below the vendor-class BF16 peak")
    if r.get("spec_dram_gbs"):
        check(r["measured_copy_gbs"] <= 1.05 * r["spec_dram_gbs"], "roofline: copy bandwidth below the DRAM spec",
              f"{r['measured_copy_gbs']:.0f} vs {r['spec_dram_gbs']:.0f} GB/s")
    if r.get("bf16_tflops_at_sustained_clock"):
        check(r["sustained_gemm_tflops"] <= 1.05 * r["bf16_tflops_at_sustained_clock"]
              and r["sustained_gemm_sm_clock_mhz"] <= 1.01 * r["clocks_max_sm_mhz"],
              "roofline: sustained GEMM below the BF16 peak at its own measured clock",
              f"{r['sustained_gemm_tflops']:.1f} TFLOP/s at {r['sustained_gemm_sm_clock_mhz']:.0f} MHz "
              f"vs {r['bf16_tflops_at_sustained_clock']:.1f}")
    sw = r["sweep"]
    check(sw[0]["bound"] == "memory" and sw[-1]["bound"] == "compute" and sw[-1]["tflops"] > 5 * sw[0]["tflops"],
          "roofline: thin GEMMs memory-bound, square ones compute-bound, rate rises with intensity")

    bad = results.count(False)
    print(f"\n{len(results) - bad}/{len(results)} checks passed")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
