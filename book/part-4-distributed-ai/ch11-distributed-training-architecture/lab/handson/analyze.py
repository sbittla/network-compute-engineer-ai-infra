#!/usr/bin/env python3
"""Chapter 11 hands-on lab: turn the raw event logs in results/<run-id>/raw/ into summary.json and report.md.

    python analyze.py results/<run-id>

Every number comes from the raw logs written by ch11_ddp.py under torchrun; nothing is typed in.
Model values (ring bytes, Young/Daly, expected lost work) are computed from measured inputs and
labelled [MODELED] in the report.
"""
from __future__ import annotations

import json
import math
import statistics as st
import sys
from pathlib import Path

NS = [1, 2, 4, 8]
BUCKETS = [1, 5, 25, 100]
ACCUM = [1, 2, 4, 8]
KS = [2, 4, 8, 16, 32]
CKPT_STEPS = 192


def events(raw: Path, name: str, kind: str = "") -> list[dict]:
    p = raw / f"{name}{kind}.jsonl"
    if not p.exists():
        return []
    out = []
    for line in p.read_text().splitlines():
        try:
            if line.strip():
                out.append(json.loads(line))
        except json.JSONDecodeError:
            pass          # a line cut short by a SIGKILL; the logger avoids this, but never trust it
    return out


def step_time(ev: list[dict], warmup: int = 5) -> float:
    """Median step seconds of attempt 0 after the warm-up steps."""
    dts = [e["dt"] for e in ev if e["ev"] == "step" and e["attempt"] == 0 and e["step"] > warmup]
    return st.median(dts) if dts else float("nan")


def done(ev: list[dict]) -> dict:
    d = [e for e in ev if e["ev"] == "done"]
    return d[-1] if d else {}


def start(ev: list[dict]) -> dict:
    s = [e for e in ev if e["ev"] == "start"]
    return s[0] if s else {}


def bucket_count(d: dict) -> int | None:
    b = d.get("ddp_buckets", {}).get("rebuilt_bucket_sizes")      # the buckets DDP actually uses
    if not b:
        return None
    return len([x for x in str(b).split(",") if x.strip()])


def attempts_summary(ev: list[dict], faults: list[dict], fault_kind: str) -> list[dict]:
    """One record per injected fault: detection, restart time R and lost steps."""
    out = []
    shots = sorted((f for f in faults if f["ev"] == fault_kind), key=lambda f: f["t"])
    for shot in shots:
        a = shot["attempt"]
        prev_steps = [e for e in ev if e["ev"] == "step" and e["attempt"] == a]
        last_done = max((e["step"] for e in prev_steps), default=0)
        nxt = [e for e in ev if e["ev"] == "start" and e["attempt"] == a + 1]
        nxt_steps = sorted((e for e in ev if e["ev"] == "step" and e["attempt"] == a + 1), key=lambda e: e["t"])
        errs = [f for f in faults if f["ev"] == "peer_error" and f["attempt"] == a]
        terms = [f for f in faults if f["ev"] == "sigterm" and f["attempt"] == a and f["rank"] != shot["rank"]]
        notice = [f["t"] for f in errs + terms]
        rec = {"fault_step": shot["step"], "attempt": a, "t_fault": shot["t"],
               "last_completed_step": last_done,
               "peer_errors": len(errs), "peer_sigterms": len(terms),
               "first_error_type": errs[0]["type"] if errs else None,
               "first_error": errs[0]["err"] if errs else None,
               "detect_s": (min(notice) - shot["t"]) if notice else None,
               "peer_error_s": (min(f["t"] for f in errs) - shot["t"]) if errs else None}
        if nxt:
            rec["resume_step"] = nxt[0]["resume_step"]
            rec["lost_steps"] = last_done - nxt[0]["resume_step"]
        if nxt_steps:
            first = nxt_steps[0]
            rec["restart_s"] = (first["t"] - first["dt"]) - shot["t"]   # fault -> first step starts again
        out.append(rec)
    return out


LOSS_RTOL = 1e-5   # resumed and uninterrupted runs agree to float32 rounding; bit-exact is not guaranteed


def same_loss(a, b) -> bool | None:
    """True if two losses agree to LOSS_RTOL (gloo/CPU float sums can differ in the last bits)."""
    if a is None or b is None:
        return None
    return abs(a - b) <= LOSS_RTOL * max(abs(a), abs(b), 1e-12)


def rel_diff(a, b) -> float | None:
    return None if a is None or b is None else abs(a - b) / max(abs(a), abs(b), 1e-12)


def loss_at(ev: list[dict], step: int) -> float | None:
    v = [e["loss"] for e in ev if e["ev"] == "step" and e["step"] == step]
    return v[-1] if v else None


def main() -> int:
    out = Path(sys.argv[1])
    raw = out / "raw"
    codes = dict(line.split("\t") for line in (raw / "exit_codes.tsv").read_text().splitlines() if line.strip())
    codes = {k: int(v) for k, v in codes.items()}
    S: dict = {"lab": "ch11-handson", "run_id": out.name, "exit_codes": codes}

    # ---- Step 1: scaling
    base = start(events(raw, "weak_n1"))
    grad_mb = base.get("grad_mb", float("nan"))
    rows = []
    for n in NS:
        w, c, s = events(raw, f"weak_n{n}"), events(raw, f"weak_nocomm_n{n}"), events(raw, f"strong_n{n}")
        tw, tc, ts = step_time(w), step_time(c), step_time(s)
        d = done(w)
        ring_mb = 2 * (n - 1) / n * grad_mb
        exposed = tw - tc
        rows.append({"n": n, "weak_step_s": tw, "compute_only_step_s": tc, "exposed_comm_s": exposed,
                     "strong_step_s": ts, "strong_micro_batch": 64 // n,
                     "weak_samples_per_s": 32 * n / tw, "ring_bytes_per_rank_mb": ring_mb,
                     "busbw_implied_gbs": (ring_mb / 1e3 / exposed) if n > 1 and exposed > 0 else None,
                     "peak_rss_mib_total": round(sum(d.get("peak_rss_mib", [])), 1),
                     "replicas_identical": len(set(d.get("param_checksums", [0]))) == 1})
    t1w, t1s = rows[0]["weak_step_s"], rows[0]["strong_step_s"]
    for r in rows:
        r["weak_efficiency"] = t1w / r["weak_step_s"]
        r["strong_speedup"] = t1s / r["strong_step_s"]
        r["strong_efficiency"] = r["strong_speedup"] / r["n"]
    S["step1_scaling"] = {"params": base.get("params"), "grad_mb": grad_mb, "threads_per_rank": base.get("threads"),
                          "rows": rows}

    # ---- Step 2: buckets
    brow = []
    for b in BUCKETS:
        ev = events(raw, f"bucket_{b}")
        brow.append({"bucket_cap_mb": b, "step_s": step_time(ev), "buckets": bucket_count(done(ev)),
                     "bucket_sizes": done(ev).get("ddp_buckets", {}).get("rebuilt_bucket_sizes")})
    dflt = events(raw, "weak_n4")
    brow.append({"bucket_cap_mb": "default", "step_s": step_time(dflt), "buckets": bucket_count(done(dflt)),
                 "bucket_sizes": done(dflt).get("ddp_buckets", {}).get("rebuilt_bucket_sizes")})
    S["step2_buckets"] = {"n": 4, "compute_only_step_s": rows[2]["compute_only_step_s"], "rows": brow}

    # ---- Step 3: accumulation with no_sync
    tcomp = rows[2]["compute_only_step_s"]
    arow = []
    for k in ACCUM:
        ev = events(raw, f"accum_{k}")
        t = step_time(ev, warmup=3)
        arow.append({"accum": k, "step_s": t, "per_micro_batch_s": t / k, "samples_per_s": 4 * 32 * k / t,
                     "comm_per_step_s": t - k * tcomp, "comm_share": (t - k * tcomp) / t})
    for r in arow:
        r["speedup_vs_accum1"] = r["samples_per_s"] / arow[0]["samples_per_s"]
    S["step3_accum"] = {"n": 4, "compute_only_micro_batch_s": tcomp, "rows": arow}

    # ---- Step 4: GPU reference
    g = events(raw, "gpu_n1")
    if g:
        S["step4_gpu"] = {"ran": True, "step_s": step_time(g, warmup=10), "cpu_1rank_step_s": t1w,
                          "speedup_vs_cpu_1rank": t1w / step_time(g, warmup=10),
                          "cuda_peak_mib": done(g).get("cuda_peak_mib"), "backend": start(g).get("backend")}
    else:
        S["step4_gpu"] = {"ran": False, "reason": (raw / "gpu_n1.skipped").read_text().strip()
                          if (raw / "gpu_n1.skipped").exists() else "no gpu_n1 log"}

    # ---- Step 5: faults
    ref = events(raw, "ckpt_base")
    ref40 = loss_at(ref, 40)
    f5 = {}
    for name, kind in [("fault_kill_norestart", "kill"), ("fault_kill", "kill"),
                       ("fault_hang_t10", "hang"), ("fault_hang_t20", "hang")]:
        ev, fl = events(raw, name), events(raw, name, ".faults")
        recs = attempts_summary(ev, fl, kind)
        log = (raw / f"{name}.log").read_text(errors="replace") if (raw / f"{name}.log").exists() else ""
        f5[name] = {"exit_code": codes.get(name), "pg_timeout_s": start(ev).get("pg_timeout_s"),
                    "attempts": len([e for e in ev if e["ev"] == "start"]),
                    "completed": bool(done(ev)), "final_step": done(ev).get("final_step"),
                    "final_loss": done(ev).get("final_loss"), "reference_loss_step40": ref40,
                    "loss_matches_uninterrupted": same_loss(done(ev).get("final_loss"), ref40) if done(ev) else None,
                    "loss_bit_exact": (done(ev).get("final_loss") == ref40) if done(ev) else None,
                    "loss_rel_diff": rel_diff(done(ev).get("final_loss"), ref40) if done(ev) else None,
                    "torchrun_reports_child_failed": "ChildFailedError" in log,
                    "faults": recs}
    S["step5_faults"] = f5

    # ---- Step 6: checkpoint interval vs lost work
    fsteps = [int(x) for x in (raw / "ckpt_fault_steps.txt").read_text().strip().split(",")]
    tstep = step_time(ref)
    ref_final = done(ref).get("final_loss")
    krow = []
    for K in KS:
        ev, fl = events(raw, f"ckpt_K{K}"), events(raw, f"ckpt_K{K}", ".faults")
        recs = attempts_summary(ev, fl, "kill")
        steps_ev = [e for e in ev if e["ev"] == "step"]
        ck = [e["dt"] for e in ev if e["ev"] == "ckpt"]
        lost = [r.get("lost_steps") for r in recs]
        pred = [(s - 1) % K for s in fsteps]
        restarts = [r["restart_s"] for r in recs if r.get("restart_s") is not None]
        nfail = len(recs)
        useful = CKPT_STEPS * tstep
        mtbf = useful / nfail if nfail else float("inf")
        C = st.median(ck) if ck else float("nan")
        tau = K * tstep
        R = st.median(restarts) if restarts else float("nan")
        t_first = min((e["t"] for e in ev if e["ev"] == "start"), default=float("nan"))
        wall = done(ev).get("t", float("nan")) - t_first
        krow.append({
            "K_steps": K, "tau_s": tau, "failures": nfail, "attempts": len([e for e in ev if e["ev"] == "start"]),
            "completed": bool(done(ev)), "final_loss_matches": same_loss(done(ev).get("final_loss"), ref_final),
            "final_loss_bit_exact": done(ev).get("final_loss") == ref_final,
            "final_loss_rel_diff": rel_diff(done(ev).get("final_loss"), ref_final),
            "step_executions": len(steps_ev), "re_executed_steps": len(steps_ev) - CKPT_STEPS,
            "lost_steps_measured": lost, "lost_steps_predicted": pred,
            "lost_mean_steps": st.mean([x for x in lost if x is not None]) if any(x is not None for x in lost) else None,
            "lost_model_mean_steps_tau_over_2": K / 2,
            "checkpoints": len(ck), "C_s": C, "ckpt_total_s": sum(ck), "restart_median_s": R,
            "restart_total_s": sum(restarts), "wall_s": wall, "useful_s": useful, "mtbf_s": mtbf,
            "measured_ckpt_frac": sum(ck) / useful,
            "measured_lost_frac": sum(x for x in lost if x is not None) * tstep / useful,
            "measured_restart_frac": sum(restarts) / useful,
            "model_ckpt_frac": C / tau, "model_lost_frac": (tau / 2) / mtbf, "model_restart_frac": R / mtbf,
        })
        r = krow[-1]
        r["measured_tau_dependent_frac"] = r["measured_ckpt_frac"] + r["measured_lost_frac"]
        r["model_tau_dependent_frac"] = r["model_ckpt_frac"] + r["model_lost_frac"]
    Cm = st.median([r["C_s"] for r in krow])
    mtbf = krow[0]["mtbf_s"]
    tau_opt = math.sqrt(2 * Cm * mtbf)
    best = min(krow, key=lambda r: r["measured_tau_dependent_frac"])
    S["step6_ckpt_interval"] = {"n": 4, "steps": CKPT_STEPS, "fault_steps": fsteps, "step_s": tstep,
                                "reference_final_loss": ref_final, "C_median_s": Cm, "mtbf_s": mtbf,
                                "tau_opt_s": tau_opt, "tau_opt_steps": tau_opt / tstep,
                                "best_measured_K": best["K_steps"], "rows": krow}
    S["run_seconds"] = int((raw / "run_seconds.txt").read_text().strip()) if (raw / "run_seconds.txt").exists() else None
    S["loadavg_before"] = (raw / "loadavg_before.txt").read_text().strip() if (raw / "loadavg_before.txt").exists() else None
    S["loadavg_after"] = (raw / "loadavg_after.txt").read_text().strip() if (raw / "loadavg_after.txt").exists() else None
    (out / "summary.json").write_text(json.dumps(S, indent=2) + "\n")
    (out / "report.md").write_text(report(S))
    print(f"wrote {out / 'summary.json'} and {out / 'report.md'}")
    return 0


def f(x, nd=3):
    return "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{nd}f}"


def report(S: dict) -> str:
    L = []
    s1 = S["step1_scaling"]
    L += [f"# Chapter 11 hands-on: multi-process training, run `{S['run_id']}`", "",
          "Every number below is `[MEASURED]` by this run (step named in brackets) unless labelled `[MODELED]`, "
          "which means computed by the chapter's formulas from measured inputs. CPU ranks use gloo over loopback "
          f"with {s1['threads_per_rank']} thread each; the model has {s1['params']:,} parameters "
          f"({f(s1['grad_mb'], 1)} MB of FP32 gradients). Load average before/after: "
          f"{S['loadavg_before']} / {S['loadavg_after']} (other jobs on the host add noise). "
          f"Total run time {S['run_seconds']} s.", "",
          "## Step 1: scaling (gloo, CPU)", "",
          "| Ranks | Weak step (s) | Compute-only (s) | Exposed comm (s) | Weak eff. | Samples/s | Strong step (s) | Strong speedup | Strong eff. | Ring bytes/rank (MB) `[MODELED]` | Implied busbw (GB/s) | Peak RSS, all ranks (MiB) |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in s1["rows"]:
        L.append(f"| {r['n']} | {f(r['weak_step_s'])} | {f(r['compute_only_step_s'])} | {f(r['exposed_comm_s'])} | "
                 f"{f(r['weak_efficiency'], 2)} | {f(r['weak_samples_per_s'], 0)} | {f(r['strong_step_s'])} | "
                 f"{f(r['strong_speedup'], 2)} | {f(r['strong_efficiency'], 2)} | {f(r['ring_bytes_per_rank_mb'], 1)} | "
                 f"{f(r['busbw_implied_gbs'], 2)} | {r['peak_rss_mib_total']} |")
    L += ["", "All values `[MEASURED]` (Step 1) except the ring bytes, 2(n − 1)/n × gradient bytes `[MODELED]`. "
          "Weak scaling keeps 32 samples per rank; strong scaling keeps 64 samples per step. "
          "Replica parameter checksums identical on every rank: "
          f"{all(r['replicas_identical'] for r in s1['rows'])} `[MEASURED]`.", "",
          "## Step 2: gradient bucket size (4 ranks)", "",
          "| bucket_cap_mb | Buckets | Bucket sizes (bytes) | Step (s) |", "|---|---|---|---|"]
    for r in S["step2_buckets"]["rows"]:
        L.append(f"| {r['bucket_cap_mb']} | {r['buckets']} | {r['bucket_sizes']} | {f(r['step_s'])} |")
    L += ["", f"Compute-only step at 4 ranks: {f(S['step2_buckets']['compute_only_step_s'])} s `[MEASURED]` (Step 1). "
          "Bucket counts are DDP's own record after its iteration-1 rebuild `[MEASURED]` (Step 2).", "",
          "## Step 3: gradient accumulation with no_sync (4 ranks)", "",
          "| Micro-batches per step | Step (s) | Per micro-batch (s) | Samples/s | Comm per step (s) | Comm share | Throughput vs k = 1 |",
          "|---|---|---|---|---|---|---|"]
    for r in S["step3_accum"]["rows"]:
        L.append(f"| {r['accum']} | {f(r['step_s'])} | {f(r['per_micro_batch_s'])} | {f(r['samples_per_s'], 0)} | "
                 f"{f(r['comm_per_step_s'])} | {f(r['comm_share'], 2)} | {f(r['speedup_vs_accum1'], 2)} |")
    L += ["", "Comm per step = step − k × compute-only micro-batch time `[MEASURED]` (Steps 1 and 3).", "",
          "## Step 4: GPU reference (1 rank, NCCL)", ""]
    g = S["step4_gpu"]
    if g["ran"]:
        L.append(f"Step time {f(g['step_s'], 4)} s on the GPU against {f(g['cpu_1rank_step_s'], 4)} s for one CPU rank "
                 f"({f(g['speedup_vs_cpu_1rank'], 1)}×), peak CUDA memory {g['cuda_peak_mib']} MiB `[MEASURED]` (Step 4). "
                 "A one-rank NCCL group moves no gradient bytes.")
    else:
        L.append(f"Not run: {g['reason']}.")
    L += ["", "## Step 5: faults", "",
          "| Run | Timeout (s) | Exit | Attempts | First notice by a peer (s) | Peer error | Lost steps | Restart R (s) | Final loss = uninterrupted |",
          "|---|---|---|---|---|---|---|---|---|"]
    for name, r in S["step5_faults"].items():
        fr = r["faults"][0] if r["faults"] else {}
        L.append(f"| {name} | {r['pg_timeout_s']} | {r['exit_code']} | {r['attempts']} | {f(fr.get('detect_s'), 2)} | "
                 f"{fr.get('first_error_type') or ('SIGTERM from torchrun' if fr.get('peer_sigterms') else 'none')} | "
                 f"{fr.get('lost_steps', 'n/a')} | {f(fr.get('restart_s'), 2)} | {r['loss_matches_uninterrupted']}{' (bit-exact)' if r['loss_bit_exact'] else ''} |")
    L += ["", "All `[MEASURED]` (Step 5). Faults fire on rank 2 just before step 23; checkpoints every 10 steps.", ""]
    for name, r in S["step5_faults"].items():
        fr = r["faults"][0] if r["faults"] else {}
        if fr.get("first_error"):
            L.append(f"- {name}: `{fr['first_error'][:160]}`")
    s6 = S["step6_ckpt_interval"]
    L += ["", "## Step 6: lost work against checkpoint interval (4 ranks, 192 steps, 6 kills)", "",
          f"Kills at steps {s6['fault_steps']}; step time {f(s6['step_s'], 4)} s, median checkpoint cost C = "
          f"{f(s6['C_median_s'], 3)} s, productive MTBF = {f(s6['mtbf_s'], 2)} s `[MEASURED]`. "
          f"Young/Daly τ_opt = √(2·C·MTBF) = {f(s6['tau_opt_s'], 2)} s = {f(s6['tau_opt_steps'], 1)} steps `[MODELED]`; "
          f"lowest measured checkpoint + lost-work overhead at K = {s6['best_measured_K']} steps `[MEASURED]`.", "",
          "| K (steps) | τ (s) | Lost steps per kill, measured | (s − 1) mod K `[MODELED]` | Mean lost (steps) | τ/2 (steps) `[MODELED]` | Ckpt overhead | C/τ `[MODELED]` | Lost-work overhead | (τ/2)/MTBF `[MODELED]` | Sum measured | Sum model | Restart R median (s) | Final loss = uninterrupted |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in s6["rows"]:
        L.append(f"| {r['K_steps']} | {f(r['tau_s'], 2)} | {r['lost_steps_measured']} | {r['lost_steps_predicted']} | "
                 f"{f(r['lost_mean_steps'], 2)} | {f(r['lost_model_mean_steps_tau_over_2'], 1)} | "
                 f"{f(100 * r['measured_ckpt_frac'], 1)} % | {f(100 * r['model_ckpt_frac'], 1)} % | "
                 f"{f(100 * r['measured_lost_frac'], 1)} % | {f(100 * r['model_lost_frac'], 1)} % | "
                 f"{f(100 * r['measured_tau_dependent_frac'], 1)} % | {f(100 * r['model_tau_dependent_frac'], 1)} % | "
                 f"{f(r['restart_median_s'], 2)} | {r['final_loss_matches']} ({'bit-exact' if r['final_loss_bit_exact'] else 'rel. diff ' + f(r['final_loss_rel_diff'], 8)}) |")
    L += ["", "Overheads are fractions of the useful compute time (192 × step time). R/MTBF does not depend on τ "
          "and is reported separately as the restart column. Measured values from Step 6 logs `[MEASURED]`. "
          "\"Final loss = uninterrupted\" means within a relative 1e-5 of the run with no faults; float sums on CPU "
          "are not guaranteed bit-exact across restarts, so the bit-exact result is shown too.", ""]
    return "\n".join(L)


if __name__ == "__main__":
    sys.exit(main())
