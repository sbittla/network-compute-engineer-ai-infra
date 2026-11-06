#!/usr/bin/env python3
"""Check a Ch 4 hands-on evidence bundle:  python check.py results/<run-id>

PASS only if the bundle is complete and physically sensible: the baseline synchronizes inside the step and
the fixed step does not; removing the syncs makes the step faster (permutation test over separate-process runs); CUDA Graphs cut launches to about one per
step and the baseline cannot be captured; and (when Nsight Systems was installed) the timeline shows the
host-sync gaps in the baseline and not in the fixed step, over step windows that cover the GPU work.
Standard library only. Exit 0 = all PASS.
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

REQUIRED = ["environment.json", "summary.json", "report.md", "step1_baseline_time.json", "step1_gpu_util.csv",
            "step6b_launchbound_runs.jsonl",
            "step2_profile_baseline.json", "step2_profile_fixed.json", "step2_profile_graphed.json",
            "step4_syncdebug.txt", "step5_runs.jsonl", "step6_capture_baseline.json"]
results: list[tuple[bool, str]] = []


def check(ok: bool, what: str, why: str = "") -> None:
    results.append((bool(ok), what))
    print(f"{'PASS' if ok else 'FAIL'}  {what}" + ("" if ok or not why else f"  — {why}"))


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
    check(bool(env.get("gpu")) and env.get("captured_at"), "environment.json names the GPU and the capture time")
    check("[MEASURED" in (d / "report.md").read_text(), "report.md labels its numbers [MEASURED]")
    s = json.loads((d / "summary.json").read_text())

    # Step 1
    b1 = s["step1"]["baseline"]
    check(b1.get("median_ms", 0) > 0 and b1.get("steps", 0) >= 50, "step 1: baseline timed over >= 50 steps")
    u = s["step1"]["gpu_util"]
    check(u["samples"] >= 5 and (u["median_pct_while_running"] or 0) <= 100, "step 1: GPU-Util sampled while the job ran",
          f"{u}")

    # Step 2
    p = s["step2_profiler"]
    pb, pf, pg = p["baseline"], p["fixed"], p["graphed"]
    check(pb["syncs_per_step"] >= 1, "step 2: the baseline synchronizes inside the step",
          f"{pb['syncs_per_step']} synchronize calls per step")
    # (_local_scalar_dense is not checked: non-capturable AdamW reads its CPU-side step counters with .item(),
    # which is a host-memory read, not a GPU sync. Synchronize calls are the ground truth.)
    check(pf["syncs_per_step"] == 0 and pf["nonzero_per_step"] == 0 and pf.get("is_nonzero_per_step", 0) == 0,
          "step 2: the fixed step body has no synchronize call, nonzero or GPU-value branch", f"{pf}")
    check(pb["nonzero_per_step"] >= 1 and pb.get("is_nonzero_per_step", 0) >= 1,
          "step 2: the baseline's syncs come from boolean indexing (nonzero) and a branch on a GPU value (is_nonzero)",
          f"nonzero {pb['nonzero_per_step']}, is_nonzero {pb.get('is_nonzero_per_step')}")
    check(pg["graph_launches_per_step"] >= 1 and pg["launches_per_step"] <= max(5, pf["launches_per_step"] / 10),
          "step 2: CUDA Graphs replace hundreds of launches with about one",
          f"fixed {pf['launches_per_step']} vs graphed {pg['launches_per_step']} launches per step")

    # Step 4
    sd = s["step4_syncdebug"]
    src = " ".join(sd["source"].values())
    check(sd["warnings"] >= 1 and "[mask]" in src, "step 4: sync debug mode points at the boolean-mask line",
          f"flagged lines: {sd['source']}")

    # Step 5: recompute from the raw runs
    runs = [json.loads(x) for x in (d / "step5_runs.jsonl").read_text().splitlines() if x.strip()]
    arms: dict[str, list[float]] = {}
    for r in runs:
        arms.setdefault(r["variant"], []).append(r["median_ms"])
    check(set(arms) == {"baseline", "fixed", "graphed"} and min(len(v) for v in arms.values()) >= 3,
          "step 5: every variant has >= 3 separate-process runs", f"{ {k: len(v) for k, v in arms.items()} }")
    if set(arms) == {"baseline", "fixed", "graphed"}:
        for v, m in arms.items():
            same = abs(statistics.mean(m) - s["step5_ab"]["arms"][v]["mean_of_run_medians_ms"]) < 1e-6
            check(same, f"step 5: summary matches the raw runs ({v})")
        mb, mf, mg = (statistics.mean(arms[v]) for v in ("baseline", "fixed", "graphed"))
        p_fix = s["step5_ab"]["fixed_vs_baseline"]["perm_p"]
        check(mf < mb and statistics.median(arms["fixed"]) < statistics.median(arms["baseline"]) and p_fix < 0.05,
              "step 5: removing the host syncs makes the step faster (exact permutation p < 0.05)",
              f"baseline runs {arms['baseline']}, fixed runs {arms['fixed']}, p = {p_fix:.4f}")
        check(mg <= 1.02 * mf, "step 5: the graphed step is not slower than the fixed step",
              f"graphed {mg:.2f} ms vs fixed {mf:.2f} ms")
        for v, m in arms.items():
            check(all(0.1 < x < 10_000 for x in m), f"step 5: step times are physically plausible ({v})")

    # Step 6
    cap = s["step6_capture_baseline"] or {}
    check(cap.get("capture_succeeded") is False and cap.get("error"),
          "step 6: capturing the baseline (with host syncs) fails", f"{cap}")

    lb = s.get("step6b_launchbound")
    check(bool(lb), "step 6b: fixed and graphed timed in the launch-bound regime", "step6b_launchbound missing from summary.json")
    if lb:
        check(max(lb["graphed_run_medians_ms"]) < min(lb["fixed_run_medians_ms"]) and lb["speedup"] >= 1.15,
              "step 6b: where the step is launch-bound, the graph is faster in every run (>= 1.15x)",
              f"fixed {lb['fixed_run_medians_ms']}, graphed {lb['graphed_run_medians_ms']}")

    # Nsight Systems
    if s.get("nsys_installed"):
        n = s["nsys"]
        if not all(n.get(v) for v in ("baseline", "fixed", "graphed")):
            check(False, "nsys: timelines for all three variants", "a gap analysis is missing")
        else:
            nb, nf, ng = n["baseline"], n["fixed"], n["graphed"]
            check(nb["host_sync_gaps"] >= 1 and nb["sync_calls_per_step"] > nf["sync_calls_per_step"],
                  "nsys: the baseline timeline has host-sync gaps and more synchronize calls",
                  f"baseline {nb['host_sync_gaps']} gaps / {nb['sync_calls_per_step']} syncs; fixed {nf['sync_calls_per_step']} syncs")
            check(nf["host_sync_gaps"] < nb["host_sync_gaps"], "nsys: the fix removes the host-sync gaps",
                  f"baseline {nb['host_sync_gaps']}, fixed {nf['host_sync_gaps']}")
            check(nf["busy_frac"] > nb["busy_frac"], "nsys: the GPU is busy a larger fraction of the fixed step",
                  f"baseline {nb['busy_frac']:.3f}, fixed {nf['busy_frac']:.3f}")
            for v in ("baseline", "fixed", "graphed"):
                w, m = n[v]["window_ms"], s["step5_ab"]["arms"][v]["median_of_run_medians_ms"]
                check(w >= 0.9 * m, f"nsys: the {v} step window covers the step (>= 90 % of the timed median)",
                      f"window {w:.2f} ms vs median {m:.2f} ms")
                check(0 < n[v]["busy_frac"] <= 1.0, f"nsys: busy fraction in (0, 1] ({v})")
    else:
        print("SKIP  nsys steps (Nsight Systems not installed when the bundle was made)")

    bad = sum(1 for ok, _ in results if not ok)
    print(f"\n{len(results) - bad}/{len(results)} checks passed")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
