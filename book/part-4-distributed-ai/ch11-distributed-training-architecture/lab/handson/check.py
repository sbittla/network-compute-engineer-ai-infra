#!/usr/bin/env python3
"""Check a Chapter 11 hands-on results directory for completeness and physical sense.

    python check.py results/<run-id>

Prints one PASS/FAIL line per check and exits 0 only if all pass. It tests what any correct run on any
machine must show (communication costs time, no_sync amortizes it, a killed rank fails the job, a hung
rank fails it after the process-group timeout, a restart loses exactly the steps since the last
checkpoint), not the reference machine's absolute numbers. Python standard library only.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

RESULTS: list[tuple[bool, str]] = []


def check(ok: bool, msg: str) -> None:
    RESULTS.append((bool(ok), msg))
    print(f"{'PASS' if ok else 'FAIL'}  {msg}")


def num(x) -> bool:
    return isinstance(x, (int, float)) and not (isinstance(x, float) and math.isnan(x))


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    d = Path(sys.argv[1])
    for name in ["environment.json", "summary.json", "report.md", "raw/exit_codes.tsv"]:
        check((d / name).is_file(), f"bundle has {name}")
    if not (d / "summary.json").is_file():
        print("FAIL  cannot continue without summary.json (run analyze.py)")
        return 1
    try:
        S = json.loads((d / "summary.json").read_text())
        env = json.loads((d / "environment.json").read_text()) if (d / "environment.json").is_file() else {}
    except json.JSONDecodeError as e:
        print(f"FAIL  summary.json or environment.json is not valid JSON: {e}")
        return 1
    check(bool(env.get("kernel")) and bool(env.get("captured_at")), "environment.json records kernel and time")
    report = (d / "report.md").read_text() if (d / "report.md").is_file() else ""
    check(report.count("[MEASURED]") >= 5, "report.md labels its numbers [MEASURED]")
    raw = sorted(p.name for p in (d / "raw").glob("*.jsonl")) if (d / "raw").is_dir() else []
    check(len(raw) >= 20, f"raw event logs present ({len(raw)} .jsonl files, need >= 20)")

    codes = S.get("exit_codes", {})
    expected = ([f"{p}_n{n}" for n in (1, 2, 4, 8) for p in ("weak", "weak_nocomm", "strong")]
                + [f"bucket_{b}" for b in (1, 5, 25, 100)] + [f"accum_{k}" for k in (1, 2, 4, 8)]
                + ["fault_kill_norestart", "fault_kill", "fault_hang_t10", "fault_hang_t20", "ckpt_base"]
                + [f"ckpt_K{k}" for k in (2, 4, 8, 16, 32)])
    missing = [x for x in expected if x not in codes or not (d / "raw" / f"{x}.jsonl").is_file()
               or not (d / "raw" / f"{x}.log").is_file()]
    check(not missing, f"every experiment has its exit code, raw/<name>.jsonl and raw/<name>.log "
                       f"(missing: {missing or 'none'})")
    bad = [k for k, v in codes.items() if k != "fault_kill_norestart" and v != 0]
    check(len(codes) >= 25 and not bad, f"every launch exited 0 except the deliberate no-restart kill (bad: {bad or 'none'})")

    # ---- Step 1
    try:
        rows = {r["n"]: r for r in S["step1_scaling"]["rows"]}
        ok = all(num(rows[n]["weak_step_s"]) and rows[n]["weak_step_s"] > 0 for n in (1, 2, 4, 8))
        check(ok, "step 1: step times measured for 1, 2, 4 and 8 ranks")
        check(rows[8]["weak_step_s"] > rows[1]["weak_step_s"] * 1.05,
              f"step 1: 8-rank weak-scaling step is slower than 1 rank (gradient all-reduce costs time): "
              f"{rows[8]['weak_step_s']:.3f} s vs {rows[1]['weak_step_s']:.3f} s")
        check(rows[8]["exposed_comm_s"] > 2 * max(rows[1]["exposed_comm_s"], 0.0),
              f"step 1: 8 ranks expose > 2x the one-rank DDP overhead ({rows[8]['exposed_comm_s']:.4f} s vs "
              f"{rows[1]['exposed_comm_s']:.4f} s; one rank still copies gradients into buckets)")
        check(all(rows[n]["exposed_comm_s"] > 0 for n in (2, 4, 8)),
              "step 1: exposed communication > 0 for 2, 4, 8 ranks")
        check(rows[8]["compute_only_step_s"] < 3.0 * rows[1]["compute_only_step_s"],
              "step 1: compute-only step stays within 3x from 1 to 8 ranks (each rank has its own core; "
              "they share memory bandwidth)")
        check(all(0 < rows[n]["strong_efficiency"] <= 1.15 for n in (2, 4, 8)),
              "step 1: strong-scaling efficiency is in (0, 1.15]")
        check(all(r["replicas_identical"] for r in rows.values()),
              "step 1: every replica ends with identical parameters (DDP keeps replicas in sync)")
        rss = rows[8]["peak_rss_mib_total"]
        check(num(rss) and 0 < rss < 7 * 1024, f"step 1: 8 ranks fit in 7 GiB (peak RSS sum {rss} MiB)")
    except (KeyError, TypeError) as e:
        check(False, f"step 1: summary incomplete ({e})")

    # ---- Step 2
    try:
        b = {r["bucket_cap_mb"]: r for r in S["step2_buckets"]["rows"]}
        check(all(num(b[k]["step_s"]) for k in (1, 5, 25, 100)), "step 2: step time for bucket_cap_mb 1, 5, 25, 100")
        nb = [b[k]["buckets"] for k in (1, 5, 25, 100)]
        check(all(isinstance(x, int) for x in nb) and nb[0] > nb[1] >= nb[2] >= nb[3] and nb[3] == 1,
              f"step 2: bucket count falls as the cap grows and a 100 MB cap gives one bucket ({nb})")
    except (KeyError, TypeError) as e:
        check(False, f"step 2: summary incomplete ({e})")

    # ---- Step 3
    try:
        a = {r["accum"]: r for r in S["step3_accum"]["rows"]}
        check(a[8]["samples_per_s"] > 1.1 * a[1]["samples_per_s"],
              f"step 3: no_sync accumulation of 8 micro-batches raises throughput "
              f"({a[1]['samples_per_s']:.0f} -> {a[8]['samples_per_s']:.0f} samples/s)")
        check(a[8]["comm_share"] < a[1]["comm_share"],
              "step 3: the communication share of a step falls as micro-batches per all-reduce grow")
    except (KeyError, TypeError) as e:
        check(False, f"step 3: summary incomplete ({e})")

    # ---- Step 4
    g = S.get("step4_gpu", {})
    if g.get("ran"):
        check(codes.get("gpu_n1") == 0 and num(g.get("step_s")) and g["step_s"] < g["cpu_1rank_step_s"],
              f"step 4: the GPU step ({g.get('step_s')}) is faster than one CPU rank ({g.get('cpu_1rank_step_s')})")
    else:
        check(bool(g.get("reason")), f"step 4: GPU step skipped with a reason ({g.get('reason')})")

    # ---- Step 5
    try:
        f5 = S["step5_faults"]
        nr = f5["fault_kill_norestart"]
        check(nr["exit_code"] not in (0, None) and not nr["completed"],
              f"step 5: killing a rank with --max-restarts=0 fails the job (exit {nr['exit_code']})")
        k = f5["fault_kill"]
        fr = k["faults"][0]
        check(k["completed"] and k["attempts"] == 2, "step 5: with --max-restarts=1 the killed job restarts once and completes")
        check(num(fr.get("detect_s")) and fr["detect_s"] < 10,
              f"step 5: survivors learn of the killed rank within seconds, not the timeout ({fr.get('detect_s')} s)")
        check(fr.get("lost_steps") == (fr["fault_step"] - 1) % 10,
              f"step 5: restart loses exactly the steps since the last checkpoint ({fr.get('lost_steps')})")
        check(k["loss_matches_uninterrupted"] is True, "step 5: resumed run reaches the uninterrupted run's loss at step 40 (relative 1e-5)")
        for name, to in [("fault_hang_t10", 10), ("fault_hang_t20", 20)]:
            h = f5[name]
            hr = h["faults"][0]
            pe = hr.get("peer_error_s")
            check(num(pe) and 0.9 * to <= pe <= 1.5 * to + 2,
                  f"step 5: a hung rank is detected after the {to} s process-group timeout ({pe} s)")
            check(h["completed"] and h["loss_matches_uninterrupted"] is True,
                  f"step 5: {name} recovers from checkpoint to the uninterrupted loss")
    except (KeyError, TypeError, IndexError) as e:
        check(False, f"step 5: summary incomplete ({e})")

    # ---- Step 6
    try:
        s6 = S["step6_ckpt_interval"]
        rows6 = s6["rows"]
        check(len(rows6) >= 4 and all(r["completed"] and r["final_loss_matches"] for r in rows6),
              "step 6: every interval completes and ends at the uninterrupted run's loss (relative 1e-5)")
        check(all(r["failures"] == len(s6["fault_steps"]) for r in rows6), "step 6: every run saw every injected kill")
        check(all(r["lost_steps_measured"] == r["lost_steps_predicted"] for r in rows6),
              "step 6: lost steps per kill equal (s - 1) mod K exactly (lost work = time since last checkpoint)")
        lost = [r["measured_lost_frac"] for r in rows6]
        ck = [r["measured_ckpt_frac"] for r in rows6]
        check(lost[-1] > lost[0] and ck[0] > ck[-1],
              "step 6: longer intervals cost more lost work and less checkpoint overhead")
        check(all(num(r["restart_median_s"]) and r["restart_median_s"] > 0 for r in rows6),
              "step 6: restart time R measured for every interval")
        check(num(s6["tau_opt_steps"]) and 0 < s6["tau_opt_steps"] < 1000, f"step 6: Young/Daly tau_opt computed ({s6.get('tau_opt_steps')})")
    except (KeyError, TypeError, IndexError) as e:
        check(False, f"step 6: summary incomplete ({e})")

    failed = sum(1 for ok, _ in RESULTS if not ok)
    print(f"\n{len(RESULTS) - failed}/{len(RESULTS)} checks passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
