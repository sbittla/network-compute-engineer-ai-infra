#!/usr/bin/env python3
"""Chapter 15 lab checker.

    python check.py                    # check lab/starter/serving_lab.py (your work)
    python check.py --impl solution    # check the reference solution (instructors)

Prints one line per check (PASS / FAIL / TODO) and exits 0 only if every check passes.
Pure Python, no hardware, no network; runs in a few seconds from any working directory.
"""
from __future__ import annotations

import argparse
import importlib.util
import math
import sys
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
IMPLS = {
    "starter": HERE / "starter" / "serving_lab.py",
    "solution": HERE.parent / "solutions" / "lab" / "serving_lab.py",
}


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("serving_lab_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def close(a: float, b: float, rel: float = 1e-3, abs_: float = 1e-9) -> bool:
    return math.isclose(float(a), float(b), rel_tol=rel, abs_tol=abs_)


class Check(Exception):
    """Raised with a short reason when a check fails."""


def expect(cond: bool, reason: str) -> None:
    if not cond:
        raise Check(reason)


# ------------------------------------------------------------------------------------------
# Independent reference computations on the trace (kept deliberately simple)
# ------------------------------------------------------------------------------------------

def ref_trace():
    df = pd.read_csv(DATA / "requests.csv")
    ttft = df["first_token_s"] - df["arrival_s"]
    tpot = (df["finish_s"] - df["first_token_s"]) / (df["output_tokens"] - 1)
    tpot[df["output_tokens"] < 2] = np.nan
    return df, ttft, tpot


def build_checks(m):
    cfg_path = DATA / "configs.yaml"
    checks = []

    def add(name):
        def deco(fn):
            checks.append((name, fn))
            return fn
        return deco

    # ---------------- Part A ----------------
    @add("A1 kv_bytes_per_token (W-INFER BF16 and FP8 KV)")
    def _():
        v = m.kv_bytes_per_token(80, 8, 128, 2)
        expect(v == 327_680, f"BF16 expected 327680 B/token, got {v}")
        v = m.kv_bytes_per_token(80, 8, 128, 1)
        expect(v == 163_840, f"FP8 expected 163840 B/token, got {v}")

    @add("A2 kv_budget_bytes (TP=8 BF16, TP=4 FP8, TP=2 FP8)")
    def _():
        for args, want in [((8, 80e9, 0.9, 140e9, 2e9), 420e9), ((4, 80e9, 0.9, 70e9, 2e9), 210e9),
                           ((2, 80e9, 0.9, 70e9, 2e9), 70e9), ((1, 80e9, 0.9, 140e9, 2e9), 0.0)]:
            got = m.kv_budget_bytes(*args)
            expect(close(got, want, abs_=1.0), f"{args} expected {want:.3e}, got {got:.3e}")

    @add("A3 max_concurrent_sequences (paged, 16-token blocks)")
    def _():
        for args, want in [((420e9, 327_680, 4096), 312), ((210e9, 327_680, 4096), 156),
                           ((70e9, 327_680, 4096), 52), ((70e9, 327_680, 4097), 51)]:
            got = m.max_concurrent_sequences(*args)
            expect(got == want, f"{args} expected {want}, got {got}")

    @add("A4 prefill_time_s (2k prompt, TP=8 BF16, 40% MFU)")
    def _():
        got = m.prefill_time_s(70e9, 2048, 8, 989e12, 0.40)
        expect(close(got, 0.090597, rel=1e-3), f"expected ~0.0906 s, got {got:.5f}")

    @add("A5 decode step lower bound and tokens/s (TP=8 BF16, B=32, ctx=2176)")
    def _():
        t = m.decode_step_time_s(140e9, 32, 2176, 327_680, 8, 3.35e12)
        expect(close(t, 162.8168e9 / 26.8e12, rel=1e-4), f"expected ~6.075 ms, got {t * 1e3:.3f} ms")
        tps = m.decode_tokens_per_s(140e9, 32, 2176, 327_680, 8, 3.35e12)
        expect(close(tps, 32 / t, rel=1e-6), f"tokens/s should equal batch/step, got {tps:.1f}")
        t2 = m.decode_step_time_s(140e9, 32, 2176, 327_680, 8, 3.35e12, 0.7, 0.003)
        expect(close(t2, 0.011679, rel=1e-3), f"with eff 0.7 + 3 ms overhead expected ~11.68 ms, got {t2 * 1e3:.3f}")

    @add("A6 compare_serving_configs + recommendation per objective")
    def _():
        cfg = m.load_config(cfg_path)
        t = m.compare_serving_configs(cfg).set_index("name")
        expect(int(t.loc["L-tp8-bf16", "max_seqs"]) == 312, "L max_seqs should be 312")
        expect(int(t.loc["T-tp4-fp8", "batch"]) == 128, "T batch should be min(128, 156) = 128")
        expect(close(t.loc["L-tp8-bf16", "tpot_s"], 0.011679, rel=2e-3), "L tpot ~11.68 ms")
        expect(close(t.loc["T-tp4-fp8", "tpot_s"], 0.020193, rel=2e-3), "T tpot ~20.19 ms")
        expect(close(t.loc["T-tp4-fp8", "tokens_per_s_per_node"], 12_678, rel=3e-3), "T ~12.7k tok/s/node")
        tt = t.reset_index()
        expect(m.recommend_config(tt, "latency") == "L-tp8-bf16", "latency objective should pick L-tp8-bf16")
        expect(m.recommend_config(tt, "throughput") == "T-tp4-fp8", "throughput objective should pick T-tp4-fp8")

    # ---------------- Part B ----------------
    df, ttft, tpot = ref_trace()

    @add("B1 request_metrics (queue, prefill, TTFT, TPOT, e2e)")
    def _():
        out = m.request_metrics(m.load_requests(DATA / "requests.csv"))
        for col in ["queue_s", "prefill_s", "ttft_s", "tpot_s", "e2e_s"]:
            expect(col in out.columns, f"missing column {col}")
        expect(np.allclose(out["ttft_s"], ttft), "ttft_s mismatch")
        expect(np.allclose(out["tpot_s"].fillna(-1), tpot.fillna(-1)), "tpot_s mismatch (NaN when output < 2?)")
        expect(np.allclose(out["queue_s"] + out["prefill_s"], out["ttft_s"]), "queue + prefill must equal TTFT")

    @add("B2 latency_percentiles (chat TTFT p50/p95/p99)")
    def _():
        p = m.latency_percentiles(range(1, 101), (50, 99.9))
        expect(set(p) == {"p50", "p99.9"}, f"keys should be p50 and p99.9, got {sorted(p)}")
        expect(close(p["p50"], 50.5), f"p50 of 1..100 is 50.5, got {p['p50']}")
        chat = ttft[df["tenant"] == "chat"]
        got = m.latency_percentiles(chat, (50, 95, 99))
        for k, q in [("p50", 50), ("p95", 95), ("p99", 99)]:
            expect(close(got[k], np.percentile(chat, q), rel=1e-6), f"chat TTFT {k} mismatch")

    @add("B3 itl_values_s + ITL tail (sampled token gaps)")
    def _():
        gaps = m.load_token_gaps(DATA / "token_gaps.csv")
        v = np.asarray(m.itl_values_s(gaps))
        ref = np.array([float(x) for s in gaps["itl_ms"] if s for x in s.split(";")]) / 1000
        expect(len(v) == len(ref), f"expected {len(ref)} gaps, got {len(v)}")
        expect(close(np.percentile(v, 99), np.percentile(ref, 99), rel=1e-6), "ITL p99 mismatch (units?)")

    @add("B4 slo_report (attainment, goodput, throughput)")
    def _():
        cfg = m.load_config(cfg_path)
        out = m.slo_report(m.request_metrics(df), cfg["trace"]["slos"], cfg["trace"]["duration_s"])
        lim_ttft = df["tenant"].map({"chat": 0.8, "longctx": 3.0})
        lim_tpot = df["tenant"].map({"chat": 0.05, "longctx": 0.08})
        ok = (ttft <= lim_ttft) & ((tpot <= lim_tpot) | tpot.isna())
        expect(close(out["attainment"], ok.mean(), rel=1e-6), f"attainment expected {ok.mean():.4f}, got {out['attainment']:.4f}")
        expect(close(out["goodput_rps"], ok.sum() / 600, rel=1e-6), "goodput_rps mismatch")
        expect(close(out["throughput_rps"], len(df) / 600, rel=1e-6), "throughput_rps mismatch")
        expect(out["goodput_rps"] < out["throughput_rps"], "goodput must be below throughput on this trace")

    issues_cache = {}

    def issues():
        if "v" not in issues_cache:
            issues_cache["v"] = m.detect_issues(m.request_metrics(df))
        return issues_cache["v"]

    @add("B5 detect queueing collapse under the arrival burst")
    def _():
        q = [i for i in issues() if i["type"] == "queueing_collapse"]
        expect(len(q) == 1, f"expected exactly 1 queueing_collapse episode, got {len(q)}")
        expect(225 <= q[0]["start_s"] <= 255 and q[0]["end_s"] >= 285,
               f"episode {q[0]['start_s']}-{q[0]['end_s']} s does not cover the burst onset")

    @add("B6 detect preemption storm (and do not call it a burst)")
    def _():
        s = [i for i in issues() if i["type"] == "preemption_storm"]
        expect(len(s) == 1, f"expected exactly 1 preemption_storm episode, got {len(s)}")
        expect(420 <= s[0]["start_s"] <= 510, f"storm starts at {s[0]['start_s']} s; expected 420-510 s")
        cs = [i for i in issues() if i["type"] == "capacity_shortfall"]
        expect(not cs, f"KV-pressure queueing misclassified as capacity_shortfall: {cs}")

    @add("B7 detect the slow replica")
    def _():
        r = sorted(i["replica"] for i in issues() if i["type"] == "slow_replica")
        expect(r == ["r3"], f"expected ['r3'], got {r}")

    @add("B8 telemetry_evidence corroborates the diagnoses")
    def _():
        tel = m.load_telemetry(DATA / "replica_telemetry.csv")
        storm = next(i for i in issues() if i["type"] == "preemption_storm")
        burst = next(i for i in issues() if i["type"] == "queueing_collapse")
        es = m.telemetry_evidence(tel, storm["start_s"], storm["end_s"])
        eb = m.telemetry_evidence(tel, burst["start_s"], burst["end_s"])
        base = m.telemetry_evidence(tel, 0, 230)
        expect(es["kv_usage_max_pct"] >= 95, f"storm KV usage max should be >= 95 %, got {es['kv_usage_max_pct']}")
        expect(es["preemptions_delta"] > 0, "storm should show preemption counter increase")
        expect(eb["kv_usage_max_pct"] < 80, "burst episode is not KV-bound (expect < 80 %)")
        expect(eb["waiting_mean"] > 10 * max(base["waiting_mean"], 0.1), "burst waiting queue should dwarf baseline")

    # ---------------- Part C ----------------
    @add("C1 kv_transfer_time_s (2k-token KV over 4x400G RDMA)")
    def _():
        t = m.kv_transfer_time_s(2048 * 327_680, 400, 4, 0.85, 30e-6)
        expect(close(t, 30e-6 + 671_088_640 / 170e9, rel=1e-6), f"expected ~3.98 ms, got {t * 1e3:.3f} ms")

    @add("C2 md1_wait_s")
    def _():
        expect(close(m.md1_wait_s(0.5, 0.1), 0.05), "rho=0.5, s=0.1 -> 0.05 s")
        expect(math.isinf(m.md1_wait_s(1.0, 0.1)), "rho >= 1 must return inf")

    @add("C3 compare_designs (shared vs disaggregated RDMA/TCP) [MODELED]")
    def _():
        t = m.compare_designs(m.load_config(cfg_path)).set_index("design")
        expect(set(t.index) == {"shared", "disagg-rdma", "disagg-tcp"}, f"designs: {list(t.index)}")
        expect(close(t.loc["shared", "tpot_s"], 0.023253, rel=3e-3), f"shared TPOT ~23.3 ms, got {t.loc['shared', 'tpot_s']:.5f}")
        expect(close(t.loc["shared", "itl_worst_s"], 0.10328, rel=3e-3), "shared worst ITL ~103 ms")
        expect(close(t.loc["disagg-rdma", "ttft_s"], 0.15951, rel=3e-3), "disagg (6P+2D) TTFT ~160 ms")
        expect(close(t.loc["disagg-rdma", "agg_kv_Gbps"], 214.75, rel=1e-3), "aggregate KV ~214.7 Gb/s")
        expect(close(t.loc["disagg-rdma", "tpot_s"], 0.017145, rel=3e-3), "disagg (6P+2D) TPOT ~17.1 ms")
        expect(close(t.loc["disagg-tcp", "itl_worst_s"], 0.071817, rel=3e-3), "TCP worst ITL ~71.8 ms")
        expect(close(t.loc["disagg-tcp", "link_util_pct"], 107.37, rel=2e-3), "TCP link util ~107 % (infeasible)")

    @add("C4 speculative decoding expected tokens and speedup")
    def _():
        expect(close(m.speculative_expected_tokens(0.8, 4), 3.3616, rel=1e-6), "alpha=0.8,k=4 -> 3.3616")
        expect(close(m.speculative_expected_tokens(1.0, 4), 5.0), "alpha=1 -> k+1")
        expect(close(m.speculative_speedup(0.8, 4, 0.05), 3.3616 / 1.2, rel=1e-6), "speedup 2.80x")
        expect(m.speculative_speedup(0.5, 8, 0.10) < 1.2, "low alpha + long k should give little or no speedup")

    return checks


def main() -> int:
    ap = argparse.ArgumentParser(description="Chapter 15 lab checker")
    ap.add_argument("--impl", choices=sorted(IMPLS), default="starter")
    args = ap.parse_args()
    try:
        m = load_module(IMPLS[args.impl])
    except Exception as e:  # noqa: BLE001 - report import errors without a traceback dump
        print(f"FAIL import {IMPLS[args.impl].name}: {type(e).__name__}: {e}")
        return 2
    results = {"PASS": 0, "FAIL": 0, "TODO": 0}
    for name, fn in build_checks(m):
        try:
            fn()
            status, why = "PASS", ""
        except NotImplementedError as e:
            status, why = "TODO", str(e)
        except Check as e:
            status, why = "FAIL", str(e)
        except Exception as e:  # noqa: BLE001
            tb = traceback.extract_tb(e.__traceback__)[-1]
            status, why = "FAIL", f"{type(e).__name__}: {e} (line {tb.lineno})"
        results[status] += 1
        print(f"{status:4} {name}" + (f" -- {why}" if why else ""))
    total = sum(results.values())
    print(f"\n{results['PASS']}/{total} passed, {results['FAIL']} failed, {results['TODO']} TODO "
          f"[impl={args.impl}]")
    return 0 if results["PASS"] == total else 1


if __name__ == "__main__":
    sys.exit(main())
