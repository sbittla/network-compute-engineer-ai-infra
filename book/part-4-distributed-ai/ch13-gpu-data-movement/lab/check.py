#!/usr/bin/env python3
"""Checker for the Chapter 13 lab (cross-layer straggler diagnosis on a 64-rank telemetry bundle).

Usage:
    python check.py                    # check starter/telemetry_diag.py (default)
    python check.py --impl solution    # check the reference implementation

Prints one line per check (PASS / FAIL / TODO); exits 0 only if every check passes. Expected values
for amplification are recomputed here directly from the CSV.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Callable

import pandas as pd

HERE = Path(__file__).resolve().parent
CSV = HERE / "data" / "telemetry.csv"
IMPLS = {
    "starter": HERE / "starter" / "telemetry_diag.py",
    "solution": HERE.parent / "solutions" / "lab" / "telemetry_diag.py",
}


def load(impl: str):
    spec = importlib.util.spec_from_file_location(f"telemetry_diag_{impl}", IMPLS[impl])
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--impl", choices=sorted(IMPLS), default="starter")
    args = ap.parse_args()
    try:
        td = load(args.impl)
        df = td.load_telemetry(CSV)
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL import/load_telemetry: {type(exc).__name__}: {exc}")
        return 1
    raw = pd.read_csv(CSV)

    def c_load() -> tuple[bool, str]:
        ok = len(df) == 3840 and df["rank"].nunique() == 64 and df["step"].nunique() == 60
        return ok, f"rows={len(df)} ranks={df['rank'].nunique()} steps={df['step'].nunique()}"

    def c_stats() -> tuple[bool, str]:
        st = td.per_step_stats(df).set_index("step")
        r10 = st.loc[10]
        exp_ratio = raw[raw.step == 10].compute_ms.max() / raw[raw.step == 10].compute_ms.median()
        ok = int(r10["slowest_rank"]) in (12, 37) and abs(r10["straggler_ratio"] - exp_ratio) < 1e-6 and len(st) == 60
        return ok, f"step 10: slowest rank {int(r10['slowest_rank'])}, ratio {r10['straggler_ratio']:.3f} (exp {exp_ratio:.3f})"

    def c_robust_z() -> tuple[bool, str]:
        z = td.robust_z(df, "compute_ms")
        s = raw[raw.step == 40]
        med = s.compute_ms.median()
        mad = (s.compute_ms - med).abs().median() * 1.4826
        exp = (s.loc[s["rank"] == 37, "compute_ms"].iloc[0] - med) / mad
        got = float(z[(df["step"] == 40) & (df["rank"] == 37)].iloc[0])
        return abs(got - exp) < 1e-6, f"z(rank 37, step 40) = {got:.1f} (exp {exp:.1f})"

    def c_stragglers() -> tuple[bool, str]:
        s = td.find_stragglers(df)
        return list(s) == [12, 37], f"stragglers={s} (expect two ranks with persistent robust z > 6)"

    def c_onset() -> tuple[bool, str]:
        o37, o12 = td.rank_onset(df, 37), td.rank_onset(df, 12)
        return o37 == 20 and o12 == 0, f"onset rank 37 = {o37}, rank 12 = {o12}"

    def c_cause() -> tuple[bool, str]:
        c37, c12 = td.attribute_cause(df, 37), td.attribute_cause(df, 12)
        return (c37, c12) == ("thermal", "data_imbalance"), f"rank 37 -> {c37}, rank 12 -> {c12}"

    def c_rails() -> tuple[bool, str]:
        rh = td.rail_health(df)
        flagged = sorted(int(r) for r in rh.loc[rh["flagged"], "rail"])
        onset = rh.loc[rh["flagged"], "onset_step"].tolist()
        return flagged == [2] and [int(x) for x in onset] == [30], f"flagged rails={flagged}, onset={onset}"

    def c_decoy() -> tuple[bool, str]:
        d = td.hot_not_throttled(df)
        return list(d) == [51], f"hot-but-not-throttled={d}"

    def c_amplification() -> tuple[bool, str]:
        a = td.amplification(df, 30, 59)
        w = raw[(raw.step >= 30) & (raw.step <= 59)]
        lost = w.wait_ms.sum() / 1000
        frac = lost / (64 * w.groupby("step").step_ms.first().sum() / 1000)
        ok = abs(a["lost_gpu_s"] - lost) < 1e-6 * lost and abs(a["lost_fraction"] - frac) < 1e-6 \
            and a["ideal_step_ms"] < 0.9 * a["actual_step_ms"]
        return ok, (f"lost {a['lost_gpu_s']:.0f} GPU-s ({a['lost_fraction']*100:.1f} %), "
                    f"ideal step {a['ideal_step_ms']:.0f} ms vs actual {a['actual_step_ms']:.0f} ms")

    def c_windows() -> tuple[bool, str]:
        w = td.symptom_windows(df, [(0, 19), (30, 59)]).set_index("window")
        early, late = w.loc["0-19"], w.loc["30-59"]
        ok = (late["sm_active_pct"] < early["sm_active_pct"] - 2 and abs(late["gpu_util_pct"] - early["gpu_util_pct"]) < 1
              and late["comm_ms"] > 1.5 * early["comm_ms"] and early["burst_tx_gbps"] > 300)
        return ok, (f"sm_active {early['sm_active_pct']:.1f} -> {late['sm_active_pct']:.1f} %, gpu_util "
                    f"{early['gpu_util_pct']:.1f} -> {late['gpu_util_pct']:.1f} %, comm {early['comm_ms']:.0f} -> "
                    f"{late['comm_ms']:.0f} ms, burst tx {early['burst_tx_gbps']:.0f} -> {late['burst_tx_gbps']:.0f} Gb/s")

    checks: list[tuple[str, Callable[[], tuple[bool, str]]]] = [
        ("load_telemetry", c_load), ("per_step_stats", c_stats), ("robust_z", c_robust_z),
        ("find_stragglers", c_stragglers), ("rank_onset", c_onset), ("attribute_cause", c_cause),
        ("rail_health", c_rails), ("hot_not_throttled", c_decoy), ("amplification", c_amplification),
        ("symptom_windows", c_windows),
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
