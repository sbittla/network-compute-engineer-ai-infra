#!/usr/bin/env python3
"""Check a Chapter 12 hands-on results directory for completeness and physical sense.

    python check.py results/<run-id>

Prints one PASS/FAIL line per check and exits 0 only if all pass. It recomputes algbw and busbw from
the raw sweeps and tests what any correct run must show (results are correct, small messages are
latency-bound and large ones bandwidth-bound, latency grows with rank count, the tree wins small
messages and the ring large ones, NCCL refuses two ranks on one GPU), not the reference machine's
absolute numbers. Python standard library only.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

RESULTS: list[tuple[bool, str]] = []
OPS = ["all_reduce", "all_gather", "reduce_scatter", "broadcast"]


def check(ok: bool, msg: str) -> None:
    RESULTS.append((bool(ok), msg))
    print(f"{'PASS' if ok else 'FAIL'}  {msg}")


def num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def factor(op: str, n: int) -> float:
    if op.endswith("all_reduce") or op.endswith("allreduce"):
        return 2 * (n - 1) / n
    if op in ("all_gather", "reduce_scatter"):
        return (n - 1) / n
    return 1.0


def load(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


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
        S = json.loads((d / "summary.json").read_text(encoding="utf-8"))
        env = json.loads((d / "environment.json").read_text(encoding="utf-8")) if (d / "environment.json").is_file() else {}
    except json.JSONDecodeError as e:
        print(f"FAIL  summary.json or environment.json is not valid JSON: {e}")
        return 1
    check(bool(env.get("kernel")) and bool(env.get("captured_at")), "environment.json records kernel and time")
    report = (d / "report.md").read_text(encoding="utf-8") if (d / "report.md").is_file() else ""
    check(report.count("[MEASURED]") >= 5, "report.md labels its numbers [MEASURED]")
    codes = S.get("exit_codes", {})
    bad = [k for k, v in codes.items() if k != "nccl_2ranks_1gpu" and v != 0]
    check(len(codes) >= 7 and not bad, f"every sweep launch exited 0 (bad: {bad or 'none'})")

    # ---- raw sweeps: completeness, correctness, recomputed bandwidths
    raw = {n: load(d / "raw" / f"coll_n{n}.jsonl") for n in (2, 4, 8)}
    for n, rows in raw.items():
        for op in OPS:
            rs = sorted((r for r in rows if r.get("op") == op), key=lambda r: r["bytes"])
            okc = len(rs) >= 20 and rs[0]["bytes"] <= 64 and rs[-1]["bytes"] >= 32 * 2**20
            check(okc, f"raw {op} n={n}: sweep from <= 64 B to >= 32 MiB ({len(rs)} sizes)")
            if not okc:
                continue
            wrong = sum(r["wrong"] for r in rs)
            recomputed = all(abs(r["bytes"] / (r["time_us"] * 1e-6) / 1e9 - r["algbw_gbs"]) <= 1e-6 * max(1, r["algbw_gbs"])
                             and abs(r["algbw_gbs"] * factor(op, n) - r["busbw_gbs"]) <= 1e-6 * max(1, r["busbw_gbs"])
                             for r in rs)
            check(wrong == 0 and recomputed, f"raw {op} n={n}: #wrong = {wrong}; algbw = S/t and busbw = algbw x factor recompute")
            # latency region: 8n B (every step of gloo's 2n-chunk ring carries data) up to 4 KiB
            small = [r["time_us"] for r in rs if 8 * n <= r["bytes"] <= 4096]
            if not small:
                check(False, f"raw {op} n={n}: no sizes between {8 * n} B and 4 KiB")
                continue
            check(rs[-1]["time_us"] > 10 * max(small),
                  f"raw {op} n={n}: 64 MiB takes > 10x the small-message time (bandwidth region exists)")
            check(max(small) < 5 * min(small),
                  f"raw {op} n={n}: times from {8 * n} B to 4 KiB lie within 5x of each other (latency region is flat; "
                  f"{min(small):.0f}-{max(small):.0f} us)")

    # ---- fits and the chapter's model
    try:
        T = {(r["op"], r["n"]): r for r in S["step1_sweeps"]["rows"]}
        fits_ok = all(num(r["alpha_us"]) and r["alpha_us"] > 0 and num(r["B_gbs"]) and r["B_gbs"] > 0
                      and num(r["n_half_bytes"]) and 1 <= r["n_half_bytes"] <= 2**31 for r in T.values())
        check(len(T) == 12 and fits_ok, "alpha-beta fit gives alpha > 0, B > 0 and 1 B <= n_half <= 2 GiB for all 12 sweeps")
        a2, a8 = T[("all_reduce", 2)]["alpha_us"], T[("all_reduce", 8)]["alpha_us"]
        check(a8 > a2, f"all_reduce latency grows with rank count (alpha n=2 {a2:.1f} us < n=8 {a8:.1f} us)")
        g2, g8 = T[("all_reduce", 2)]["plateau_algbw_gbs"], T[("all_reduce", 8)]["plateau_algbw_gbs"]
        check(g8 < g2, f"all_reduce algbw falls from 2 to 8 ranks ({g2:.3f} -> {g8:.3f} GB/s)")
        check(all(abs(r["busbw_over_algbw"] - r["factor"]) < 1e-6 for r in T.values()),
              "busbw / algbw equals the chapter's factor for every sweep")
    except (KeyError, TypeError) as e:
        check(False, f"fits: summary incomplete ({e})")

    try:
        r2 = S["step2_repeats"]
        check(r2["launches"] >= 3 and num(r2["plateau_cv"]) and r2["plateau_cv"] < 0.5,
              f"step 2: >= 3 launches, plateau CV {r2.get('plateau_cv')} < 0.5")
    except (KeyError, TypeError) as e:
        check(False, f"step 2: summary incomplete ({e})")

    try:
        p = S["step3_p2p"]
        check(num(p["alpha_us"]) and p["alpha_us"] > 0 and num(p["B_gbs"]) and p["B_gbs"] > 0,
              "step 3: ping-pong gives alpha > 0 and B > 0")
        for n in ("4", "8"):
            a = S["step3_ring_vs_tree"][n]
            rows = a["rows"]
            check(len(rows) >= 10 and all(r["wrong"] == 0 for r in rows), f"step 3 n={n}: ring and tree sweeps complete and correct")
            check(rows[0]["faster"] == "tree" and rows[-1]["faster"] == "ring",
                  f"step 3 n={n}: the tree wins the smallest message and the ring the largest "
                  f"({rows[0]['faster']} at {rows[0]['bytes']} B, {rows[-1]['faster']} at {rows[-1]['bytes']} B)")
    except (KeyError, TypeError, IndexError) as e:
        check(False, f"step 3: summary incomplete ({e})")

    g = S.get("step4_nccl", {})
    if g.get("ran"):
        check(g.get("two_ranks_one_gpu_exit") not in (0, None) and g.get("duplicate_gpu_rejected") is True,
              "step 4: NCCL refuses two ranks on one GPU (Duplicate GPU detected)")
        fl = g.get("ops", {}).get("all_reduce", {}).get("floor_us")
        check(num(fl) and 0 < fl < 10_000, f"step 4: one-rank NCCL all_reduce floor measured ({fl} us)")
        check(all(r.get("wrong") == 0 for r in g.get("ops", {}).values()), "step 4: NCCL results correct (#wrong = 0)")
    else:
        check(bool(g.get("reason")), f"step 4: NCCL step skipped with a reason ({g.get('reason')})")

    failed = sum(1 for ok, _ in RESULTS if not ok)
    print(f"\n{len(RESULTS) - failed}/{len(RESULTS)} checks passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
