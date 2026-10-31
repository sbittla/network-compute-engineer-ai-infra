"""14.8 -- Checkpoint size, write time, overhead and RPO for a 34B model on 128 GPUs. [MODELED]

Usage: python solve.py --out DIR
Inputs (prompt, [ILLUSTRATIVE]): 34e9 params, 14 B/param, 128 GPUs, PFS 50 GB/s at 80 %, commit 1.0 s,
interval 15 min; async snapshot 0.6 s; 3 % interference; RPO target ≈ 5 min.
Formulas: manuscript Sections 14.9 and 14.11 (RPO max = tau + L, E[lost] = tau/2 + L).
"""
import argparse
import json
from pathlib import Path

PARAMS = 34e9
B_PER_PARAM = 14
GPUS = 128
PFS_GBPS = 50.0
EFF = 0.80
COMMIT_S = 1.0
TAU_S = 15 * 60
SNAP_S = 0.6
INTERF = 0.03
RPO_TARGET_S = 300


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    size = PARAMS * B_PER_PARAM
    per_gpu = size / GPUS
    write = size / (PFS_GBPS * 1e9 * EFF)
    blocking = write + COMMIT_S
    overhead = blocking / TAU_S
    rpo_max = TAU_S + blocking
    e_lost = TAU_S / 2 + blocking
    persist = blocking                       # background write + commit for async
    ovh_async_block = SNAP_S / TAU_S
    delta_async = SNAP_S + INTERF * persist
    ovh_async = delta_async / TAU_S
    L_async = SNAP_S + persist
    rpo_async = TAU_S + L_async
    tau_f = RPO_TARGET_S - L_async
    ovh_f = delta_async / tau_f

    # Key 14.8 (tolerances in the units shown).
    checks = [(size / 1e9, 476, 0.5), (per_gpu / 1e9, 3.72, 0.005), (write, 11.9, 0.05), (blocking, 12.9, 0.05),
              (overhead * 100, 1.43, 0.005), (rpo_max, 912.9, 0.1), (e_lost, 462.9, 0.1),
              (ovh_async_block * 100, 0.067, 0.0005), (ovh_async * 100, 0.11, 0.005), (rpo_async, 913.5, 0.1),
              (tau_f, 286.5, 0.1), (delta_async, 0.987, 0.001), (ovh_f * 100, 0.34, 0.005)]
    for got, want, tol in checks:
        assert abs(got - want) <= tol, (got, want)

    ans = {"a_size_GB": round(size / 1e9, 1), "a_per_gpu_GB": round(per_gpu / 1e9, 2),
           "b_write_s": round(write, 2), "b_blocking_s": round(blocking, 2),
           "c_overhead_pct": round(overhead * 100, 2),
           "d_rpo_max_s": round(rpo_max, 1), "d_expected_lost_s": round(e_lost, 1),
           "e_overhead_blocking_pct": round(ovh_async_block * 100, 3),
           "e_overhead_with_interference_pct": round(ovh_async * 100, 2),
           "e_completion_s": round(L_async, 1), "e_rpo_max_s": round(rpo_async, 1),
           "f_interval_s": round(tau_f, 1), "f_delta_s": round(delta_async, 3), "f_overhead_pct": round(ovh_f * 100, 2)}
    result = {
        "inputs": {"params": PARAMS, "bytes_per_param": B_PER_PARAM, "gpus": GPUS, "pfs_GBps": PFS_GBPS,
                   "efficiency": EFF, "commit_s": COMMIT_S, "interval_s": TAU_S, "snapshot_s": SNAP_S,
                   "interference": INTERF, "rpo_target_s": RPO_TARGET_S},
        "steps": {"effective_GBps": PFS_GBPS * EFF, "persist_s": round(persist, 2)},
        "answer": ans,
        "units": {"time": "s", "size": "GB (1e9 B)", "overhead": "%"},
        "evidence_label": "[MODELED]",
    }
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = "\n".join([
        "# 14.8 result `[MODELED]`", "",
        f"(a) S = 34e9 × 14 B = {size/1e9:.0f} GB; per GPU {per_gpu/1e9:.2f} GB",
        f"(b) write = {size/1e9:.0f} / {PFS_GBPS*EFF:.0f} = {write:.1f} s; blocking = {blocking:.1f} s",
        f"(c) overhead = {blocking:.1f} / {TAU_S} = {overhead*100:.2f} %",
        f"(d) RPO max = {TAU_S} + {blocking:.1f} = {rpo_max:.1f} s; E[lost] = {TAU_S/2:.0f} + {blocking:.1f} = {e_lost:.1f} s",
        f"(e) async: overhead {ovh_async_block*100:.3f} % ({ovh_async*100:.2f} % with interference); "
        f"L = {L_async:.1f} s; RPO max = {rpo_async:.1f} s (unchanged)",
        f"(f) tau = 300 - {L_async:.1f} = {tau_f:.1f} s; delta = {delta_async:.3f} s; overhead = {ovh_f*100:.2f} %", ""])
    (out / "result.md").write_text(md, encoding="utf-8")


if __name__ == "__main__":
    main()
