#!/usr/bin/env python3
"""Check a Ch 22 hands-on evidence bundle:  python check.py results/<run-id>

PASS only if the bundle is complete and physically sensible: each injected bottleneck slowed the job, the
evidence named the injected cause (and only it), every fix is validated by an interleaved A/B with an exact
permutation test recomputed here from the raw runs, the fixed job is back near the healthy step time, and the
layer evidence agrees with the mechanism (the delayed veth's ping, the hog on the job's CPUs, the sync count).
Standard library only. Exit 0 = all PASS.
"""
from __future__ import annotations

import itertools
import json
import re
import statistics
import sys
from pathlib import Path

SCEN = {"loader": "dataloader", "cpu": "cpu_contention", "sync": "host_sync", "network": "network"}
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
        tot += 1
        hits += abs(sb / len(b) - (sum(pooled) - sb) / len(a)) >= obs - 1e-12
    return hits / tot


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    d = Path(sys.argv[1])
    if not d.is_dir():
        print(f"FAIL  bundle directory {d} does not exist")
        return 1
    need = ["environment.json", "summary.json", "report.md", "calibration.json", "calibration_gpu_only.json",
            "evidence_healthy.json", "healthy_runs.jsonl", "net_healthy_status.txt", "net_delay_status_before.txt",
            "cpu_ps_snapshot.txt", "evidence_sync.stderr"]
    need += [f"{p}_{k}.{e}" for k in SCEN for p, e in (("evidence", "json"), ("diagnosis", "json"), ("ab", "jsonl"))]
    missing = [f for f in need if not (d / f).exists()]
    check(not missing, "bundle complete", f"missing: {', '.join(missing)}")
    if missing:
        return 1
    try:
        checks(d)
    except Exception as e:  # noqa: BLE001 - a malformed bundle must give a useful line, not a traceback
        check(False, "bundle readable", f"{type(e).__name__}: {e}")
    bad = sum(1 for r in results if not r)
    print(f"\n{len(results) - bad}/{len(results)} checks passed")
    return 0 if bad == 0 else 1


def checks(d: Path) -> None:
    env = json.loads((d / "environment.json").read_text())
    check(env.get("gpu") and env.get("captured_at"), "environment.json names the GPU and the time")
    check("[MEASURED" in (d / "report.md").read_text(), "report.md labels its numbers [MEASURED]")
    s = json.loads((d / "summary.json").read_text())
    healthy = s["healthy"]
    h = healthy["evidence"]
    cal = s["calibration"]
    check(h["data_wait_share"] < 0.15 and (h.get("profile_syncs_per_step") or 0) < 1,
          "healthy: the GPU is not waiting for data and the step has no host sync (< 1 synchronize per step)",
          f"data wait {h['data_wait_share']:.2f}, syncs {h.get('profile_syncs_per_step')}")
    check(healthy["mean_step_ms"] <= 1.35 * cal["gpu_only_step_ms"],
          "healthy: the step is close to the GPU-only step (the pipeline keeps up)",
          f"{healthy['mean_step_ms']:.1f} vs GPU-only {cal['gpu_only_step_ms']:.1f} ms")

    for k, want in SCEN.items():
        sc = s["scenarios"][k]
        dg = json.loads((d / f"diagnosis_{k}.json").read_text())
        check(dg["verdict"] == want, f"{k}: the evidence names the injected bottleneck ({want})",
              f"verdict {dg['verdict']}: {dg['why']}")
        check(sc["slowdown_vs_healthy"] >= 1.10, f"{k}: the injected bottleneck slows the job by >= 10 %",
              f"{sc['slowdown_vs_healthy']:.2f}x")
        rows = [json.loads(x) for x in (d / f"ab_{k}.jsonl").read_text().splitlines() if x.strip()]
        bad = [r["step_ms"] for r in rows if r["arm"] == "bad"]
        fixed = [r["step_ms"] for r in rows if r["arm"] == "fixed"]
        check(len(bad) >= 5 and len(fixed) >= 5, f"{k}: A/B has >= 5 separate-process runs per arm",
              f"{len(bad)}/{len(fixed)}")
        arms = [r["arm"] for r in rows]
        longest = max(len(list(g)) for _, g in itertools.groupby(arms))
        check(longest <= 2, f"{k}: A/B runs interleaved", f"longest block {longest}")
        if len(bad) >= 2 and len(fixed) >= 2:
            pt = 100 * (statistics.mean(fixed) - statistics.mean(bad)) / statistics.mean(bad)
            p = perm_p(bad, fixed)
            check(abs(pt - sc["ab"]["change_pct"]) < 1e-6 and abs(p - sc["ab"]["perm_p"]) < 1e-9,
                  f"{k}: A/B statistic and exact p recomputed from the raw runs")
            check(pt <= -s["threshold_pct"] and p < 0.05 and sc["ab"]["decision"] == "improvement",
                  f"{k}: the fix is an improvement beyond the {s['threshold_pct']:.0f} % threshold with p < 0.05",
                  f"change {pt:+.1f} %, p {p:.4f}")
            check(statistics.mean(fixed) <= 1.25 * healthy["mean_step_ms"], f"{k}: after the fix the job is within 25 % of healthy",
                  f"{statistics.mean(fixed):.1f} vs healthy {healthy['mean_step_ms']:.1f} ms")
        check(all(0.5 < x < 20_000 for x in bad + fixed), f"{k}: step times physically plausible")

    # layer evidence agrees with the mechanism
    e = s["scenarios"]
    check(e["loader"]["evidence"]["loader_pids"] == [e["loader"]["evidence"]["pid"]],
          "loader: the batches were decoded by the training process itself")
    check(e["cpu"]["evidence"]["decode_runqueue_share"] > 3 * max(h["decode_runqueue_share"], 0.01),
          "cpu: decode threads waited for a CPU far more than when healthy",
          f"{e['cpu']['evidence']['decode_runqueue_share']:.2f} vs {h['decode_runqueue_share']:.2f}")
    check(e["cpu"].get("hog_processes_seen", 0) >= 1, "cpu: the competing process is visible in the ps snapshot")
    check((e["sync"]["evidence"]["profile_syncs_per_step"] or 0) >= 4 and (e["sync"]["evidence"].get("sync_debug_warnings") or 0) >= 1,
          "sync: torch.profiler counts synchronize calls inside the step and sync-debug mode flags them")
    rtt, delay = e["network"].get("ping_avg_ms"), cal["netem_delay_ms"]
    check(rtt is not None and 0.9 * delay <= rtt <= 1.5 * delay + 5, "network: ping over the veth shows the netem delay",
          f"ping {rtt} ms vs delay {delay} ms")
    check(e["network"]["evidence"]["fetch_wait_ms_median"] >= 0.9 * delay,
          "network: each fetch waited at least the added delay", f"{e['network']['evidence']['fetch_wait_ms_median']:.1f} ms")
    hp = healthy.get("ping_avg_ms")
    check(hp is not None and hp < 5, "network: the healthy veth has sub-5 ms RTT", f"{hp}")


if __name__ == "__main__":
    sys.exit(main())
