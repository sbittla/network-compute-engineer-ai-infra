#!/usr/bin/env python3
"""Turn the raw outputs in results/<run-id>/ into summary.json and report.md (standard library only)."""
from __future__ import annotations

import csv
import itertools
import json
import re
import statistics
import sys
from pathlib import Path


def jload(p: Path):
    return json.loads(p.read_text().strip().splitlines()[-1]) if p.exists() else None


def util_stats(p: Path) -> dict:
    vals = []
    if p.exists():
        rows = list(csv.reader(p.open()))
        for r in rows[1:]:
            try:
                vals.append(float(r[1].strip().split()[0]))
            except (ValueError, IndexError):
                pass
    busy = [v for v in vals if v > 0]          # samples while the job's kernels were running
    return {"samples": len(vals), "busy_samples": len(busy),
            "median_pct_while_running": statistics.median(busy) if busy else None}


def perm_p(a: list[float], b: list[float]) -> float:
    """Exact two-sided permutation test on the difference in arm means (Chapter 6, Section 6.7)."""
    pooled = a + b
    obs = abs(statistics.mean(b) - statistics.mean(a))
    hits = total = 0
    for idx in itertools.combinations(range(len(pooled)), len(b)):
        s = set(idx)
        cb = [pooled[i] for i in s]
        ca = [pooled[i] for i in range(len(pooled)) if i not in s]
        total += 1
        hits += abs(statistics.mean(cb) - statistics.mean(ca)) >= obs - 1e-12
    return hits / total


def nsys_summary(out: Path, v: str):
    p = out / f"nsys_{v}_gaps.json"
    if not p.exists():
        return None
    steps = json.loads(p.read_text())["steps"]
    # median over the captured steps, so one step hit by a CPU-contention burst cannot decide the result
    def mean(key):
        return statistics.median(s[key] for s in steps)
    def gap(cause, field):
        return statistics.median(s["gaps_by_cause"].get(cause, {}).get(field, 0) for s in steps)
    return {"steps": len(steps), "window_ms": mean("window_ms"), "busy_ms": mean("busy_ms"), "busy_frac": mean("busy_frac"),
            "kernels_per_step": mean("kernels"), "sync_calls_per_step": mean("sync_calls"),
            "host_sync_gaps": gap("host_sync", "count"), "host_sync_gap_ms": gap("host_sync", "total_us") / 1e3,
            "launch_bound_gaps": gap("launch_bound", "count"), "launch_bound_gap_ms": gap("launch_bound", "total_us") / 1e3,
            "dependency_gaps": gap("dependency", "count"), "dependency_gap_ms": gap("dependency", "total_us") / 1e3}


def main() -> int:
    out = Path(sys.argv[1])
    s: dict = {"lab": "ch04-handson", "run_id": out.name}
    s["step1"] = {"baseline": {k: v for k, v in (jload(out / "step1_baseline_time.json") or {}).items() if k != "step_ms"},
                  "gpu_util": util_stats(out / "step1_gpu_util.csv")}
    s["step2_profiler"] = {v: jload(out / f"step2_profile_{v}.json") for v in ("baseline", "fixed", "graphed")}
    s["nsys_installed"] = not (out / "nsys_skipped.json").exists()
    s["nsys"] = {v: nsys_summary(out, v) for v in ("baseline", "fixed", "graphed")}
    sd = (out / "step4_syncdebug.txt").read_text() if (out / "step4_syncdebug.txt").exists() else ""
    lines = sorted({int(m) for m in re.findall(r"train_step\.py:(\d+)", sd)})
    src = (Path(__file__).resolve().parent / "train_step.py").read_text().splitlines()
    s["step4_syncdebug"] = {"warnings": len(re.findall(r"^WARNING ", sd, flags=re.M)), "train_step_lines": lines,
                            "source": {str(n): src[n - 1].strip() for n in lines if 0 < n <= len(src)}}
    runs = [json.loads(x) for x in (out / "step5_runs.jsonl").read_text().splitlines() if x.strip()]
    arms = {}
    for r in runs:
        arms.setdefault(r["variant"], []).append(r["median_ms"])
    ab = {v: {"run_medians_ms": m, "mean_of_run_medians_ms": statistics.mean(m),
              "median_of_run_medians_ms": statistics.median(m), "runs": len(m)} for v, m in arms.items()}
    def compare(a, b):
        ma, mb = arms[a], arms[b]
        return {"change_pct": 100 * (statistics.mean(mb) - statistics.mean(ma)) / statistics.mean(ma),
                "speedup": statistics.mean(ma) / statistics.mean(mb), "perm_p": perm_p(ma, mb)}
    s["step5_ab"] = {"arms": ab, "fixed_vs_baseline": compare("baseline", "fixed"),
                     "graphed_vs_fixed": compare("fixed", "graphed"), "graphed_vs_baseline": compare("baseline", "graphed")}
    s["step6_capture_baseline"] = jload(out / "step6_capture_baseline.json")
    lb_path = out / "step6b_launchbound_runs.jsonl"
    if lb_path.exists():
        lb = {}
        for x in lb_path.read_text().splitlines():
            if x.strip():
                r = json.loads(x)
                lb.setdefault(r["variant"], []).append(r["median_ms"])
                batch = r.get("batch")
        if {"fixed", "graphed"} <= set(lb):
            mf, mg = statistics.mean(lb["fixed"]), statistics.mean(lb["graphed"])
            s["step6b_launchbound"] = {"batch": batch, "fixed_run_medians_ms": lb["fixed"], "graphed_run_medians_ms": lb["graphed"],
                                       "fixed_mean_ms": mf, "graphed_mean_ms": mg, "change_pct": 100 * (mg - mf) / mf,
                                       "speedup": mf / mg, "perm_p": perm_p(lb["fixed"], lb["graphed"])}
    (out / "summary.json").write_text(json.dumps(s, indent=2))

    b, f, g = (s["step2_profiler"][v] for v in ("baseline", "fixed", "graphed"))
    ab5 = s["step5_ab"]
    L = [f"# Ch 4 hands-on: profile a training step — `{out.name}`", "",
         "Every number below is `[MEASURED]` on the machine in `environment.json`; the step that produced it is named.", "",
         "## Step 1 — the symptom", "",
         f"- Baseline step: median **{s['step1']['baseline'].get('median_ms', float('nan')):.2f} ms** over "
         f"{s['step1']['baseline'].get('steps')} steps `[MEASURED, step 1]`.",
         f"- nvidia-smi GPU-Util while the job ran: median **{s['step1']['gpu_util']['median_pct_while_running']} %** "
         f"({s['step1']['gpu_util']['busy_samples']} samples at 100 ms) `[MEASURED, step 1]`: a duty cycle, not efficiency.", "",
         "## Step 2 — torch.profiler (CPU side)", "",
         "| Variant | Kernel launches / step | Graph launches / step | Synchronize calls / step (step body, excl. end of step) | `_local_scalar_dense` / step | `nonzero` / step | `is_nonzero` / step | GPU (device) events recorded |",
         "|---|---|---|---|---|---|---|---|"]
    for name, d in (("baseline", b), ("fixed", f), ("graphed", g)):
        if d:
            L.append(f"| {name} | {d['launches_per_step']:.0f} | {d['graph_launches_per_step']:.0f} | {d['syncs_per_step']:.0f} | "
                     f"{d['local_scalar_dense_per_step']:.0f} | {d['nonzero_per_step']:.0f} | {d.get('is_nonzero_per_step', 0):.0f} | {d['device_events']} |")
    L += ["", "`_local_scalar_dense` also counts host-memory reads: non-capturable AdamW reads each parameter's CPU-side step "
          "counter with `.item()`, which does not wait for the GPU. The synchronize count is the ground truth.",
          "", "All `[MEASURED, step 2]`. A device-event count of 0 means CUPTI delivered no GPU activity to torch.profiler "
          "on this platform (WSL2); the GPU side comes from Nsight Systems below.", ""]
    L += ["## Steps 3, 5, 6 — Nsight Systems timeline (median over the captured steps per variant)", ""]
    if s["nsys_installed"]:
        L += ["| Variant | Step window (ms) | GPU busy (%) | Kernels / step | Synchronize calls / step | host_sync gaps (n, ms) | launch_bound gaps (n, ms) | dependency gaps (n, ms) |",
              "|---|---|---|---|---|---|---|---|"]
        for v in ("baseline", "fixed", "graphed"):
            n = s["nsys"][v]
            if n:
                L.append(f"| {v} | {n['window_ms']:.2f} | {100 * n['busy_frac']:.1f} | {n['kernels_per_step']:.0f} | "
                         f"{n['sync_calls_per_step']:.0f} | {n['host_sync_gaps']:.1f}, {n['host_sync_gap_ms']:.2f} | "
                         f"{n['launch_bound_gaps']:.1f}, {n['launch_bound_gap_ms']:.2f} | {n['dependency_gaps']:.1f}, {n['dependency_gap_ms']:.2f} |")
        L += ["", "All `[MEASURED, steps 3/5/6]`; gaps ≥ 10 µs inside each `train_step_N` NVTX range, attributed with the Section 4.11 rule by `gaps.py`.", ""]
    else:
        L += ["Nsight Systems was not installed, so the timeline steps were skipped.", ""]
    sd4 = s["step4_syncdebug"]
    L += ["## Step 4 — which lines synchronize", "",
          f"`set_sync_debug_mode(\"warn\")` printed **{sd4['warnings']}** warnings for one step `[MEASURED, step 4]`, at these lines of `train_step.py`:", ""]
    L += [f"- line {k}: `{v}`" for k, v in sd4["source"].items()]
    L += ["", "## Step 5 — the fix, re-measured (separate processes, interleaved)", "",
          "| Variant | Runs | Run medians (ms) | Mean of run medians (ms) |", "|---|---|---|---|"]
    for v in ("baseline", "fixed", "graphed"):
        a = ab5["arms"].get(v)
        if a:
            L.append(f"| {v} | {a['runs']} | {', '.join(f'{x:.2f}' for x in a['run_medians_ms'])} | {a['mean_of_run_medians_ms']:.2f} |")
    for key, label in (("fixed_vs_baseline", "fixed vs baseline"), ("graphed_vs_fixed", "graphed vs fixed"),
                       ("graphed_vs_baseline", "graphed vs baseline")):
        c = ab5[key]
        L.append(f"\n- {label}: **{c['change_pct']:+.1f} %** step time ({c['speedup']:.2f}×), exact permutation p = {c['perm_p']:.3f} `[MEASURED, step 5]`")
    cap = s["step6_capture_baseline"] or {}
    L += ["", "## Step 6 — CUDA Graphs", "",
          f"- Capturing the *baseline* step: {'succeeded (unexpected)' if cap.get('capture_succeeded') else 'failed, as it must'} — `{cap.get('error', '')[:160]}` `[MEASURED, step 6]`.",
          "- The fixed step captures; its timing is the `graphed` row above."]
    lb = s.get("step6b_launchbound")
    if lb:
        L += [f"- Launch-bound regime (`--batch {lb['batch']}`, 4 interleaved runs each): fixed "
              f"{', '.join(f'{x:.2f}' for x in lb['fixed_run_medians_ms'])} ms, graphed "
              f"{', '.join(f'{x:.2f}' for x in lb['graphed_run_medians_ms'])} ms: **{lb['change_pct']:+.1f} %** "
              f"({lb['speedup']:.2f}×), exact permutation p = {lb['perm_p']:.3f} `[MEASURED, step 6b]`."]
    L += [""]
    (out / "report.md").write_text("\n".join(L) + "\n")
    print(f"wrote {out / 'summary.json'} and {out / 'report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
