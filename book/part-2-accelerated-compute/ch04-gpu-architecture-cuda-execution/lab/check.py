#!/usr/bin/env python3
"""Checker for the Chapter 4 lab (training-step trace analysis).

Usage:
    python check.py                    # check your starter/trace_analysis.py
    python check.py --impl solution    # check the instructor reference (not in student release)

Prints one PASS / FAIL / TODO line per check and exits 0 only if every check passes.
Expected values are computed independently here or are hand-derived constants; the checker
never calls the reference solution.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Callable

import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
MODULE = "trace_analysis.py"


def load_impl(impl: str):
    path = (HERE / "starter" / MODULE) if impl == "starter" else (HERE.parent / "solutions" / "lab" / MODULE)
    if not path.exists():
        print(f"Implementation not found: {path}\n(The solutions folder is removed from the student release.)")
        sys.exit(2)
    spec = importlib.util.spec_from_file_location(f"ch04_{impl}_trace_analysis", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod  # required for @dataclass in the loaded module
    try:
        assert spec.loader is not None
        spec.loader.exec_module(mod)
    except Exception as exc:  # noqa: BLE001 — a learner syntax/import error must not crash the checker
        print(f"FAIL import — could not import {path.name}: {type(exc).__name__}: {exc}")
        sys.exit(1)
    return mod


# ---- independent reference computations (deliberately simple, not the solution) -------
def _union(iv):
    tot, cur_s, cur_e = 0, None, None
    for s, e in sorted(iv):
        if cur_e is None or s > cur_e:
            if cur_e is not None:
                tot += cur_e - cur_s
            cur_s, cur_e = s, e
        else:
            cur_e = max(cur_e, e)
    return tot + ((cur_e - cur_s) if cur_e is not None else 0)


def _windows():
    n = pd.read_csv(DATA / "nvtx_ranges.csv")
    st = n[n["name"].str.startswith("train_step_")].sort_values("start_ns")
    return [(r["name"], int(r["start_ns"]), int(r["end_ns"])) for _, r in st.iterrows()]


def _clipped(df, s, e):
    return [(max(a, s), min(b, e)) for a, b in zip(df["start_ns"], df["end_ns"]) if b > s and a < e]


GPU = pd.read_csv(DATA / "gpu_trace.csv", keep_default_na=False)
API = pd.read_csv(DATA / "cuda_api_trace.csv")


def close(a: float, b: float, tol: float) -> bool:
    return abs(a - b) <= tol


# ---- checks ---------------------------------------------------------------------------
def c_merge(m):
    assert m.merge_intervals([(0, 10), (5, 20), (30, 40)]) == [(0, 20), (30, 40)], "overlap merge wrong"
    assert m.merge_intervals([(10, 12), (0, 10)]) == [(0, 12)], "touching intervals should merge"
    assert m.merge_intervals([(5, 5), (1, 2)]) == [(1, 2)], "empty interval should be dropped"
    return "overlapping, touching and empty intervals handled"


def c_busy(m):
    assert m.busy_ns([(0, 100), (50, 150), (200, 210)]) == 160, "double counting overlaps?"
    return "union length correct (no double counting across streams)"


def c_steps(m):
    w = m.step_windows(pd.read_csv(DATA / "nvtx_ranges.csv"))
    exp = _windows()
    assert [tuple(x) for x in w] == exp, f"expected {exp}, got {w}"
    return f"{len(w)} step windows"


def c_util(m):
    name, s, e = _windows()[0]
    u = m.utilization(GPU, s, e)
    k = GPU[GPU["kind"] == "kernel"]
    exp_any = _union(_clipped(GPU, s, e)) / (e - s)
    exp_k = _union(_clipped(k, s, e)) / (e - s)
    assert close(u["busy_any_frac"], exp_any, 1e-6), f"busy_any_frac {u['busy_any_frac']:.4f} != {exp_any:.4f}"
    assert close(u["busy_kernel_frac"], exp_k, 1e-6), f"busy_kernel_frac {u['busy_kernel_frac']:.4f} != {exp_k:.4f}"
    return f"{name}: busy(any) {exp_any:.1%}, busy(kernel) {exp_k:.1%}"


def c_overlap(m):
    name, s, e = _windows()[0]
    o = m.copy_compute_overlap(GPU, s, e)
    c = GPU[GPU["kind"] == "memcpy"]
    copy_ns = _union(_clipped(c, s, e))
    assert o["copy_ns"] == copy_ns, f"copy_ns {o['copy_ns']} != {copy_ns}"
    k = GPU[GPU["kind"] == "kernel"]
    # |C ∩ K| = |C| + |K| - |C ∪ K|  (inclusion-exclusion on interval unions)
    exp_ov = copy_ns + _union(_clipped(k, s, e)) - _union(_clipped(c, s, e) + _clipped(k, s, e))
    assert o["overlapped_ns"] == exp_ov, f"overlapped_ns {o['overlapped_ns']} != {exp_ov}"
    assert 0.05 < o["overlap_frac"] < 0.25, "only the pinned side-stream prefetch should overlap compute"
    return f"{name}: {o['overlap_frac']:.1%} of copy time overlapped with compute"


def c_gaps(m):
    totals = {"host_sync": 0, "launch_bound": 0, "dependency": 0}
    for _, s, e in _windows():
        g = m.find_gaps(GPU, API, s, e, 2_000)
        for col in ("gap_start_ns", "gap_end_ns", "gap_ns", "next_id", "next_name", "cause"):
            assert col in g.columns, f"missing column {col}"
        assert (g["gap_ns"] >= 2_000).all(), "gaps below min_gap_ns returned"
        assert ((g["gap_end_ns"] - g["gap_start_ns"]) == g["gap_ns"]).all(), "gap_ns inconsistent"
        vc = g["cause"].value_counts()
        # Planted per step: 12 debug-hook .item() + 1 loss.item() + 2 blocking pageable copies.
        assert vc.get("host_sync", 0) == 15, f"expected 15 host_sync gaps per step, got {vc.get('host_sync', 0)}"
        assert vc.get("launch_bound", 0) >= 590, f"expected ~600 launch_bound gaps per step, got {vc.get('launch_bound', 0)}"
        # Planted: one host-callback wait per step (work queued long before the GPU went idle).
        assert vc.get("dependency", 0) == 1, f"expected 1 dependency gap per step, got {vc.get('dependency', 0)}"
        for k in totals:
            totals[k] += int(vc.get(k, 0))
    assert totals["dependency"] == 2, f"expected 2 dependency gaps over 2 steps, got {totals['dependency']}"
    return f"causes over 2 steps: {totals}"


def c_copies(m):
    t = m.copy_table(GPU)
    assert len(t) == int((GPU["kind"] == "memcpy").sum()), "one row per memcpy expected"
    big = t[t["bytes"] >= 1 << 20]
    pg = big[big["host_mem"] == "pageable"]
    pn = big[big["host_mem"] == "pinned"]
    assert len(pg) == 4 and len(pn) == 2, f"expected 4 pageable + 2 pinned large copies, got {len(pg)} + {len(pn)}"
    exp = (pg["bytes"] / pg["dur_ns"]).to_numpy()
    assert all(close(a, b, 1e-9) for a, b in zip(pg["gbps"], exp)), "gbps must be bytes/dur_ns"
    assert pg["gbps"].max() < 15 and pn["gbps"].min() > 40, "pageable vs pinned bandwidth looks wrong"
    return f"pageable ≈ {pg['gbps'].mean():.1f} GB/s vs pinned ≈ {pn['gbps'].mean():.1f} GB/s"


def c_occupancy(m):
    import json
    dev = json.loads((DATA / "device.json").read_text(encoding="utf-8"))
    cases = [  # (block, regs, smem) -> (occupancy, limiter); hand-derived in solutions key
        ((256, 168, 16_384), (0.125, "registers")),
        ((384, 168, 213_000), (0.1875, "registers")),
        ((128, 255, 163_840), (0.0625, "shared_memory")),
        ((256, 32, 0), (1.0, "warps")),
        ((32, 16, 0), (0.5, "blocks")),
        ((1024, 64, 0), (0.5, "registers")),
        ((32, 96, 0), (0.3125, "registers")),  # 3,072 regs/warp -> 21 warps -> 20 after granularity 4 -> 20 blocks
    ]
    for args, (occ, lim) in cases:
        r = m.theoretical_occupancy(*args, dev)
        assert close(r["occupancy"], occ, 1e-9) and r["limiter"] == lim, \
            f"{args}: expected {occ:.4f}/{lim}, got {r['occupancy']:.4f}/{r['limiter']}"
    return f"{len(cases)} launch configurations match hand calculation"


def c_kernels(m):
    import json
    dev = json.loads((DATA / "device.json").read_text(encoding="utf-8"))
    ks = m.kernel_summary(GPU, dev).set_index("name")
    ln = ks.loc["layernorm_bwd_fused_kernel"]
    assert close(ln["occupancy"], 0.125, 1e-9) and ln["bound"] == "memory", "layernorm_bwd row wrong"
    k = GPU[GPU["name"] == "layernorm_bwd_fused_kernel"]
    exp = k["dram_bytes"].sum() / ((k["end_ns"] - k["start_ns"]).sum() / 1e9) / dev["hbm_bytes_per_s"]
    assert close(ln["roof_frac"], exp, 1e-6), f"roof_frac {ln['roof_frac']:.3f} != {exp:.3f}"
    g = ks.loc["sm90_xmma_gemm_bf16bf16_bf16f32_nt_128x256_cublas"]
    assert g["bound"] == "compute" and g["roof_frac"] > 0.5, "GEMM should be compute-bound near its roof"
    assert close(ks["time_share"].sum(), 1.0, 1e-6), "time_share must sum to 1"
    return f"layernorm_bwd at {ln['roof_frac']:.0%} of HBM roof; GEMM at {g['roof_frac']:.0%} of BF16 roof"


def c_findings(m):
    a = m.analyze(DATA)
    codes = sorted(f["code"] for f in a["findings"])
    assert codes == sorted(["PAGEABLE_H2D", "EXCESS_SYNC", "LAUNCH_BOUND", "STREAM_DEPENDENCY", "LOW_OCCUPANCY"]), f"codes {codes}"
    low = [f.get("kernel") for f in a["findings"] if f["code"] == "LOW_OCCUPANCY"]
    assert low == ["layernorm_bwd_fused_kernel"], f"LOW_OCCUPANCY should name only layernorm_bwd_fused_kernel, got {low}"
    assert any("gemm" in n for n in a["low_occupancy_by_design"]), "GEMMs should be 'low occupancy by design'"
    assert "layernorm_bwd_fused_kernel" not in a["low_occupancy_by_design"]
    pg = next(f for f in a["findings"] if f["code"] == "PAGEABLE_H2D")
    c = GPU[(GPU["kind"] == "memcpy") & (GPU["src_mem"] == "pageable") & (GPU["bytes"] >= 1 << 20)]
    exp = (c["end_ns"] - c["start_ns"]).sum() / 1e6 / 2
    assert close(pg["est_saving_ms_per_step"], exp, 0.05), f"PAGEABLE_H2D saving {pg['est_saving_ms_per_step']:.2f} != {exp:.2f}"
    for f in a["findings"]:
        assert f["evidence"] and f["recommendation"] and f["est_saving_ms_per_step"] > 0, f"incomplete finding {f['code']}"
    assert len(a["steps"]) == 2
    return "5 planted problems found; tensor-core kernels correctly not flagged"


def c_report(m):
    rep = m.render_report(m.analyze(DATA))
    for code in ("PAGEABLE_H2D", "EXCESS_SYNC", "LAUNCH_BOUND", "STREAM_DEPENDENCY", "LOW_OCCUPANCY"):
        assert code in rep, f"{code} missing from report"
    return "report renders with all findings"


CHECKS: list[tuple[str, Callable]] = [
    ("merge_intervals", c_merge), ("busy_ns", c_busy), ("step_windows", c_steps),
    ("utilization", c_util), ("copy_compute_overlap", c_overlap), ("find_gaps", c_gaps),
    ("copy_table", c_copies), ("theoretical_occupancy", c_occupancy), ("kernel_summary", c_kernels),
    ("analyze_findings", c_findings), ("render_report", c_report),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--impl", choices=["starter", "solution"], default="starter")
    args = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    mod = load_impl(args.impl)
    passed = 0
    for name, fn in CHECKS:
        try:
            msg = fn(mod)
            print(f"PASS {name} — {msg}")
            passed += 1
        except NotImplementedError:
            print(f"TODO {name} — not implemented yet")
        except AssertionError as exc:
            print(f"FAIL {name} — {exc}")
        except Exception as exc:  # noqa: BLE001 — report, never crash
            print(f"FAIL {name} — {type(exc).__name__}: {exc}")
    print(f"\n{passed}/{len(CHECKS)} checks passed ({args.impl})")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
