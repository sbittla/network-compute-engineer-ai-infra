#!/usr/bin/env python3
"""Capstone D starter-kit checker — W-INFER capacity model, serving simulator, SLOs and cost.

Usage:
    python check.py                    # check your starter/serving.py (default)
    python check.py --impl solution    # check the instructor reference (instructor edition only)

Prints one line per check (PASS / FAIL / TODO). Exits 0 only when every check passes.
Simulator outputs are [SIMULATED]; randomness lives only in the committed traces (trace_s1 is used here), so results
are deterministic.
"""
from __future__ import annotations

import argparse
import importlib.util
import math
import sys
from pathlib import Path
from types import ModuleType
from typing import Callable

import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
MODULE = "serving"


def load(impl: str) -> ModuleType | None:
    if impl == "solution":
        path = HERE.parent / "instructor" / "reference" / f"{MODULE}.py"
    else:
        path = HERE / "starter" / f"{MODULE}.py"
    if not path.exists():
        print(f"Implementation not found: {path}")
        if impl == "solution":
            print("The instructor reference is not shipped in the student edition.")
        return None
    spec = importlib.util.spec_from_file_location(f"{MODULE}_{impl}", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


CHECKS: list[tuple[str, Callable[[ModuleType], str]]] = []
_C: dict[str, object] = {}


def check(name: str):
    def deco(fn: Callable[[ModuleType], str]):
        CHECKS.append((name, fn))
        return fn
    return deco


def close(a: float, b: float, rel: float = 1e-3) -> bool:
    return abs(a - b) <= rel * max(abs(a), abs(b), 1e-12)


def I(m):  # noqa: E743
    if "I" not in _C:
        _C["I"] = m.load_inputs(DATA)
    return _C["I"]


def run(m, cfg_name: str, scale: float):
    k = f"{cfg_name}@{scale}"
    if k not in _C:
        i = I(m)
        res = m.simulate(i["trace"], i["model"], i["hardware"], i["configs"][cfg_name], rate_scale=scale)
        _C[k] = (res, m.summarize(res, i["slo"]))
    return _C[k]


def trace(rows: list[tuple[str, float, int, int]]) -> pd.DataFrame:
    return pd.DataFrame([{"request_id": r, "arrival_s": a, "prompt_tokens": p, "output_tokens": o, "tenant": "t"}
                         for r, a, p, o in rows])


# ---- checks ---------------------------------------------------------------------------------------

@check("01 KV bytes per token (units)")
def _c01(m):
    kv = m.kv_bytes_per_token(I(m)["model"])
    assert kv == 2 * 80 * 8 * 128 * 2 == 327_680, (
        f"{kv} B/token; expected 2 (K,V) x 80 layers x 8 KV heads x 128 x 2 B = 327,680 B = 320 KiB "
        "(not 320 KB = 320,000 B)")
    return "327,680 B = 320 KiB per token (BF16 KV)"


@check("02 replica capacity")
def _c02(m):
    i = I(m)
    c1 = m.capacity(i["model"], i["hardware"], i["configs"]["c1_bf16_tp8_chunked"])
    c3 = m.capacity(i["model"], i["hardware"], i["configs"]["c3_fp8_tp4_chunked"])
    exp1 = int((8 * 80e9 * 0.90 - 140e9 - 8 * 4e9) // 327_680)
    exp3 = int((4 * 80e9 * 0.90 - 70e9 - 4 * 4e9) // 327_680)
    assert c1["kv_tokens"] == exp1, f"TP8 BF16 kv_tokens {c1['kv_tokens']}, expected {exp1} (404 GB KV budget)"
    assert c3["kv_tokens"] == exp3, f"TP4 FP8 kv_tokens {c3['kv_tokens']}, expected {exp3} (202 GB KV budget)"
    assert c1["max_seqs_at_4k"] == exp1 // 4096, f"max_seqs_at_4k {c1['max_seqs_at_4k']}"
    return f"TP8 BF16: {exp1:,} KV tokens ({exp1 // 4096} x 4k seqs); TP4 FP8: {exp3:,}"


@check("03 iteration cost (roofline + attention)")
def _c03(m):
    i = I(m)
    hw, md, cfg = i["hardware"], i["model"], i["configs"]["c1_bf16_tp8_chunked"]
    pre = m.iteration_time_s(2048, 0, 0, md, hw, cfg)
    exp_pre = 0.003 + max(2 * 70e9 * 2048 / (8 * 989e12 * 0.5), 140e9 / (8 * 3.35e12 * 0.7))
    dec = m.iteration_time_s(0, 64, 64 * 2000, md, hw, cfg)
    exp_dec = 0.003 + (140e9 + 64 * 2000 * 327_680) / (8 * 3.35e12 * 0.7)
    assert close(pre, exp_pre), f"2048-token prefill iteration {pre * 1e3:.2f} ms, expected {exp_pre * 1e3:.2f} ms (compute-bound)"
    assert close(dec, exp_dec), f"64-seq decode iteration {dec * 1e3:.2f} ms, expected {exp_dec * 1e3:.2f} ms (HBM-bound)"
    att = m.attention_flops(md, 0, 32000)
    assert close(att, 2 * 80 * 8192 * 32000 ** 2), f"attention FLOPs for a 32k prompt {att:.3e}, expected 2·L·d·n² = 1.34e15 for n = 32,000 (1.41e15 for n = 32,768)"
    assert close(m.attention_flops(md, 0, 2048) + m.attention_flops(md, 2048, 952), m.attention_flops(md, 0, 3000)), \
        "chunked attention FLOPs must sum to the full-prompt value: 2·L·d·((p+c)² − p²)"
    share = att / (att + 2 * 70e9 * 32000)
    return f"prefill 2k {pre * 1e3:.1f} ms; decode 64 x 2k {dec * 1e3:.1f} ms; attention = {share:.0%} of a 32k prefill"


@check("04 simulator: single request timeline")
def _c04(m):
    i = I(m)
    hw, md, cfg = i["hardware"], i["model"], i["configs"]["c1_bf16_tp8_chunked"]
    res = m.simulate(trace([("a", 0.0, 3000, 3)]), md, hw, cfg)
    t1 = m.iteration_time_s(2048, 0, 0, md, hw, cfg, m.attention_flops(md, 0, 2048))
    t2 = t1 + m.iteration_time_s(952, 0, 2048, md, hw, cfg, m.attention_flops(md, 2048, 952))
    g1 = m.iteration_time_s(0, 1, 3001, md, hw, cfg)
    g2 = m.iteration_time_s(0, 1, 3002, md, hw, cfg)
    r = res.iloc[0]
    assert r["status"] == "ok", f"status {r['status']}"
    assert close(r["ttft_s"], t2, 1e-6), f"TTFT {r['ttft_s']:.6f}, expected {t2:.6f} (chunks 2048 + 952 incl. attention; first token at chunk end)"
    assert close(r["e2e_s"], t2 + g1 + g2, 1e-6), f"E2E {r['e2e_s']:.6f}, expected {t2 + g1 + g2:.6f}"
    assert close(r["tpot_s"], (g1 + g2) / 2, 1e-6), "TPOT = (finish - first token) / (output - 1)"
    itl = list(res.attrs.get("itl_s", []))
    assert len(itl) == 2 and all(close(a, b, 1e-6) for a, b in zip(itl, [g1, g2])), \
        f"res.attrs['itl_s'] must hold every inter-token gap: {itl}"
    return "chunked prefill with attention, first-token timing, TPOT and per-token ITL exact"


@check("05 simulator: rejection and preemption")
def _c05(m):
    i = I(m)
    hw, md = i["hardware"], i["model"]
    cfg = dict(i["configs"]["c1_bf16_tp8_chunked"])
    res = m.simulate(trace([("x", 0.0, 32000, 1000), ("y", 0.0, 100, 10)]), md, hw, cfg)
    st = dict(zip(res["request_id"], res["status"]))
    assert st == {"x": "rejected", "y": "ok"}, f"statuses {st}: prompt + output > max_model_len must be rejected"
    small = dict(cfg, gpu_memory_utilization=0.2693)     # leaves room for only ~1,000 KV tokens
    cap = m.capacity(md, hw, small)["kv_tokens"]
    assert 500 < cap < 2000, f"test setup: capacity {cap}"
    res = m.simulate(trace([("big", 0.0, 1500, 10), ("p", 0.0, 400, 300), ("q", 0.0, 400, 300)]), md, hw, small)
    st = dict(zip(res["request_id"], res["status"]))
    assert st["big"] == "rejected", "a request larger than the whole KV cache must be rejected on arrival (else it waits forever)"
    assert st["p"] == st["q"] == "ok", "all fitting requests must eventually complete"
    assert int(res["preemptions"].sum()) >= 1, "KV exhaustion during decode must preempt the newest request"
    return f"over-length and over-capacity requests rejected; preemption at {cap:,}-token KV capacity"


@check("06 c1 nominal load: TTFT and ITL tails")
def _c06(m):
    _, s = run(m, "c1_bf16_tp8_chunked", 1.0)
    assert s["stable"], "c1 at node load 1.0 is stable (no queue growth)"
    assert close(s["ttft_p95_s"], 1.530, 0.03), f"TTFT p95 {s['ttft_p95_s']:.3f} s, reference 1.530 s (seed 1)"
    assert close(s["tpot_p95_s"], 0.0386, 0.03), f"TPOT p95 {s['tpot_p95_s'] * 1e3:.1f} ms, reference 38.6 ms"
    assert close(s["itl_p99_s"], 0.1037, 0.03), f"ITL p99 {s['itl_p99_s'] * 1e3:.1f} ms, reference 103.7 ms"
    assert close(s["ttft_target_s"], 0.77), "engine TTFT target = 0.8 s SLO − 30 ms frontend budget"
    assert not s["slo_met"], "c1 misses TTFT (head-of-line blocking) and ITL p99, though mean-based TPOT p95 looks fine"
    return f"TTFT p95 {s['ttft_p95_s']:.2f} s, TPOT p95 {s['tpot_p95_s'] * 1e3:.0f} ms but ITL p99 {s['itl_p99_s'] * 1e3:.0f} ms"


@check("07 c4 'meets SLO' by rejecting")
def _c07(m):
    _, s = run(m, "c4_bf16_tp8_len8k", 1.0)
    assert s["rejected"] == 82 and close(s["error_rate"], 82 / 3891, 0.02), f"rejected {s['rejected']}, error_rate {s['error_rate']:.4f}"
    assert s["slo_met"], "latency SLIs look fine for c4"
    rb, why = m.rollback_decision(s, s, I(m)["slo"])
    assert rb and any("burn" in w for w in why), f"a ~2.1 % error rate burns a 99.9 % budget ~21x: {why}"
    return f"latency SLIs met, but {s['error_rate']:.1%} rejections = {s['error_rate'] / 0.001:.0f}x burn -> roll back"


@check("08 c3 FP8 TP4 (two replicas per node)")
def _c08(m):
    _, s = run(m, "c3_fp8_tp4_chunked", 0.5)
    assert s["slo_met"] and close(s["ttft_p95_s"], 0.742, 0.03), f"TTFT p95 {s['ttft_p95_s']:.3f} s"
    return f"half the node's traffic per replica: TTFT p95 {s['ttft_p95_s']:.2f} s (target 0.77), ITL p99 {s['itl_p99_s'] * 1e3:.0f} ms"


@check("09 replication and instability")
def _c09(m):
    i = I(m)
    slo0 = dict(i["slo"], warmup_exclude_s=0, cooldown_exclude_s=0)
    over = trace([(f"o{k}", k / 40.0, 2000, 100) for k in range(400)])           # 40 req/s of 2k prompts
    calm = trace([(f"c{k}", k / 2.0, 2000, 100) for k in range(60)])             # 2 req/s
    cfg = i["configs"]["c1_bf16_tp8_chunked"]
    reps = m.replicate([over, calm], i["model"], i["hardware"], cfg, slo0)
    assert list(reps["stable"]) == [False, True], f"stable flags {list(reps['stable'])}: TTFT must trend upward under overload"
    ag = m.aggregate(reps)
    assert ag["ttft_p95_s_median"] is None and ag["stable_all"] is False, "an unstable seed makes latency medians 'unstable' (None)"
    assert m.aggregate(reps.iloc[[1]])["ttft_p95_s_median"] is not None, "stable seeds report a median"
    return "overloaded run flagged unstable; aggregate refuses to report a p95"


@check("10 error budget, burn rate, rollback gates")
def _c10(m):
    slo = I(m)["slo"]
    assert close(m.error_budget_minutes(0.999, 30), 43.2), "0.1 % of 30 days = 43.2 min"
    assert close(m.burn_rate(0.01, 0.999), 10.0), "1 % errors against a 0.1 % budget = 10x"
    base = {"ttft_p95_s": 0.40, "tpot_p95_s": 0.020, "itl_p99_s": 0.05, "error_rate": 0.0}
    ok, _ = m.rollback_decision(dict(base, ttft_p95_s=0.42), base, slo)
    assert ok is False, "5 % worse TTFT within SLO should not roll back"
    rb, _ = m.rollback_decision(dict(base, ttft_p95_s=0.46), base, slo)
    assert rb is True, "15 % TTFT regression should roll back"
    rb, _ = m.rollback_decision(dict(base, ttft_p95_s=0.78), dict(base, ttft_p95_s=0.78), slo)
    assert rb is True, "TTFT above 0.8 s − 30 ms frontend budget should roll back"
    rb, why = m.rollback_decision(dict(base, itl_p99_s=0.15), base, slo)
    assert rb is True and any("itl" in w for w in why), "ITL p99 above SLO should roll back"
    return "43.2 min budget; SLO (incl. frontend budget and ITL), regression and burn gates"


@check("11 cost per million tokens")
def _c11(m):
    i = I(m)
    _, s = run(m, "c3_fp8_tp4_chunked", 0.5)
    c = m.cost_per_million_tokens(s, i["configs"]["c3_fp8_tp4_chunked"], i["economics"])
    h = 4 * 2.20 / 0.65
    assert close(c["usd_per_hour"], h), f"usd/hour {c['usd_per_hour']:.3f}, expected {h:.3f} (idle capacity is paid for)"
    exp = h / ((s["output_tokens_per_s"] + s["input_tokens_per_s"]) * 3600) * 1e6
    assert close(c["usd_per_m_total"], exp), f"usd per M total tokens {c['usd_per_m_total']:.4f}"
    return f"${c['usd_per_hour']:.2f}/replica-hour -> ${c['usd_per_m_total']:.3f} per M total tokens (input-dominated mix) [MODELED]"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--impl", choices=["starter", "solution"], default="starter")
    args = ap.parse_args()
    try:
        mod = load(args.impl)
    except Exception as e:  # syntax error etc. in learner code
        print(f"FAIL import  {type(e).__name__}: {e}")
        return 1
    if mod is None:
        return 2
    counts = {"PASS": 0, "FAIL": 0, "TODO": 0}
    for name, fn in CHECKS:
        try:
            msg = fn(mod)
            status = "PASS"
        except NotImplementedError as e:
            status, msg = "TODO", str(e) or "not implemented yet"
        except AssertionError as e:
            status, msg = "FAIL", str(e) or "assertion failed"
        except Exception as e:  # noqa: BLE001 - report, never crash
            status, msg = "FAIL", f"{type(e).__name__}: {e}"
        counts[status] += 1
        print(f"{status:4} {name:<38} {msg}")
    total = len(CHECKS)
    print(f"\n{counts['PASS']}/{total} checks pass ({counts['TODO']} TODO, {counts['FAIL']} FAIL) [impl={args.impl}]")
    return 0 if counts["PASS"] == total else 1


if __name__ == "__main__":
    _ = math  # keep import for learners extending checks
    sys.exit(main())
