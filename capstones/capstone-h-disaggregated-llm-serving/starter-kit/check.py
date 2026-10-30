#!/usr/bin/env python3
"""Checker for the Capstone H starter kit (disaggregated LLM serving).

Usage:
    python check.py                    # check your starter/serve.py (default)
    python check.py --impl solution    # instructor: check ../instructor/reference/serve.py

Contract (docs/LAB_STANDARDS.md §4): one line per check (PASS/FAIL/TODO/SKIP), never a traceback,
exit 0 only when every check passes or is skipped. MODELED + SIMULATED only, no network, < 60 s.
"""
from __future__ import annotations

import argparse
import filecmp
import importlib.util
import math
import subprocess
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Callable

HERE = Path(__file__).resolve().parent
MODULE = "serve"
DATA = HERE / "data"
sys.path.insert(0, str(HERE))
from sim import serving_sim  # noqa: E402  (given simulator)

RDMA_5P2D = {"kind": "disaggregated", "prefill": 5, "decode": 2, "link_GBps": 360.0, "link_overhead_s": 5e-5}


class Skip(Exception):
    """A check that cannot run in this copy (e.g. the instructor-only generator is absent)."""


def load(impl: str) -> ModuleType | None:
    path = (HERE / "starter" / f"{MODULE}.py") if impl == "starter" else (
        HERE.parent / "instructor" / "reference" / f"{MODULE}.py")
    if not path.exists():
        print(f"Implementation not found: {path}")
        if impl == "solution":
            print("(The instructor/ folder is removed from student releases; use --impl starter.)")
        return None
    spec = importlib.util.spec_from_file_location(f"{MODULE}_{impl}", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    try:
        spec.loader.exec_module(mod)
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL  import -- {type(exc).__name__}: {exc}")
        return None
    return mod


class Ctx:
    def __init__(self, m: ModuleType) -> None:
        self.m = m
        self.d = m.load_dataset(DATA)
        self.h100 = m.hw_profile(self.d["hardware"], "h100-class")
        self.trace = self.d["trace"].to_dict("records")


def close(a: float, b: float, rel: float = 1e-3) -> bool:
    return abs(a - b) <= rel * max(abs(b), 1e-12)


def c_data(_: Ctx) -> str:
    if not (HERE / "tools" / "generate_data.py").exists():
        raise Skip("generator is instructor copy only (tools/ absent); data/ used as shipped")
    with tempfile.TemporaryDirectory() as tmp:
        proc = subprocess.run([sys.executable, str(HERE / "tools" / "generate_data.py"), "--out", tmp],
                              capture_output=True, text=True, timeout=60)
        assert proc.returncode == 0, f"generator failed: {proc.stderr.strip()[-200:]}"
        files = sorted(p.name for p in DATA.iterdir() if p.is_file())
        _, mismatch, errors = filecmp.cmpfiles(DATA, tmp, files, shallow=False)
        assert not mismatch and not errors, f"regenerated files differ: {mismatch + errors}"
    return f"{len(files)} files byte-identical on regeneration"


def c_kv(c: Ctx) -> str:
    assert c.m.kv_cache_bytes(1) == 327_680, f"1 token -> {c.m.kv_cache_bytes(1)} B"
    assert c.m.kv_cache_bytes(2048) == 671_088_640 and c.m.kv_cache_bytes(4096) == 1_342_177_280
    return "327,680 B/token; 2,048 tokens = 671 MB; 4,096 tokens = 1.34 GB"


def c_links(c: Ctx) -> str:
    rows = {r["name"]: r for r in c.m.link_capacity(c.d["links"])}
    assert close(rows["rdma-400g-x8"]["GBps"], 360.0) and close(rows["rdma-400g-x1"]["GBps"], 45.0) \
        and close(rows["tcp-200g-x2"]["GBps"], 30.0) and close(rows["tcp-200g-x1-ch15"]["GBps"], 12.5), \
        {k: v["GBps"] for k, v in rows.items()}
    bad = [k for k, v in rows.items() if not v["valid"]]
    assert bad == ["rdma-400g-x8-vendor-sheet"], f"invalid rows: {bad} (look at the unit column)"
    return "360 / 45 / 30 / 12.5 GB/s achievable; vendor-sheet row rejected (GB/s vs Gb/s)"


def c_roofline(c: Ctx) -> str:
    h = c.h100
    for t in (512, 2048, 32768):
        assert close(c.m.prefill_time_s(t, h), serving_sim.prefill_s(t, h), 1e-6), f"prefill({t})"
    for b, ctx in ((1, 2000), (64, 64 * 2600), (256, 256 * 2600)):
        assert close(c.m.decode_step_time_s(b, ctx, h), serving_sim.decode_step_s(b, ctx, h), 1e-6), f"decode({b})"
    assert c.m.decode_step_time_s(0, 0, h) == 0.0
    assert c.m.kv_capacity_tokens(h) == serving_sim.kv_capacity_tokens(h)
    return (f"prefill 2k {c.m.prefill_time_s(2048, h) * 1e3:.1f} ms, 32k {c.m.prefill_time_s(32768, h):.2f} s; "
            f"decode B=256 {c.m.decode_step_time_s(256, 256 * 2600, h) * 1e3:.1f} ms; KV cap {c.m.kv_capacity_tokens(h):,} tokens")


def c_transfer(c: Ctx) -> str:
    h = c.h100
    pf2, pf32 = serving_sim.prefill_s(2048, h), serving_sim.prefill_s(32768, h)
    cases = [((2048, 360.0, 5e-5, pf2, True), serving_sim.exposed_transfer_s(2048, 360.0, 5e-5, pf2, True)),
             ((2048, 30.0, 5e-4, pf2, False), serving_sim.exposed_transfer_s(2048, 30.0, 5e-4, pf2, False)),
             ((32768, 30.0, 5e-4, pf32, True), serving_sim.exposed_transfer_s(32768, 30.0, 5e-4, pf32, True))]
    for args, exp in cases:
        got = c.m.kv_transfer_exposed_s(*args)
        assert close(got, exp, 1e-6), f"{args[:2]} pipelined={args[4]}: {got} vs {exp}"
    return "2k RDMA pipelined 0.07 ms; 2k TCP unpipelined 22.9 ms; 32k TCP pipelined 5.0 ms"


def c_sizing(c: Ctx) -> str:
    sz = c.m.size_pools(c.d["trace"], c.h100, c.h100, c.d["slo"], c.d["config"]["rho_max"])
    assert (sz["P"], sz["D"]) == (4, 1), f"P, D = {sz['P']}, {sz['D']}"
    assert close(sz["mean_prefill_s"], 0.09101, 1e-3), f"mean prefill {sz['mean_prefill_s']}"
    assert sz["decode_batch"] == 491, f"decode batch {sz['decode_batch']}"
    assert close(sz["kv_GBps_total"], 23.81, 1e-3), f"KV GB/s {sz['kv_GBps_total']}"
    return f"P=4, D=1 ({sz['gpus']} GPUs); B=491 at {sz['decode_step_s'] * 1e3:.1f} ms/step; KV {sz['kv_GBps_total']:.1f} GB/s"


def c_bottleneck(c: Ctx) -> str:
    sz = c.m.size_pools(c.d["trace"], c.h100, c.h100, c.d["slo"], c.d["config"]["rho_max"])
    u = c.m.utilizations(5, 2, sz, 30.0, sz["mean_output"], 30.0)
    assert u["bottleneck"] == "prefill", f"5P2D over TCP: bottleneck {u}"
    assert close(u["prefill"], 0.5461, 2e-3) and close(u["network_out"], 0.1587, 2e-3) \
        and close(u["network_in"], 0.3969, 2e-3), f"utilisations {u}"
    u1 = c.m.utilizations(5, 1, sz, 30.0, sz["mean_output"], 30.0)
    assert u1["bottleneck"] == "network" and close(u1["network_in"], 0.7937, 2e-3), \
        f"5P1D over TCP: decode-side fan-in must be the bottleneck: {u1}"
    u15 = c.m.utilizations(5, 2, sz, 30.0, sz["mean_output"], 12.5)
    assert u15["bottleneck"] == "network" and u15["network_in"] > 0.9, f"Chapter 15 TCP profile: {u15}"
    pre = [r for r in c.trace if r["arrival_s"] < 115]
    sim = serving_sim.run(pre, {**RDMA_5P2D, "util_window_s": 115.0})
    model = c.m.utilizations(5, 2, sz, len(pre) / 115, sz["mean_output"], 360.0)["prefill"]
    assert abs(sim.util["prefill_window"] - model) / model < 0.05, \
        f"model {model:.3f} vs sim {sim.util['prefill_window']:.3f} over the same 115 s window"
    return (f"5P2D prefill-bound (prefill {u['prefill']:.2f}, TCP fan-in {u['network_in']:.2f}); 5P1D over TCP "
            f"network-bound (fan-in {u1['network_in']:.2f}); Ch15 TCP fan-in {u15['network_in']:.2f}; "
            f"model {model:.3f} vs sim {sim.util['prefill_window']:.3f} (same window)")


def c_admission(c: Ctx) -> str:
    base = serving_sim.summarize(serving_sim.run(c.trace, RDMA_5P2D))
    res = serving_sim.summarize(serving_sim.run(c.trace, RDMA_5P2D, c.m.admission_policy))
    slo = c.d["slo"]
    assert base["ttft_p95_s"] > slo["ttft_p95_s"], "sanity: the burst must break TTFT without admission"
    assert res["ttft_p95_s"] <= slo["ttft_p95_s"], f"TTFT p95 {res['ttft_p95_s']:.3f} s"
    assert res["ttft_long_p95_s"] <= slo["ttft_long_p95_s"], f"long TTFT p95 {res['ttft_long_p95_s']:.3f} s"
    assert res["tpot_p95_s"] <= slo["tpot_p95_s"], f"TPOT p95 {res['tpot_p95_s'] * 1e3:.1f} ms"
    assert res["reject_rate"] <= slo["max_reject_rate"], f"reject rate {res['reject_rate']:.3f}"
    assert res["itl_p99_s"] <= slo["itl_p99_s"], f"ITL p99 {res['itl_p99_s'] * 1e3:.1f} ms"
    assert res["second_gap_p95_s"] <= slo["itl_p99_s"], f"second-token gap p95 {res['second_gap_p95_s'] * 1e3:.1f} ms"
    return (f"TTFT p95 {base['ttft_p95_s']:.2f} s -> {res['ttft_p95_s']:.2f} s; reject {res['reject_rate']:.1%}; "
            f"TPOT p95 {res['tpot_p95_s'] * 1e3:.1f} ms; ITL p99 {res['itl_p99_s'] * 1e3:.1f} ms; "
            f"second-token gap p95 {res['second_gap_p95_s'] * 1e3:.1f} ms")


def c_spec(c: Ctx) -> str:
    g = c.m.speculative_gain(0.8, 4, 0.1)
    assert close(g["tokens_per_target_step"], 3.3616, 1e-4) and close(g["speedup"], 2.40114, 1e-4), g
    ks = (c.m.best_draft_length(0.8, 0.1), c.m.best_draft_length(0.6, 0.1), c.m.best_draft_length(0.9, 0.05))
    assert ks == (6, 3, 8), f"best k {ks}"
    sz = c.m.size_pools(c.d["trace"], c.h100, c.h100, c.d["slo"], c.d["config"]["rho_max"])
    B = sz["decode_batch"]
    ctx = B * (sz["mean_prompt"] + sz["mean_output"] / 2)
    op = c.m.speculative_gain_at_batch(0.8, 4, 0.1, B, ctx, c.h100)
    assert close(op["speedup"], 1.2527, 2e-3) and op["verify_step_s"] > op["plain_step_s"], \
        f"at B={B} verification is compute-bound: {op}"
    one = c.m.speculative_gain_at_batch(0.8, 4, 0.1, 1, sz["mean_prompt"], c.h100)
    assert close(one["speedup"], g["speedup"], 1e-3), "at batch 1 the batch-aware model must reduce to the simple one"
    return (f"simple model 2.40x (k=4); at the operating point B={B}: {op['speedup']:.2f}x "
            f"(verify {op['verify_step_s'] * 1e3:.1f} ms vs plain {op['plain_step_s'] * 1e3:.1f} ms); best k 6 / 3 / 8")


def c_qos(c: Ctx) -> str:
    f = c.m.audit_qos(c.d["qos"])
    exp = ["kv_dscp_collision", "kv_shares_lossless_training_tc", "kv_unencrypted_across_boundary"]
    assert f == exp, f"findings {f}"
    fixed = {**c.d["qos"], "kv_encryption": "ipsec",
             "classes": [x if x["name"] != "kv-transfer" else {**x, "dscp": 34, "tc": 4} for x in c.d["qos"]["classes"]]}
    assert c.m.audit_qos(fixed) == [], f"fixed design still flagged: {c.m.audit_qos(fixed)}"
    return "3 findings on the proposal; corrected design is clean"


def c_cost(c: Ctx) -> str:
    v = c.m.cost_per_million_tokens(56, 4.0, 8939.5)
    assert close(v, 56 * 4.0 / (8939.5 * 3600) * 1e6, 1e-9), f"{v}"
    return f"5P2D at 8,940 tok/s: ${v:.2f} per million output tokens"


CHECKS: list[tuple[str, Callable[[Ctx], str]]] = [
    ("dataset deterministic", c_data),
    ("T1 KV-cache size", c_kv),
    ("T2 link normalisation", c_links),
    ("T3 roofline prefill/decode", c_roofline),
    ("T3 KV transfer exposure", c_transfer),
    ("T4 pool sizing", c_sizing),
    ("T4 bottleneck at target load", c_bottleneck),
    ("T5 admission control", c_admission),
    ("T6 speculative decoding", c_spec),
    ("T7 QoS / isolation audit", c_qos),
    ("T8 cost model", c_cost),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--impl", choices=["starter", "solution"], default="starter")
    args = ap.parse_args()
    mod = load(args.impl)
    if mod is None:
        return 2
    try:
        ctx = Ctx(mod)
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL  load_dataset -- {type(exc).__name__}: {exc}")
        return 1
    passed = 0
    for name, fn in CHECKS:
        try:
            detail = fn(ctx)
            print(f"PASS  {name} -- {detail}")
            passed += 1
        except Skip as exc:
            print(f"SKIP  {name} -- {exc}")
            passed += 1
        except NotImplementedError as exc:
            print(f"TODO  {name} -- not implemented: {exc}")
        except AssertionError as exc:
            print(f"FAIL  {name} -- {exc}")
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL  {name} -- {type(exc).__name__}: {exc}")
    print(f"\n{passed}/{len(CHECKS)} checks passed ({args.impl})")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
