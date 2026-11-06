#!/usr/bin/env python3
"""Ch 22 hands-on: summary.json and report.md from the raw outputs in results/<run-id>/ (standard library only)."""
from __future__ import annotations

import json
import re
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import abstats  # noqa: E402

SCENARIOS = {"loader": ("Dataloader stall", "decode moved into the training process (num_workers=0)", "num_workers=4"),
             "cpu": ("CPU contention", "8 ch22-hog busy loops pinned with taskset to the job's CPUs",
                     "re-pin the job to a disjoint CPU set"),
             "sync": ("Hidden host sync", "a per-block activation statistic copied to the host (.cpu() + numpy) and loss.item() every step",
                      "remove the per-block host statistic; log the loss every 20 steps"),
             "network": ("Network delay on the data fetch", "netem delay on the data server's veth (ch22-d0)",
                         "4 fetches in flight per worker (prefetch)")}
THRESHOLD = 5.0   # % practical threshold for "the fix matters"; there is no A/A arm, so the bar is the threshold


def last_json(p: Path):
    return json.loads(p.read_text().strip().splitlines()[-1])


def main() -> int:
    out = Path(sys.argv[1])
    s: dict = {"lab": "ch22-handson", "run_id": out.name, "threshold_pct": THRESHOLD}
    s["calibration"] = json.loads((out / "calibration.json").read_text())
    healthy = last_json(out / "evidence_healthy.json")
    hr = [json.loads(x) for x in (out / "healthy_runs.jsonl").read_text().splitlines() if x.strip()]
    s["healthy"] = {"evidence": healthy, "run_step_ms": [r["step_ms"] for r in hr],
                    "mean_step_ms": statistics.mean(r["step_ms"] for r in hr)}
    ping = re.search(r"= ([\d.]+)/([\d.]+)/([\d.]+)", (out / "net_healthy_status.txt").read_text())
    s["healthy"]["ping_avg_ms"] = float(ping.group(2)) if ping else None
    s["scenarios"] = {}
    for key, (title, inject, fix) in SCENARIOS.items():
        ev = last_json(out / f"evidence_{key}.json")
        dg = last_json(out / f"diagnosis_{key}.json")
        rows = [json.loads(x) for x in (out / f"ab_{key}.jsonl").read_text().splitlines() if x.strip()]
        bad = [r["step_ms"] for r in rows if r["arm"] == "bad"]
        fixed = [r["step_ms"] for r in rows if r["arm"] == "fixed"]
        cmp = abstats.compare(bad, fixed, 0.0, THRESHOLD)
        s["scenarios"][key] = {
            "title": title, "injected": inject, "fix": fix, "expected_verdict": "dataloader" if key == "loader" else
            {"cpu": "cpu_contention", "sync": "host_sync", "network": "network"}[key],
            "verdict": dg["verdict"], "why": dg["why"], "slowdown_vs_healthy": dg["slowdown"],
            "evidence": {k: ev.get(k) for k in ("step_ms", "data_wait_share", "data_block_share", "fetch_wait_ms_median", "decode_ms_median",
                                                 "decode_cpu_ms_median", "decode_runqueue_share", "main_cpu_share",
                                                 "main_runqueue_share", "gpu_util_median", "profile_syncs_per_step",
                                                 "profile_item_per_step", "sync_debug_warnings", "loader_pids", "pid")},
            "ab": {"bad_step_ms": bad, "fixed_step_ms": fixed, "bad_mean_ms": statistics.mean(bad),
                   "fixed_mean_ms": statistics.mean(fixed), **cmp,
                   "fixed_vs_healthy_pct": 100 * (statistics.mean(fixed) / s["healthy"]["mean_step_ms"] - 1)}}
    st = (out / "net_delay_status_before.txt").read_text() if (out / "net_delay_status_before.txt").exists() else ""
    ping = re.search(r"= ([\d.]+)/([\d.]+)/([\d.]+)", st)
    s["scenarios"]["network"]["ping_avg_ms"] = float(ping.group(2)) if ping else None
    snap = (out / "cpu_ps_snapshot.txt").read_text() if (out / "cpu_ps_snapshot.txt").exists() else ""
    s["scenarios"]["cpu"]["hog_processes_seen"] = len(re.findall(r"ch22-hog", snap.split("affinity")[0]))
    (out / "summary.json").write_text(json.dumps(s, indent=2))

    c = s["calibration"]
    L = [f"# Ch 22 hands-on: find the bottleneck — `{out.name}`", "",
         "Every number is `[MEASURED]` on the machine in `environment.json` (step named) unless labelled otherwise.", "",
         "## Calibration", "",
         f"GPU-only step {c['gpu_only_step_ms']:.1f} ms; decode {c['decode_ms_expected']:.1f} ms per batch on one CPU "
         f"({c['decode_rounds']} rounds); netem delay {c['netem_delay_ms']} ms `[MEASURED, calibration]` "
         "(sizes chosen by rule: decode ≈ 2 × GPU step, delay ≈ 6 × GPU step).", "",
         f"Healthy: {len(hr)} runs, mean step **{s['healthy']['mean_step_ms']:.1f} ms**; data-wait share "
         f"{100 * healthy['data_wait_share']:.0f} %; GPU-Util median {healthy['gpu_util_median']} %; ping over the veth "
         f"{s['healthy']['ping_avg_ms']} ms `[MEASURED, healthy]`.", "",
         "## Diagnoses (rules in diagnose.py, written before the runs)", "",
         "| Scenario | Injected | Step vs healthy | Data-wait share | Network wait / batch (ms) | Decode run-queue share | Syncs / step | GPU-Util | Verdict | Expected |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for k, d in s["scenarios"].items():
        e = d["evidence"]
        L.append(f"| {d['title']} | {d['injected']} | {d['slowdown_vs_healthy']:.2f}× | {100 * e['data_wait_share']:.0f} % | "
                 f"{e['fetch_wait_ms_median']:.1f} | {100 * e['decode_runqueue_share']:.0f} % | {e['profile_syncs_per_step']} | "
                 f"{e['gpu_util_median']} % | **{d['verdict']}** | {d['expected_verdict']} |")
    L += ["", "All `[MEASURED, evidence run of each scenario]`.", "",
          "## Fixes validated by A/B (interleaved, separate processes; primary statistic = difference in arm means of run step times)", "",
          "| Scenario | Fix | Before (ms) | After (ms) | Change | 95 % band | Exact p (floor) | Decision | After vs healthy |",
          "|---|---|---|---|---|---|---|---|---|"]
    for k, d in s["scenarios"].items():
        a = d["ab"]
        L.append(f"| {d['title']} | {d['fix']} | {a['bad_mean_ms']:.1f} | {a['fixed_mean_ms']:.1f} | {a['change_pct']:+.1f} % | "
                 f"[{a['band_pct'][0]:+.1f} %, {a['band_pct'][1]:+.1f} %] | {a['perm_p']:.4f} ({a['p_floor']:.4f}) | "
                 f"**{a['decision']}** | {a['fixed_vs_healthy_pct']:+.1f} % |")
    L += ["", f"All `[MEASURED, A/B of each scenario]`; practical threshold {THRESHOLD:.0f} %.", "",
          f"Network scenario ping over the delayed veth: {s['scenarios']['network']['ping_avg_ms']} ms `[MEASURED, scenario 4]`.", ""]
    (out / "report.md").write_text("\n".join(L) + "\n")
    print(f"wrote {out / 'summary.json'} and {out / 'report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
