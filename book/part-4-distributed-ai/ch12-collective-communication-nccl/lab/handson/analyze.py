#!/usr/bin/env python3
"""Chapter 12 hands-on lab: turn the raw sweeps in results/<run-id>/raw/ into summary.json and report.md.

    python analyze.py results/<run-id>

Fits T(S) = alpha + factor * S / B to every sweep, weighting each point by 1/T (the chapter's method),
and compares the measurements with the chapter's alpha-beta formulas. Standard library only.
"""
from __future__ import annotations

import json
import math
import statistics as st
import sys
from pathlib import Path

OPS = ["all_reduce", "all_gather", "reduce_scatter", "broadcast"]
NS = [2, 4, 8]
MiB = 2**20


def factor(op: str, n: int) -> float:
    if op in ("all_reduce", "ring_allreduce", "tree_allreduce"):
        return 2 * (n - 1) / n
    if op in ("all_gather", "reduce_scatter"):
        return (n - 1) / n
    return 1.0


def load(raw: Path, name: str) -> list[dict]:
    p = raw / f"{name}.jsonl"
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]


def series(rows: list[dict], op: str) -> list[dict]:
    return sorted((r for r in rows if r["op"] == op), key=lambda r: r["bytes"])


def fit(rs: list[dict], f: float) -> dict:
    """Weighted least squares of T = alpha + f*S*beta with weights 1/T: minimise sum((model - T)/T)^2."""
    if len(rs) < 3 or f == 0:
        return {"alpha_us": None, "B_gbs": None, "n_half_bytes": None}
    a11 = a12 = a22 = b1 = b2 = 0.0
    for r in rs:
        t = r["time_us"] * 1e-6
        x1, x2 = 1 / t, f * r["bytes"] / t
        a11, a12, a22, b1, b2 = a11 + x1 * x1, a12 + x1 * x2, a22 + x2 * x2, b1 + x1, b2 + x2
    det = a11 * a22 - a12 * a12
    alpha = (b1 * a22 - b2 * a12) / det
    beta = (a11 * b2 - a12 * b1) / det
    B = 1 / beta if beta > 0 else float("inf")
    return {"alpha_us": alpha * 1e6, "B_gbs": B / 1e9, "n_half_bytes": alpha * B / f if beta > 0 else None}


def latency_region(n: int) -> tuple[int, int]:
    """Sizes that are latency-bound with every algorithm step doing work: 8n B (two float32 per rank, gloo's
    ring uses 2n chunks and skips empty ones) up to 4 KiB."""
    return 8 * n, 4096


def summarize(rs: list[dict], op: str, n: int) -> dict:
    big = rs[-4:]
    lo, hi = latency_region(n)
    small = [r for r in rs if lo <= r["bytes"] <= hi]
    tiny = [r for r in rs if r["bytes"] < lo]
    out = {"op": op, "n": n, "points": len(rs), "wrong": sum(r["wrong"] for r in rs),
           "floor_us": st.median(r["time_us"] for r in small) if small else None,
           "plateau_busbw_gbs": st.median(r["busbw_gbs"] for r in big) if big else None,
           "plateau_algbw_gbs": st.median(r["algbw_gbs"] for r in big) if big else None,
           "t_max_us": rs[-1]["time_us"] if rs else None, "max_bytes": rs[-1]["bytes"] if rs else None,
           "busbw_over_algbw": (rs[-1]["busbw_gbs"] / rs[-1]["algbw_gbs"]) if rs else None,
           "factor": factor(op, n), "latency_region_bytes": [lo, hi],
           "below_region_us": {str(r["bytes"]): r["time_us"] for r in tiny}}
    out.update(fit([r for r in rs if r["bytes"] >= lo], factor(op, n)))
    return out


def at(rs: list[dict], nbytes: int) -> dict | None:
    return min(rs, key=lambda r: abs(math.log(r["bytes"]) - math.log(nbytes))) if rs else None


def main() -> int:
    out = Path(sys.argv[1])
    raw = out / "raw"
    codes = {k: int(v) for k, v in (line.split("\t") for line in (raw / "exit_codes.tsv").read_text().splitlines() if line.strip())}
    S: dict = {"lab": "ch12-handson", "run_id": out.name, "exit_codes": codes}
    data = {n: load(raw, f"coll_n{n}") for n in NS}
    init = {n: next((r["init_s"] for r in data[n] if r["op"] == "_init"), None) for n in NS}

    # ---- Step 1: sweeps and fits
    table = []
    for n in NS:
        for op in OPS:
            rs = series(data[n], op)
            if rs:
                table.append(summarize(rs, op, n))
    S["step1_sweeps"] = {"init_s": init, "rows": table,
                         "raw": {f"{op}_n{n}": [[r["bytes"], round(r["time_us"], 3)] for r in series(data[n], op)]
                                 for n in NS for op in OPS}}
    T = {(r["op"], r["n"]): r for r in table}

    # chapter comparisons
    comp = {}
    comp["busbw_plateau_by_n"] = {op: {n: T[(op, n)]["plateau_busbw_gbs"] for n in NS if (op, n) in T} for op in OPS}
    comp["algbw_plateau_by_n"] = {op: {n: T[(op, n)]["plateau_algbw_gbs"] for n in NS if (op, n) in T} for op in OPS}
    comp["all_reduce_alpha_by_n"] = {n: {"alpha_us": T[("all_reduce", n)]["alpha_us"],
                                         "ring_steps_2(n-1)": 2 * (n - 1),
                                         "alpha_per_step_us": T[("all_reduce", n)]["alpha_us"] / (2 * (n - 1)),
                                         "tree_steps_2log2n": 2 * math.log2(n)} for n in NS if ("all_reduce", n) in T}
    ident = []
    for n in NS:
        ar, ag, rsc = series(data[n], "all_reduce"), series(data[n], "all_gather"), series(data[n], "reduce_scatter")
        for size in (64 * 1024, MiB, 16 * MiB, 64 * MiB):
            a, g, r = at(ar, size), at(ag, size), at(rsc, size)
            if a and g and r:
                ident.append({"n": n, "bytes": a["bytes"], "t_all_reduce_us": a["time_us"],
                              "t_reduce_scatter_us": r["time_us"], "t_all_gather_us": g["time_us"],
                              "ratio_ar_over_rs_plus_ag": a["time_us"] / (r["time_us"] + g["time_us"]),
                              "ratio_rs_over_ar": r["time_us"] / a["time_us"]})
    comp["identity_all_reduce_eq_rs_plus_ag"] = ident
    if ("all_reduce", 4) in T:
        t4 = T[("all_reduce", 4)]
        sb = 25 * MiB
        f4 = factor("all_reduce", 4)
        bw_term = f4 * sb / (t4["B_gbs"] * 1e9) * 1e6
        meas = at(series(data[4], "all_reduce"), 32 * MiB)
        comp["ddp_bucket_25MiB_n4"] = {"predicted_us": t4["alpha_us"] + bw_term, "bandwidth_term_us": bw_term,
                                       "fraction_of_plateau": bw_term / (t4["alpha_us"] + bw_term),
                                       "n_half_bytes": t4["n_half_bytes"],
                                       "measured_32MiB_us": meas["time_us"] if meas else None}
    S["step1_model"] = comp

    # ---- Step 2: run-to-run spread at n = 4
    reps = [series(data[4], "all_reduce"), series(load(raw, "coll_n4_rep2"), "all_reduce"),
            series(load(raw, "coll_n4_rep3"), "all_reduce")]
    reps = [r for r in reps if r]
    plateaus = [st.median(x["busbw_gbs"] for x in r[-4:]) for r in reps]
    per_size_cv = []
    for i in range(min(len(r) for r in reps)):
        ts = [r[i]["time_us"] for r in reps]
        per_size_cv.append({"bytes": reps[0][i]["bytes"], "times_us": ts,
                            "cv": st.pstdev(ts) / st.mean(ts) if len(ts) > 1 else None})
    S["step2_repeats"] = {"launches": len(reps), "plateau_busbw_gbs": plateaus,
                          "plateau_cv": (st.pstdev(plateaus) / st.mean(plateaus)) if len(plateaus) > 1 else None,
                          "median_per_size_cv": st.median(c["cv"] for c in per_size_cv) if per_size_cv else None,
                          "per_size": per_size_cv}

    # ---- Step 3: ring vs tree, predicted from the ping-pong alpha and beta
    pp = series(data[2], "pingpong")
    p2p = fit(pp, 1.0) if pp else {}
    S["step3_p2p"] = {"rows": [[r["bytes"], r["time_us"]] for r in pp], **p2p}
    algo = {}
    for n in (4, 8):
        rows = load(raw, f"algo_n{n}")
        g, ring, tree = series(rows, "all_reduce"), series(rows, "ring_allreduce"), series(rows, "tree_allreduce")
        recs = []
        gb, tb = {r["bytes"]: r for r in g}, {r["bytes"]: r for r in tree}
        # join on the actual size: the ring rounds tiny sizes up to n elements, so the series differ in length
        for r_ in ring:
            a_, t_ = gb.get(r_["bytes"]), tb.get(r_["bytes"])
            if a_ is None or t_ is None:
                continue
            Sb = r_["bytes"]
            al, B = (p2p.get("alpha_us") or 0) * 1e-6, (p2p.get("B_gbs") or float("inf")) * 1e9
            pr = 2 * (n - 1) * (al + Sb / n / B) * 1e6
            pt = 2 * math.log2(n) * (al + Sb / B) * 1e6
            recs.append({"bytes": Sb, "gloo_us": a_["time_us"], "ring_us": r_["time_us"], "tree_us": t_["time_us"],
                         "ring_model_us": pr, "tree_model_us": pt, "faster": "ring" if r_["time_us"] < t_["time_us"] else "tree",
                         "faster_model": "ring" if pr < pt else "tree",
                         "wrong": a_["wrong"] + r_["wrong"] + t_["wrong"]})
        meas_x = next((r["bytes"] for r in recs if r["faster"] == "ring"), None)
        al, B = (p2p.get("alpha_us") or 0) * 1e-6, (p2p.get("B_gbs") or float("inf")) * 1e9
        k_a, k_b = 2 * (n - 1) - 2 * math.log2(n), 2 * math.log2(n) - 2 * (n - 1) / n
        algo[n] = {"rows": recs, "first_size_ring_wins": meas_x,
                   "model_crossover_bytes": al * B * k_a / k_b if k_b > 0 else None,
                   "ring_fit": fit(ring, factor("ring_allreduce", n)), "tree_fit": fit(tree, factor("tree_allreduce", n)),
                   "gloo_fit": fit(g, factor("all_reduce", n))}
    S["step3_ring_vs_tree"] = algo

    # ---- Step 4: NCCL on one GPU
    nc = load(raw, "nccl_n1")
    dup_log = (raw / "nccl_2ranks_1gpu.log").read_text(errors="replace") if (raw / "nccl_2ranks_1gpu.log").exists() else ""
    if nc:
        rows = {op: series(nc, op) for op in OPS}
        S["step4_nccl"] = {
            "ran": True, "init_s": next((r["init_s"] for r in nc if r["op"] == "_init"), None),
            "two_ranks_one_gpu_exit": codes.get("nccl_2ranks_1gpu"),
            "duplicate_gpu_rejected": "Duplicate GPU detected" in dup_log,
            "duplicate_gpu_line": next((ln.strip() for ln in dup_log.splitlines() if "Duplicate GPU detected" in ln), None),
            "nccl_version_line": next((ln.strip() for ln in (raw / "nccl_n1.log").read_text(errors="replace").splitlines()
                                       if "NCCL version" in ln), None) if (raw / "nccl_n1.log").exists() else None,
            "ops": {op: {"floor_us": st.median(r["time_us"] for r in rs if r["bytes"] <= 64 * 1024) if rs else None,
                         "t_64MiB_us": rs[-1]["time_us"] if rs else None,
                         "algbw_64MiB_gbs": rs[-1]["algbw_gbs"] if rs else None,
                         "busbw_64MiB_gbs": rs[-1]["busbw_gbs"] if rs else None,
                         "wrong": sum(r["wrong"] for r in rs)} for op, rs in rows.items()},
            "gloo_n2_all_reduce_floor_us": T[("all_reduce", 2)]["floor_us"] if ("all_reduce", 2) in T else None}
    else:
        S["step4_nccl"] = {"ran": False, "reason": (raw / "nccl.skipped").read_text().strip()
                           if (raw / "nccl.skipped").exists() else "no nccl_n1 log"}
    S["nccl_tests"] = (raw / "nccl_tests.txt").read_text().strip() if (raw / "nccl_tests.txt").exists() else None
    for k in ("run_seconds", "loadavg_before", "loadavg_after"):
        p = raw / f"{k}.txt"
        S[k] = p.read_text().strip() if p.exists() else None
    (out / "summary.json").write_text(json.dumps(S, indent=2) + "\n")
    (out / "report.md").write_text(report(S))
    print(f"wrote {out / 'summary.json'} and {out / 'report.md'}")
    return 0


def f(x, nd=2):
    return "n/a" if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))) else f"{x:.{nd}f}"


def size(b) -> str:
    if b is None:
        return "n/a"
    for unit, k in (("MiB", MiB), ("KiB", 1024)):
        if b >= k:
            return f"{b / k:g} {unit}"
    return f"{b} B"


def report(S: dict) -> str:
    L = [f"# Chapter 12 hands-on: collectives you can measure, run `{S['run_id']}`", "",
         "Numbers are `[MEASURED]` by this run (step in brackets) unless labelled `[MODELED]` (the chapter's "
         "formulas applied to measured inputs). CPU ranks use gloo over loopback TCP, one thread each; GB = 10⁹ B. "
         f"Load average before/after: {S['loadavg_before']} / {S['loadavg_after']}. Run time {S['run_seconds']} s.", "",
         "## Step 1: sweeps, 4 B to 64 MiB, and alpha-beta fits", "",
         "| Op | Ranks | Floor 8n B–4 KiB (µs) | α fit (µs) | B fit (GB/s) | n½ | Plateau algbw (GB/s) | Plateau busbw (GB/s) | busbw/algbw | #wrong |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for r in S["step1_sweeps"]["rows"]:
        L.append(f"| {r['op']} | {r['n']} | {f(r['floor_us'], 1)} | {f(r['alpha_us'], 1)} | {f(r['B_gbs'], 3)} | "
                 f"{size(int(r['n_half_bytes'])) if r['n_half_bytes'] else 'n/a'} | {f(r['plateau_algbw_gbs'], 3)} | "
                 f"{f(r['plateau_busbw_gbs'], 3)} | {f(r['busbw_over_algbw'], 3)} | {r['wrong']} |")
    L += ["", "All `[MEASURED]` (Step 1); α, B and n½ are fits to the measured points from 8n B up, n½ = α·B/factor. "
          "Floor = median time from 8n B to 4 KiB, where every step of gloo's ring (2n chunks) carries data; below "
          "8n B some chunks are empty and gloo skips them, so those calls are faster (see summary.json, "
          "below_region_us). Plateau = median of the four largest sizes (8–64 MiB).", "", "**Against the chapter's formulas.**", ""]
    m = S["step1_model"]
    L.append("- busbw plateau by rank count (ideal ring: independent of n) `[MEASURED]`: " + "; ".join(
        f"{op} " + ", ".join(f"n={n}: {f(v, 3)}" for n, v in d.items()) for op, d in m["busbw_plateau_by_n"].items()))
    L.append("- algbw plateau by rank count (falls as 2(n − 1)/n grows) `[MEASURED]`: all_reduce " + ", ".join(
        f"n={n}: {f(v, 3)}" for n, v in m["algbw_plateau_by_n"]["all_reduce"].items()))
    L.append("- all_reduce α against the ring's 2(n − 1) latency steps: " + "; ".join(
        f"n={n}: α = {f(v['alpha_us'], 1)} µs = {f(v['alpha_per_step_us'], 1)} µs × {v['ring_steps_2(n-1)']} steps"
        for n, v in m["all_reduce_alpha_by_n"].items()) + " `[MEASURED fit]`")
    L += ["", "| Ranks | Size | all_reduce (µs) | reduce_scatter (µs) | all_gather (µs) | AR / (RS + AG) | RS / AR |",
          "|---|---|---|---|---|---|---|"]
    for r in m["identity_all_reduce_eq_rs_plus_ag"]:
        L.append(f"| {r['n']} | {size(r['bytes'])} | {f(r['t_all_reduce_us'], 1)} | {f(r['t_reduce_scatter_us'], 1)} | "
                 f"{f(r['t_all_gather_us'], 1)} | {f(r['ratio_ar_over_rs_plus_ag'], 2)} | {f(r['ratio_rs_over_ar'], 2)} |")
    L += ["", "The identity all-reduce = reduce-scatter + all-gather predicts AR / (RS + AG) ≈ 1 and RS / AR ≈ 0.5 "
          "for a ring implementation `[MODELED]`; the measured ratios `[MEASURED]` show what gloo actually does.", ""]
    b = m.get("ddp_bucket_25MiB_n4")
    if b:
        L.append(f"- A 25 MiB DDP bucket on 4 ranks: α + factor·S/B = {f(b['predicted_us'], 0)} µs `[MODELED]` from the fit, "
                 f"{f(100 * b['fraction_of_plateau'], 0)} % of plateau bandwidth (n½ = {size(int(b['n_half_bytes']))}); "
                 f"measured 32 MiB all_reduce: {f(b['measured_32MiB_us'], 0)} µs `[MEASURED]`.")
    r2 = S["step2_repeats"]
    L += ["", "## Step 2: run-to-run spread (all_reduce, 4 ranks, separate launches)", "",
          f"Plateau busbw over {r2['launches']} launches: {', '.join(f(x, 3) for x in r2['plateau_busbw_gbs'])} GB/s, "
          f"CV {f(r2['plateau_cv'], 3)}; median per-size CV {f(r2['median_per_size_cv'], 3)} `[MEASURED]` (Step 2).", "",
          "## Step 3: ring versus tree (hand-written from send/recv)", ""]
    p = S["step3_p2p"]
    L.append(f"Ping-pong between two ranks: α = {f(p.get('alpha_us'), 1)} µs, B = {f(p.get('B_gbs'), 3)} GB/s "
             "`[MEASURED fit]`. Ring model 2(n − 1)(α + S/(nB)), tree model 2·log₂n·(α + S/B) `[MODELED]`.")
    for n, a in S["step3_ring_vs_tree"].items():
        L += ["", f"**{n} ranks.** First size where the ring beats the tree: {size(a['first_size_ring_wins'])} `[MEASURED]`; "
              f"model crossover α·B·(2(n−1) − 2log₂n)/(2log₂n − 2(n−1)/n) = {size(int(a['model_crossover_bytes'])) if a['model_crossover_bytes'] else 'n/a'} `[MODELED]`.", "",
              "| Size | gloo all_reduce (µs) | ring (µs) | tree (µs) | ring model (µs) | tree model (µs) | Faster | Model says |",
              "|---|---|---|---|---|---|---|---|"]
        for r in a["rows"]:
            L.append(f"| {size(r['bytes'])} | {f(r['gloo_us'], 1)} | {f(r['ring_us'], 1)} | {f(r['tree_us'], 1)} | "
                     f"{f(r['ring_model_us'], 1)} | {f(r['tree_model_us'], 1)} | {r['faster']} | {r['faster_model']} |")
    g = S["step4_nccl"]
    L += ["", "## Step 4: NCCL on one GPU", ""]
    if g["ran"]:
        L.append(f"Two ranks on one GPU: exit {g['two_ranks_one_gpu_exit']}, rejected by NCCL: {g['duplicate_gpu_rejected']} "
                 f"(`{g['duplicate_gpu_line']}`) `[MEASURED]`. {g['nccl_version_line'] or ''}")
        L += ["", "| Op (1 rank) | Floor ≤ 64 KiB (µs) | 64 MiB (µs) | algbw 64 MiB (GB/s) | busbw (GB/s) |", "|---|---|---|---|---|"]
        for op, r in g["ops"].items():
            L.append(f"| {op} | {f(r['floor_us'], 1)} | {f(r['t_64MiB_us'], 1)} | {f(r['algbw_64MiB_gbs'], 1)} | {f(r['busbw_64MiB_gbs'], 1)} |")
        L += ["", f"`[MEASURED]` (Step 4). busbw is 0 for one-rank all-reduce, all-gather and reduce-scatter because their "
              f"factors contain (n − 1). Broadcast's factor is 1, so its busbw only repeats algbw: an in-place one-rank "
              f"broadcast (and all-reduce) copies nothing, which is why its 64 MiB time equals its floor. The all-gather "
              f"and reduce-scatter 64 MiB times are a device-memory copy. One GPU shows the per-call floor, not a network. gloo's 2-rank all_reduce floor for comparison: "
              f"{f(g['gloo_n2_all_reduce_floor_us'], 1)} µs."]
    else:
        L.append(f"Not run: {g['reason']}.")
    L += ["", f"nccl-tests: {S['nccl_tests']}.", ""]
    return "\n".join(L)


if __name__ == "__main__":
    sys.exit(main())
