#!/usr/bin/env python3
"""Checker for the Chapter 12 lab (nccl-tests all_reduce_perf analysis).

Usage:
    python check.py                    # check starter/nccl_analysis.py (default)
    python check.py --impl solution    # check the reference implementation

Prints one line per check (PASS / FAIL / TODO); exits 0 only if every check passes.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Callable

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
IMPLS = {
    "starter": HERE / "starter" / "nccl_analysis.py",
    "solution": HERE.parent / "solutions" / "lab" / "nccl_analysis.py",
}
EXPECTED_LABELS = {
    "c1_1node_8gpu": "ok",
    "c2_2node_aligned": "ok",
    "c3_2node_alt_map": "low_plateau_steady",
    "c4_4node_aligned": "ok",
    "c5_8node_aligned": "ok",
    "c6_8node_run2": "low_plateau_jittery",
}


def load(impl: str):
    spec = importlib.util.spec_from_file_location(f"nccl_analysis_{impl}", IMPLS[impl])
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def text(name: str) -> str:
    return (DATA / f"{name}.log").read_text(encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--impl", choices=sorted(IMPLS), default="starter")
    args = ap.parse_args()
    try:
        na = load(args.impl)
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL import: {type(exc).__name__}: {exc}")
        return 1

    def c_factor() -> tuple[bool, str]:
        vals = (na.bus_factor("all_reduce", 8), na.bus_factor("all_gather", 8),
                na.bus_factor("reduce_scatter", 16), na.bus_factor("broadcast", 64))
        ok = all(abs(a - b) < 1e-12 for a, b in zip(vals, (1.75, 0.875, 15 / 16, 1.0)))
        return ok, f"all_reduce(8)={vals[0]}, all_gather(8)={vals[1]}, reduce_scatter(16)={vals[2]:.4f}, broadcast={vals[3]}"

    def c_parse() -> tuple[bool, str]:
        meta, df = na.parse_nccl_log(text("c2_2node_aligned"))
        ok = (len(df) == 31 and meta["nranks"] == 16 and meta["nodes"] == 2
              and set(meta["ranks_per_host"].values()) == {8} and meta["warmup_iters"] == 5
              and meta["iters"] == 20 and meta["avg_busbw_reported"] is not None
              and int(df["size"].iloc[-1]) == 8589934592 and float(df["time_us"].iloc[0]) > 0)
        return ok, f"rows={len(df)} nranks={meta['nranks']} nodes={meta['nodes']} iters={meta['iters']}"

    def c_bw() -> tuple[bool, str]:
        meta, df = na.parse_nccl_log(text("c5_8node_aligned"))
        worst = 0.0
        for t, a, b in (("time_us", "algbw", "busbw"), ("time_us_ip", "algbw_ip", "busbw_ip")):
            alg, bus = na.compute_bw(df["size"].to_numpy(), df[t].to_numpy(), meta["nranks"])
            for got, ref in ((alg, df[a].to_numpy()), (bus, df[b].to_numpy())):
                err = abs(got - ref) - (0.011 + 0.002 * abs(ref))
                worst = max(worst, float(err.max()))
        return worst <= 0, f"recomputed algbw/busbw match printed columns (worst excess {worst:.4f} GB/s)"

    def c_plateau() -> tuple[bool, str]:
        p1 = na.plateau_busbw(na.parse_nccl_log(text("c1_1node_8gpu"))[1])
        p5 = na.plateau_busbw(na.parse_nccl_log(text("c5_8node_aligned"))[1])
        ok = abs(p1 - 450) < 13.5 and abs(p5 - 346) < 10.4
        return ok, f"plateau busbw 1-node={p1:.1f} GB/s (~450), 8-node={p5:.1f} GB/s (~346)"

    def c_regions() -> tuple[bool, str]:
        _, df = na.parse_nccl_log(text("c2_2node_aligned"))
        reg = list(na.classify_regions(df))
        order = {"latency": 0, "transition": 1, "bandwidth": 2}
        mono = all(order[a] <= order[b] for a, b in zip(reg, reg[1:]))
        n_lat, n_bw = reg.count("latency"), reg.count("bandwidth")
        ok = reg[0] == "latency" and reg[-1] == "bandwidth" and mono and 15 <= n_lat <= 19 and 8 <= n_bw <= 10
        return ok, f"latency sizes={n_lat}, bandwidth sizes={n_bw}, monotonic={mono}"

    def c_fit() -> tuple[bool, str]:
        _, df = na.parse_nccl_log(text("c2_2node_aligned"))
        fit = na.fit_alpha_beta(df, 16)
        a, b, nh = fit["alpha_us"], fit["busbw_fit_GBps"], fit["n_half_bytes"]
        ok = abs(a - 28) / 28 < 0.15 and abs(b - 355) / 355 < 0.05 and abs(nh - a * 1e-6 * b * 1e9 / 1.875) / nh < 0.01
        return ok, f"alpha={a:.1f} us (~28), B={b:.1f} GB/s (~355), n_half={nh/1e6:.2f} MB"

    def c_jitter() -> tuple[bool, str]:
        j5 = na.jitter_cv(na.parse_nccl_log(text("c5_8node_aligned"))[1])
        j6 = na.jitter_cv(na.parse_nccl_log(text("c6_8node_run2"))[1])
        return j6 > 0.04 > j5, f"jitter CV c5={j5:.3f}, c6={j6:.3f}"

    def c_summary() -> tuple[bool, str]:
        s = na.analyze_all(DATA).set_index("name")
        ok = len(s) == 6 and (s.loc["c5_8node_aligned", "plateau_busbw"] > 2.5 * s.loc["c5_8node_aligned", "avg_busbw_reported"])
        return ok, (f"6 configs; c5 plateau {s.loc['c5_8node_aligned', 'plateau_busbw']:.0f} GB/s vs reported "
                    f"'Avg bus bandwidth' {s.loc['c5_8node_aligned', 'avg_busbw_reported']:.0f} GB/s")

    def c_detect() -> tuple[bool, str]:
        got = na.detect_anomalies(na.analyze_all(DATA))
        bad = {k: v for k, v in got.items() if EXPECTED_LABELS.get(k) != v}
        return not bad and len(got) == 6, f"mismatches={bad}" if bad else "anomalous configs correctly labelled"

    def c_predict() -> tuple[bool, str]:
        t = na.predict_time_us(28.0, 355.0, 16, 2**30)
        exp = 28.0 + 1.875 * 2**30 / 355e9 * 1e6
        return abs(t - exp) < 1e-6 * exp, f"1 GiB on 16 ranks: {t:.0f} us (exp {exp:.0f})"

    checks: list[tuple[str, Callable[[], tuple[bool, str]]]] = [
        ("bus_factor", c_factor), ("parse_nccl_log", c_parse), ("compute_bw", c_bw),
        ("plateau_busbw", c_plateau), ("classify_regions", c_regions), ("fit_alpha_beta", c_fit),
        ("jitter_cv", c_jitter), ("analyze_all", c_summary), ("detect_anomalies", c_detect),
        ("predict_time_us", c_predict),
    ]
    failed = 0
    for name, fn in checks:
        try:
            ok, msg = fn()
            print(f"{'PASS' if ok else 'FAIL'} {name}: {msg}")
            failed += not ok
        except NotImplementedError as exc:
            print(f"TODO {name}: implement {exc}")
            failed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL {name}: {type(exc).__name__}: {exc}")
            failed += 1
    print(f"\n{len(checks) - failed}/{len(checks)} checks passed ({args.impl})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
