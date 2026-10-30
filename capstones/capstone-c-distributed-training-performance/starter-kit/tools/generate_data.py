#!/usr/bin/env python3
"""Generate the Capstone C supplied run logs for W-TRAIN weak-scaling experiments on ORION.

Writes (byte-identical on every run with the same seed):
  runs.csv               per-step times for 3 variants x 4 scales (32/64/128/256 GPUs) x 5 repetitions
  manifests.csv          one environment manifest row per run
  profile_summary.csv    nsys-style per-step time breakdown (busy and exposed ms) at 32 and 256 GPUs
  nccl_tests.csv         all_reduce_perf bus bandwidth sweeps, 8 GPUs (1 node) and 16 GPUs (2 nodes)
  nccl_debug_baseline.log / nccl_debug_ib_gdr.log   NCCL_DEBUG=INFO excerpts from rank 0 [ILLUSTRATIVE;
                         exact wording varies by NCCL version]

The data is [SIMULATED]: a step-time model (compute + exposed communication + straggler maximum over
nodes + noise) stands in for real runs. It is designed to look like what a performance engineer gets
back from a cluster, including the defects such logs really have.

Usage:
    python tools/generate_data.py [--out ../data] [--seed 1729]
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

COMPUTE_S = 6 * 70e9 * (128 * 4096) / (32 * 989e12 * 0.40)   # per DP replica of 32 GPUs, [MODELED] ≈ 17.39 s
GRAD_BYTES = 70e9 / 32 * 2                                     # per GPU (TP8 x PP4 shard), BF16
PP_BYTES = 128 * 4096 * 8192 * 2 / 8                           # per GPU per boundary per direction
SCALES = [32, 64, 128, 256]
STEPS = 60
REPS = 8
# DP exposure follows docs/VERIFIED_FACTS.md: with PP, only the last micro-batch's backward (~70 ms on
# W-TRAIN) can hide the DP collective, so exposed = max(0, T_DP - window). The bucket variant's +15 ms
# window (fewer, larger buckets -> less per-call overhead at the tail) is an ILLUSTRATIVE effect size.
# PP send/recv: half of it is on the critical path at stage boundaries [ILLUSTRATIVE].
VARIANTS = {
    # name: (inter-node bus bandwidth GB/s, DP exposed model, PP exposed fraction, per-step noise sigma)
    "baseline": {"busbw": 2.5, "dp_window_s": 0.07, "dp_frac": None, "pp_frac": 0.5, "sigma": 0.035,
                 "nccl_net": "Socket", "gdr": "disabled", "bucket_cap_mb": 25},
    "ib_gdr": {"busbw": 40.0, "dp_window_s": 0.07, "dp_frac": None, "pp_frac": 0.5, "sigma": 0.010,
                "nccl_net": "IB", "gdr": "enabled", "bucket_cap_mb": 25},
    "ib_gdr_bucket": {"busbw": 40.0, "dp_window_s": 0.085, "dp_frac": None, "pp_frac": 0.5, "sigma": 0.010,
                       "nccl_net": "IB", "gdr": "enabled", "bucket_cap_mb": 100},
}


def comm_times(v: dict, n_gpus: int) -> tuple[float, float, float, float]:
    """Return (dp_busy, dp_exposed, pp_busy, pp_exposed) seconds per step."""
    dp = n_gpus // 32
    dp_busy = 2 * (dp - 1) / dp * GRAD_BYTES / (v["busbw"] * 1e9) if dp > 1 else 0.0
    if v["dp_window_s"] is not None:
        dp_exp = max(dp_busy - v["dp_window_s"], 0.0)
    else:
        dp_exp = v["dp_frac"] * dp_busy
    pp_busy = PP_BYTES / (v["busbw"] * 1e9)
    return dp_busy, dp_exp, pp_busy, v["pp_frac"] * pp_busy


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parent.parent / "data")
    ap.add_argument("--seed", type=int, default=1729)
    args = ap.parse_args()
    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    run_rows = ["run_id,variant,n_gpus,rep,step,step_time_s,tokens"]
    man_rows = ["run_id,variant,n_gpus,rep,date,container_image,pytorch,cuda,driver,nccl_version,nccl_net,"
                "gdr,rdma_dev_in_container,bucket_cap_mb,warmup_steps_policy,nodes,notes"]
    run_no = 400
    for vi, (name, v) in enumerate(VARIANTS.items()):
        for n in SCALES:
            nodes = n // 8
            _, dp_exp, _, pp_exp = comm_times(v, n)
            for rep in range(1, REPS + 1):
                run_no += 1
                rid = f"r{run_no:04d}"
                run_offset = rng.normal(0, 0.004)
                nccl, image = "2.23.4", "halcyon/train:2026.10.1"
                notes = ""
                extra = 1.0
                if name == "ib_gdr" and n == 64 and rep == 4:
                    nccl, image, extra = "2.21.5", "halcyon/train:2026.09.3", 1.015
                    notes = "image rebuilt from stale cache"
                if name == "ib_gdr" and n == 256 and rep == 2:
                    extra = 1.07
                    notes = ("DCGM: SW thermal slowdown clock-event reason on orion-n19 GPU3 in 100 % of sampled steps; "
                             "SM clock ~1710 MHz vs peers ~1830 MHz (-6.6 %)")
                steps = list(range(STEPS))
                if name == "baseline" and n == 128 and rep == 3:
                    steps = list(range(42)) + list(range(36, STEPS))     # restart from checkpoint at step 36
                    notes = "job requeued after node failure; resumed from step-36 checkpoint"
                restart_seen = False
                for i, s in enumerate(steps):
                    node_noise = rng.normal(0, 0.012, size=nodes).max()           # synchronous: slowest node
                    t = COMPUTE_S * (1 + node_noise) + dp_exp + pp_exp
                    t *= (1 + run_offset) * extra * (1 + rng.normal(0, v["sigma"]))
                    first_after_restart = (i > 0 and s < steps[i - 1])
                    if first_after_restart:
                        restart_seen = True
                    warm_idx = s if not restart_seen else s - 36
                    if 0 <= warm_idx < 5:
                        t *= [3.1, 1.35, 1.18, 1.08, 1.03][warm_idx]
                    tokens = 128 * 4096 * (n // 32)
                    run_rows.append(f"{rid},{name},{n},{rep},{s},{t:.4f},{tokens}")
                man_rows.append(
                    f"{rid},{name},{n},{rep},2026-10-{5 + vi:02d},{image},2.5.1,12.6,"
                    f"570.86.15,{nccl},{v['nccl_net']},{v['gdr']},{'no' if name == 'baseline' else 'yes'},"
                    f"{v['bucket_cap_mb']},none-recorded,{nodes},{notes}")
    (out / "runs.csv").write_text("\n".join(run_rows) + "\n", encoding="utf-8", newline="\n")
    (out / "manifests.csv").write_text("\n".join(man_rows) + "\n", encoding="utf-8", newline="\n")

    # ---- profile summary (nsys-style aggregation over 10 steady-state steps, per-step means)
    prof = ["variant,n_gpus,category,busy_ms,exposed_ms"]
    for name, v in VARIANTS.items():
        for n in (32, 256):
            dp_busy, dp_exp, pp_busy, pp_exp = comm_times(v, n)
            straggle = COMPUTE_S * 0.012 * (1.03 if n == 32 else 2.04)
            cats = [
                ("gemm", COMPUTE_S * 0.68, COMPUTE_S * 0.68),
                ("attention", COMPUTE_S * 0.21, COMPUTE_S * 0.21),
                ("other_compute", COMPUTE_S * 0.11, COMPUTE_S * 0.11),
                ("nccl_tp_allreduce_nvlink", 2.10, 0.0),
                ("nccl_dp_allreduce", dp_busy, dp_exp),
                ("nccl_pp_sendrecv", pp_busy, pp_exp),
                ("memcpy_dtoh_htod", (dp_busy + pp_busy) * 0.55 if v["gdr"] == "disabled" else 0.004, 0.0),
                ("idle_sync_wait", straggle, straggle),
            ]
            for c, busy, exp in cats:
                prof.append(f"{name},{n},{c},{busy * 1000:.1f},{exp * 1000:.1f}")
    (out / "profile_summary.csv").write_text("\n".join(prof) + "\n", encoding="utf-8", newline="\n")

    # ---- nccl-tests all_reduce_perf (out-of-place busbw, GB/s)
    sizes = [2**k for k in range(20, 34)]          # 1 MiB .. 8 GiB
    nt = ["variant,n_gpus,size_bytes,algbw_GBps,busbw_GBps"]
    for name, peak16 in (("baseline", 20.0), ("ib_gdr", 360.0)):
        for n, peak in ((8, 370.0), (16, peak16)):
            for sz in sizes:
                half = 8e6 if n == 8 else (2e6 if name == "baseline" else 32e6)
                bus = peak * sz / (sz + half) * (1 + rng.normal(0, 0.01))
                alg = bus / (2 * (n - 1) / n)
                nt.append(f"{name},{n},{sz},{alg:.2f},{bus:.2f}")
    (out / "nccl_tests.csv").write_text("\n".join(nt) + "\n", encoding="utf-8", newline="\n")

    base_log = """orion-n01:20417:20417 [0] NCCL INFO Bootstrap : Using eth0:10.10.1.11<0>
orion-n01:20417:20417 [0] NCCL INFO NET/IB : No device found.
orion-n01:20417:20417 [0] NCCL INFO NET/Socket : Using [0]eth0:10.10.1.11<0> [1]eth1:10.10.129.11<0>
orion-n01:20417:20417 [0] NCCL INFO Using network Socket
orion-n01:20417:20530 [0] NCCL INFO Channel 00/0 : 0[0] -> 8[0] [send] via NET/Socket/0
orion-n01:20417:20530 [0] NCCL INFO Channel 01/0 : 0[0] -> 8[0] [send] via NET/Socket/1
orion-n01:20417:20530 [0] NCCL INFO Connected all rings
"""
    ib_log = """orion-n01:31877:31877 [0] NCCL INFO Bootstrap : Using eth0:10.10.1.11<0>
orion-n01:31877:31877 [0] NCCL INFO NET/IB : Using [0]mlx5_0:1/RoCE [1]mlx5_1:1/RoCE [2]mlx5_2:1/RoCE [3]mlx5_3:1/RoCE [4]mlx5_4:1/RoCE [5]mlx5_5:1/RoCE [6]mlx5_6:1/RoCE [7]mlx5_7:1/RoCE ; OOB eth0:10.10.1.11<0>
orion-n01:31877:31877 [0] NCCL INFO Using network IB
orion-n01:31877:31990 [0] NCCL INFO Channel 00/0 : 0[0] -> 8[0] [send] via NET/IB/0/GDRDMA
orion-n01:31877:31990 [0] NCCL INFO Channel 01/0 : 0[0] -> 8[0] [send] via NET/IB/0/GDRDMA
orion-n01:31877:31990 [0] NCCL INFO Connected all rings
"""
    (out / "nccl_debug_baseline.log").write_text(base_log, encoding="utf-8", newline="\n")
    (out / "nccl_debug_ib_gdr.log").write_text(ib_log, encoding="utf-8", newline="\n")
    print(f"wrote dataset to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
