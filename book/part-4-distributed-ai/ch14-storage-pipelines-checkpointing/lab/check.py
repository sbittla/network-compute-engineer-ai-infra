#!/usr/bin/env python3
"""Chapter 14 lab checker.

    python check.py                    # check lab/starter/storage_lab.py (your work)
    python check.py --impl solution    # check the reference implementation (instructors)

Prints one line per check (PASS / FAIL / TODO) and exits 0 only if every check passes.
Pure Python; no hardware, network, or root access; runs in a few seconds.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
import traceback
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
IMPLS = {"starter": HERE / "starter" / "storage_lab.py",
         "solution": HERE.parent / "solutions" / "lab" / "storage_lab.py"}


def load_impl(name: str):
    path = IMPLS[name]
    spec = importlib.util.spec_from_file_location(f"storage_lab_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def close(a: float, b: float, rel: float = 2e-3, abs_: float = 1e-9) -> bool:
    return abs(float(a) - float(b)) <= max(rel * abs(float(b)), abs_)


class Checker:
    def __init__(self) -> None:
        self.results: list[tuple[str, str, str]] = []

    def run(self, name: str, fn: Callable[[], str]) -> None:
        try:
            msg = fn()
            self.results.append(("PASS", name, msg))
        except NotImplementedError as e:
            self.results.append(("TODO", name, str(e) or "not implemented yet"))
        except AssertionError as e:
            self.results.append(("FAIL", name, str(e)))
        except Exception as e:  # noqa: BLE001 -- report, never crash
            last = traceback.extract_tb(e.__traceback__)[-1]
            self.results.append(("FAIL", name, f"{type(e).__name__}: {e} (line {last.lineno})"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--impl", choices=sorted(IMPLS), default="starter")
    args = ap.parse_args()
    try:
        m = load_impl(args.impl)
    except Exception as e:  # noqa: BLE001
        print(f"FAIL import {IMPLS[args.impl]}: {type(e).__name__}: {e}")
        return 2

    cfg = yaml.safe_load((DATA / "orion_ckpt_inputs.yaml").read_text(encoding="utf-8"))
    raw = pd.read_csv(DATA / "io_trace.csv")
    c = Checker()

    # ------------------------------------------------------------------ Part A: planner
    def a1() -> str:
        s = m.checkpoint_size_bytes(70e9, 14)
        assert close(s, 980e9), f"expected 980e9 B, got {s}"
        t = m.transfer_time_s(980e9, 80.0, 0.75)
        assert close(t, 16.3333), f"980 GB at 80 GB/s x 0.75 should be 16.33 s, got {t:.3f}"
        return "980 GB; 16.33 s at 60 GB/s effective"

    def a2() -> str:
        y = m.young_interval_s(17.8333, 172800)
        d = m.daly_interval_s(17.8333, 172800)
        assert close(y, 2482.58), f"Young: expected ~2482.6 s, got {y:.1f}"
        assert close(d, 2470.70), f"Daly: expected ~2470.7 s, got {d:.1f}"
        assert close(m.daly_interval_s(200, 50), 50), "Daly must return M when delta >= 2M"
        return f"Young {y:.0f} s, Daly {d:.0f} s"

    def a3() -> str:
        t = m.choose_interval_s(1.188125, 172800, 18.486, 17.4)
        assert close(t, 643.8), f"expected 37 steps = 643.8 s, got {t}"
        t2 = m.choose_interval_s(0.001, 86400, 30.0, 17.4)
        assert close(t2, 34.8), f"floor at in-flight latency then round up to steps: expected 34.8, got {t2}"
        return "Young floored at completion latency, rounded up to whole steps"

    expected_timings = {
        "sync_pfs": dict(delta=17.8333, blocking=17.8333, L_soft=17.8333, L_hard=17.8333,
                         load_soft=8.1667, load_hard=8.1667, pfs_every=1),
        "async_pfs": dict(delta=1.18813, blocking=0.65313, L_soft=18.4865, L_hard=18.4865,
                          load_soft=8.1667, load_hard=8.1667, pfs_every=1),
        "sync_local_drain": dict(delta=3.08375, blocking=2.59375, L_soft=2.59375, L_hard=20.4271,
                                 load_soft=0.63802, load_hard=8.1667, pfs_every=1),
        "async_two_level": dict(delta=0.78394, blocking=0.65313, L_soft=3.24688, L_hard=21.0802,
                                load_soft=0.63802, load_hard=8.1667, pfs_every=5),
    }

    def a4() -> str:
        for strat, exp in expected_timings.items():
            got = m.strategy_timings(cfg, strat)
            for k, v in exp.items():
                assert k in got, f"{strat}: missing key {k!r}"
                assert close(got[k], v), f"{strat}.{k}: expected {v}, got {got[k]:.5f}"
        return "all four strategies' blocking/delta/completion/load times match"

    def a5() -> str:
        r = m.plan_strategy(cfg, "sync_pfs", 1800.0)
        assert close(r["overhead_pct"], 0.99074), f"overhead_pct expected 0.991, got {r['overhead_pct']:.4f}"
        assert close(r["rpo_max_s"], 1817.83), f"rpo_max_s expected 1817.8, got {r['rpo_max_s']:.1f}"
        assert close(r["ttr_expected_s"], 904.167), f"ttr_expected_s expected 904.2, got {r['ttr_expected_s']:.1f}"
        assert close(r["lost_gpu_h_day"], 125.653), f"lost_gpu_h_day expected 125.7, got {r['lost_gpu_h_day']:.2f}"
        r2 = m.plan_strategy(cfg, "async_pfs", 1800.0)
        assert close(r2["lost_gpu_h_day"], 68.861), f"async @1800 s lost_gpu_h_day expected 68.9, got {r2['lost_gpu_h_day']:.2f}"
        return "sync @30 min: 0.99 % overhead, 125.7 GPU-h/day; async @30 min: 68.9 GPU-h/day"

    def a6() -> str:
        df = m.compare_strategies(cfg)
        assert list(df.index) == ["async_pfs", "async_two_level", "sync_local_drain", "sync_pfs"], \
            f"ranking by lost_gpu_h_day wrong: {list(df.index)}"
        exp = {"async_pfs": (643.8, 55.589), "async_two_level": (522.0, 65.712),
               "sync_local_drain": (1044.0, 69.041), "sync_pfs": (2488.2, 121.052)}
        for s, (tau, lost) in exp.items():
            assert close(df.loc[s, "interval_s"], tau), f"{s}: interval {df.loc[s, 'interval_s']} != {tau}"
            assert close(df.loc[s, "lost_gpu_h_day"], lost), f"{s}: lost {df.loc[s, 'lost_gpu_h_day']:.2f} != {lost}"
        assert close(df.loc["async_two_level", "rpo_max_s"], 2631.08), "two-level RPO_max must include k*tau"
        return "async_pfs best at 37-step interval (55.6 GPU-h/day); two-level pays for its k*tau RPO"

    for n, f in [("A1 size + transfer time", a1), ("A2 Young/Daly interval", a2),
                 ("A3 interval selection", a3), ("A4 strategy timings", a4),
                 ("A5 fixed-interval plan", a5), ("A6 strategy comparison", a6)]:
        c.run(n, f)

    # ------------------------------------------------------------------ Part B: I/O analyzer
    def b1() -> str:
        df = m.load_trace(DATA / "io_trace.csv")
        p = m.latency_percentiles(df)
        for op in ("open", "read", "close"):
            v = raw.loc[raw.op == op, "lat_us"].to_numpy()
            for col, q in (("p50", 50), ("p99", 99), ("p999", 99.9)):
                assert close(p.loc[op, col], np.percentile(v, q)), f"{op} {col} wrong"
        return f"open p50 {p.loc['open', 'p50']/1e3:.1f} ms, read p99.9 {p.loc['read', 'p999']/1e3:.0f} ms"

    def b2() -> str:
        prof = m.window_profile(raw, 1.0)
        assert len(prof) == 19, f"expected 19 one-second windows, got {len(prof)}"
        cls = list(prof["cls"])
        exp = ["metadata"] * 6 + ["idle"] + ["bandwidth"] * 12
        assert cls == exp, f"window classes wrong: {cls}"
        assert close(prof.loc[0.0, "meta_time_share"], 0.8893, rel=5e-3), "meta_time_share window 0 wrong"
        assert close(prof.loc[9.0, "read_GBps"], 7.751, rel=5e-3), "read_GBps window 9 wrong"
        return "0-6 s metadata-bound (~0.2 GB/s), 7-19 s bandwidth-bound (~7.6 GB/s)"

    def b3() -> str:
        ph = m.phases(m.window_profile(raw, 1.0))
        exp = [(0.0, 6.0, "metadata"), (6.0, 7.0, "idle"), (7.0, 19.0, "bandwidth")]
        assert [(float(a), float(b), cl) for a, b, cl in ph] == exp, f"phases wrong: {ph}"
        return "3 phases"

    def b4() -> str:
        dw = m.degraded_windows(m.window_profile(raw, 1.0))
        assert [float(x) for x in dw] == [13.0, 14.0, 15.0, 16.0], f"degraded windows wrong: {dw}"
        return "read p99 inflated 13-17 s (write-burst interference)"

    def b5() -> str:
        st = m.slow_targets(raw)
        assert list(st) == [5], f"slow targets wrong: {st}"
        return "storage target 5 is slow"

    def b6() -> str:
        f = m.parse_fio(DATA / "fio_nvme_acceptance.json")
        assert len(f) == 16, f"expected 16 jobs, got {len(f)}"
        assert ((f["littles_qd"] - f["iodepth"]).abs() / f["iodepth"] < 0.05).all(), "Little's law QD wrong"
        r = f[(f.device == "/dev/nvme2n1") & (f.rw == "write")].iloc[0]
        assert close(r["bw_GBps"], 1.62, rel=1e-2), f"nvme2 write bw expected 1.62 GB/s, got {r['bw_GBps']}"
        o = m.fio_outliers(f)
        exp = {("/dev/nvme2n1", "LOW_BANDWIDTH"), ("/dev/nvme5n1", "TAIL_LATENCY")}
        assert set(o) == exp, f"fio outliers wrong: {o}"
        return "nvme2 low write bandwidth; nvme5 p99.9 tail outlier"

    for n, f in [("B1 latency percentiles", b1), ("B2 window classification", b2),
                 ("B3 phase segmentation", b3), ("B4 interference windows", b4),
                 ("B5 slow storage target", b5), ("B6 fio acceptance parse", b6)]:
        c.run(n, f)

    # ------------------------------------------------------------------ Part C: validator
    store = DATA / "checkpoints"

    def c1() -> str:
        a = m.audit_store(store)
        exp = {"step_000900": [], "step_001200": ["SIZE_MISMATCH"],
               "step_001500": ["CHECKSUM_MISMATCH"], "step_001800": [],
               "step_002100": ["MISSING_SHARD"], "step_002400": ["MANIFEST_HASH_MISMATCH"],
               "step_002700": ["NO_COMMIT"]}
        assert {k: list(v) for k, v in a.items()} == exp, f"audit wrong: {a}"
        return "5 planted defects classified"

    def c2() -> str:
        latest = (store / "latest").read_text().strip()
        sel = m.select_latest_valid(store)
        assert sel == "step_001800", f"expected step_001800, got {sel} (pointer says {latest})"
        return f"restore from {sel}, not the '{latest}' pointer"

    def c3() -> str:
        with tempfile.TemporaryDirectory() as td:
            src = store / "step_000900"
            d1 = Path(td) / "step_000001"
            shutil.copytree(src, d1)
            assert list(m.validate_checkpoint(d1)) == [], "pristine copy must be valid"
            man = json.loads((d1 / "manifest.json").read_bytes())
            man["shards"] = man["shards"][:-1]                       # drop rank 7 from manifest
            mb = json.dumps(man, sort_keys=True, separators=(",", ":")).encode()
            (d1 / "manifest.json").write_bytes(mb)
            (d1 / "COMMIT").write_text(hashlib.sha256(mb).hexdigest())
            got = list(m.validate_checkpoint(d1))
            assert got == ["WORLD_SIZE_MISMATCH"], f"rank coverage: expected WORLD_SIZE_MISMATCH, got {got}"
            d2 = Path(td) / "step_000002"
            shutil.copytree(src, d2)
            (d2 / "manifest.json").write_text("{truncated", encoding="utf-8")
            got = list(m.validate_checkpoint(d2))
            assert got == ["BAD_MANIFEST"], f"expected ['BAD_MANIFEST'], got {got}"
        return "unseen defects (rank coverage, truncated manifest) detected"

    for n, f in [("C1 audit checkpoint store", c1), ("C2 select latest valid", c2),
                 ("C3 validator on unseen defects", c3)]:
        c.run(n, f)

    width = max(len(n) for _, n, _ in c.results)
    for status, name, msg in c.results:
        print(f"{status:4s}  {name:<{width}}  {msg}")
    n_pass = sum(s == "PASS" for s, _, _ in c.results)
    print(f"\n{n_pass}/{len(c.results)} checks passed ({args.impl})")
    return 0 if n_pass == len(c.results) else 1


if __name__ == "__main__":
    sys.exit(main())
