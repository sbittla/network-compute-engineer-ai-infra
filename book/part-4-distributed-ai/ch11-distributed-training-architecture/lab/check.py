#!/usr/bin/env python3
"""Checker for the Chapter 11 lab (W-TRAIN step-time, memory and checkpoint model).

Usage:
    python check.py                    # check your starter/stepmodel.py (default)
    python check.py --impl solution    # check the reference implementation

Prints one line per check (PASS / FAIL / TODO) and exits 0 only if every check passes.
Expected values are computed here from first principles, independently of the module under test.
"""
from __future__ import annotations

import argparse
import importlib.util
import math
import sys
from pathlib import Path
from typing import Callable

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
IMPLS = {
    "starter": HERE / "starter" / "stepmodel.py",
    "solution": HERE.parent / "solutions" / "lab" / "stepmodel.py",
}

# Independent expected values for the baseline (TP=8, PP=4, DP=8, b=1, ZeRO-1, selective).
N, L, H, S, GBS = 70e9, 80, 8192, 4096, 1024
P_LOCAL = N / 32
EXP_STATES_GB = (2 + 2 + 12 / 8) * P_LOCAL / 1e9                 # 12.03 GB
EXP_ACT_GB = S * H * 34 / 8 * (L // 4) * 4 / 1e9                 # 11.41 GB
EXP_TOTAL_GB = EXP_STATES_GB + EXP_ACT_GB + 4.0                  # 27.44 GB
M_PAYLOAD = S * H * 2                                            # 67.1 MB
EXP_TP_BYTES = 4 * (L // 4) * 128 * 2 * 7 / 8 * M_PAYLOAD        # 1.20 TB
EXP_DP_BYTES = 2 * 7 / 8 * 2 * P_LOCAL                           # 7.66 GB
EXP_PP_BYTES = 2 * 128 * M_PAYLOAD / 8                           # 2.15 GB
EXP_FEASIBLE = {"A_baseline_tp8_pp4_dp8", "B_tp8_pp2_dp16", "C_tp8_pp8_dp4", "D_tp4_pp8_dp8",
                "F_fsdp_tp1_pp1_dp256", "H_tp8_pp1_dp32", "K_tp8_pp4_dp8_fullrecomp",
                "L_tp8_pp4_dp8_mb2"}
BASE = {"tp": 8, "pp": 4, "dp": 8, "micro_batch": 1, "zero_stage": 1, "recompute": "selective"}


def close(a: float, b: float, rel: float = 0.01) -> bool:
    return abs(a - b) <= rel * abs(b)


def load(impl: str):
    path = IMPLS[impl]
    spec = importlib.util.spec_from_file_location(f"stepmodel_{impl}", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--impl", choices=sorted(IMPLS), default="starter")
    args = ap.parse_args()
    try:
        sm = load(args.impl)
        model, cluster, cands, rel = sm.load_inputs(DATA)
    except Exception as exc:  # noqa: BLE001 - report, never crash
        print(f"FAIL import/load_inputs: {type(exc).__name__}: {exc}")
        return 1

    def c_bubble() -> tuple[bool, str]:
        got = sm.bubble_fraction(4, 128)
        ok = close(got, 3 / 131, 1e-6) and sm.bubble_fraction(1, 32) == 0.0
        return ok, f"bubble(pp=4,m=128)={got:.4f} (expect {3/131:.4f}); pp=1 must be 0"

    def c_validate() -> tuple[bool, str]:
        base = sm.validate_config(model, cluster, BASE)
        e = sm.validate_config(model, cluster, {**BASE, "tp": 16, "pp": 2, "dp": 8})
        bad = sm.validate_config(model, cluster, {**BASE, "dp": 4})
        ok = base == [] and "tp_spans_nodes" in e and "kv_heads_not_divisible_by_tp" in e \
            and "world_size_mismatch" in bad
        return ok, f"baseline={base} tp16={e} dp4={bad}"

    def c_memory() -> tuple[bool, str]:
        m = sm.memory_per_gpu(model, cluster, BASE)
        states = m["weights_gb"] + m["grads_gb"] + m["optimizer_gb"]
        ok = close(states, EXP_STATES_GB) and close(m["activations_gb"], EXP_ACT_GB) \
            and close(m["total_gb"], EXP_TOTAL_GB)
        return ok, (f"states={states:.2f} GB (exp {EXP_STATES_GB:.2f}), act={m['activations_gb']:.2f} "
                    f"(exp {EXP_ACT_GB:.2f}), total={m['total_gb']:.2f} (exp {EXP_TOTAL_GB:.2f})")

    def c_traps() -> tuple[bool, str]:
        g = sm.memory_per_gpu(model, cluster, {**BASE, "tp": 1, "pp": 4, "dp": 64})["total_gb"]
        i = sm.memory_per_gpu(model, cluster, {**BASE, "micro_batch": 4, "zero_stage": 0})["total_gb"]
        j = sm.memory_per_gpu(model, cluster, {**BASE, "tp": 2, "pp": 8, "dp": 16})["total_gb"]
        ok = g > 80 and i > 80 and 68 < j <= 80
        return ok, f"G={g:.1f} GB (>80), I={i:.1f} GB (>80), J={j:.1f} GB (68..80: fits, violates headroom)"

    def c_allreduce() -> tuple[bool, str]:
        t1 = sm.allreduce_time_s(M_PAYLOAD, 8, 8, cluster)
        e1 = 1.75 * M_PAYLOAD / 300e9
        t2 = sm.allreduce_time_s(2 * P_LOCAL, 8, 1, cluster)
        e2 = 1.75 * 2 * P_LOCAL / 45e9
        ok = close(t1, e1) and close(t2, e2)
        return ok, f"NVLink 8-GPU 67 MB: {t1*1e6:.0f} us (exp {e1*1e6:.0f}); 8-node rail 4.4 GB: {t2:.3f} s (exp {e2:.3f})"

    def c_comm() -> tuple[bool, str]:
        c = sm.comm_model(model, cluster, BASE)
        ok = close(c["tp_bytes"], EXP_TP_BYTES) and close(c["dp_bytes"], EXP_DP_BYTES) \
            and close(c["pp_bytes"], EXP_PP_BYTES) and c["micro_batches"] == 128 and not c["tp_spans_nodes"]
        return ok, (f"TP={c['tp_bytes']/1e12:.3f} TB (exp {EXP_TP_BYTES/1e12:.3f}), DP={c['dp_bytes']/1e9:.2f} GB "
                    f"(exp {EXP_DP_BYTES/1e9:.2f}), PP={c['pp_bytes']/1e9:.2f} GB (exp {EXP_PP_BYTES/1e9:.2f})")

    def c_step() -> tuple[bool, str]:
        st = sm.step_time(model, cluster, BASE)
        ok = close(st["step_s"], 17.45, 0.01) and close(st["mfu"], 0.399, 0.02) \
            and close(st["compute_s"], 6 * N * GBS * S / 256 / (989e12 * 0.5), 0.005)
        ok = ok and close(st["exposed_dp_s"], 0.1702 - 13.916 / 128 * 0.667, 0.02)
        return ok, (f"baseline step={st['step_s']:.2f} s (exp ~17.45), MFU={st['mfu']:.3f} (exp ~0.399), "
                    f"exposed DP={st['exposed_dp_s']*1e3:.0f} ms (exp ~98)")

    def c_evaluate() -> tuple[bool, str]:
        t = sm.evaluate_candidates(model, cluster, cands)
        feas = set(t.loc[t["feasible"], "name"])
        rec = sm.recommend(t)
        ok = feas == EXP_FEASIBLE and rec == "D_tp4_pp8_dp8"
        return ok, f"feasible={len(feas)} (exp {len(EXP_FEASIBLE)}), recommended={rec} (exp D_tp4_pp8_dp8)"

    def c_youngdaly() -> tuple[bool, str]:
        mtbf = 48 * 3600.0
        tau = sm.young_daly_interval_s(45.0, mtbf)
        w = sm.waste_fraction(tau, 45.0, 900.0, mtbf)
        lost = sm.expected_lost_work_s(tau, 900.0)
        et = math.sqrt(2 * 45 * mtbf)
        ok = close(tau, et, 1e-6) and close(w, 45 / et + (et / 2 + 900) / mtbf, 1e-6) and close(lost, et / 2 + 900, 1e-6)
        return ok, f"tau_opt={tau/60:.1f} min (exp {et/60:.1f}), waste={w*100:.2f} %"

    def c_reliability() -> tuple[bool, str]:
        r = sm.reliability_table(rel).set_index("name")
        xl = r.loc["orionxl4096_sync_pfs"]
        ok = (close(xl["tau_opt_min"], math.sqrt(2 * 45 * 3.0 * 3600) / 60) and math.isnan(xl["waste_at_4h"])
              and not bool(xl["valid_at_4h"]) and close(xl["p_interval_completes_4h"], math.exp(-4 / 3), 1e-6))
        return ok, (f"ORION-XL sync tau_opt={xl['tau_opt_min']:.1f} min, waste opt={xl['waste_at_opt']*100:.1f} %; "
                    f"4 h interval invalid (completes with p={xl['p_interval_completes_4h']:.2f})")

    checks: list[tuple[str, Callable[[], tuple[bool, str]]]] = [
        ("bubble_fraction", c_bubble),
        ("validate_config", c_validate),
        ("memory_baseline", c_memory),
        ("memory_traps", c_traps),
        ("allreduce_time", c_allreduce),
        ("comm_volumes_baseline", c_comm),
        ("step_time_baseline", c_step),
        ("evaluate_and_recommend", c_evaluate),
        ("young_daly", c_youngdaly),
        ("reliability_table", c_reliability),
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
        except Exception as exc:  # noqa: BLE001 - never crash the learner's progress meter
            print(f"FAIL {name}: {type(exc).__name__}: {exc}")
            failed += 1
    print(f"\n{len(checks) - failed}/{len(checks)} checks passed ({args.impl})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
