#!/usr/bin/env python3
"""Generate the Chapter 22 regression-investigation bundle (deterministic, seeded).

Scenario: on ORION-256, Halcyon AI runs a sweep of W-TRAIN ablation jobs. Each job uses 64 GPUs
(8 HX8 nodes; TP=8, PP=4, DP=2; 128 sequences x 4,096 tokens per DP replica per step). This is a
stated variation of the reference W-TRAIN workload (docs/REFERENCE_CLUSTER.md): global batch is
256 sequences instead of 1,024, so modeled step time at 40 % MFU stays ~17.4 s.

After a "routine" change window, the fleet dashboard shows mean step time up ~23 %. Several things
changed at once. The generator encodes ground truth that only the instructor solution documents.

All values are [SIMULATED]. Regenerating produces byte-identical files.

Usage:
    python tools/generate_data.py            # writes ../data/
    python tools/generate_data.py --out DIR
"""
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import numpy as np

SEED = 2214
N_NODES = 32
NODES = [f"orion-n{i + 1:02d}" for i in range(N_NODES)]  # canonical names
BLOCKS = 4                 # 4 blocks of 8 nodes; Slurm allocates whole blocks (topology-aware)
SLOTS = 6                  # 6 sequential time slots per period, 4 concurrent jobs per slot
STEPS = 200
FAILED_STEPS = 70
WARMUP_STEPS = 10

# ---- ground truth (seconds per step) -- documented only in solutions/ ----
BASE_COMPUTE_S = 17.35     # compute + exposed comm with good placement; data wait added separately
AFTER_SHIFT_S = 0.20       # unexplained common shift in the after period
TP_SPLIT_S = 8.90          # TP group spans two nodes -> TP all-reduce leaves NVLink
DRIVER_S = 1.00            # GPUDirect RDMA disabled on upgraded nodes -> host-staged inter-node
ALERT_S = 0.00             # red herring: correctable-ECC alert on orion-n13
STEP_NOISE_S = 0.30
JOB_NOISE_S = 0.10
STALL_P = 0.10             # capacity-tier dataloader stall probability per step
STALL_RANGE_S = (10.0, 18.0)
SPLIT_STALL_EXPOSED = 0.10  # fraction of a recall stall still exposed when the step is TP-split

# After-period design (job index j = slot*4 + block)
TP_SPLIT_J = {1, 6, 8, 11, 13, 16, 22}
STORAGE_NEW_J = {0, 1, 3, 4, 6, 7, 9, 10, 13, 15, 17, 18, 20, 23}
FAILED_J = 13               # TP-split job that later died with an NCCL timeout (survivorship trap)
DUP_J = 4                   # log shipper replayed this job's stall steps twice
DRIVER_NEW_NODES = set(NODES[16:])
ALERT_NODE = "orion-n13"


def fmt(x: float, nd: int = 3) -> str:
    return f"{x:.{nd}f}"


def block_nodes(b: int) -> list[str]:
    return NODES[8 * b: 8 * b + 8]


def placement_rows(job_id: int, b: int, split: bool) -> list[list]:
    """Rank -> (node, local GPU). TP groups are 8 consecutive ranks (Megatron ordering)."""
    nodes = block_nodes(b)
    rows = []
    for r in range(64):
        slot = (r + 4) % 64 if split else r
        rows.append([job_id, r, nodes[slot // 8], slot % 8, r // 8, (r // 8) % 4, r // 32])
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parents[1] / "data")
    args = ap.parse_args()
    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)

    jobs, steps, place, nmet = [], [], [], []
    for period in ("before", "after"):
        for s in range(SLOTS):
            for b in range(BLOCKS):
                j = s * BLOCKS + b
                job_id = (41001 if period == "before" else 41101) + j
                after = period == "after"
                split = after and j in TP_SPLIT_J
                sto_new = after and j in STORAGE_NEW_J
                nodes = block_nodes(b)
                drv = after and any(n in DRIVER_NEW_NODES for n in nodes)
                alert = after and ALERT_NODE in nodes
                failed = after and j == FAILED_J
                n_steps = FAILED_STEPS if failed else STEPS
                day = 5 + s if not after else 12 + s
                start = f"2026-10-{day:02d}T{8 + b:02d}:00:00Z"
                jobs.append([job_id, period, start, "FAILED" if failed else "COMPLETED", n_steps,
                             "capacity" if sto_new else "hot", ";".join(nodes)])
                place.extend(placement_rows(job_id, b, split))

                job_off = rng.normal(0.0, JOB_NOISE_S)
                mean_compute = (BASE_COMPUTE_S + job_off + AFTER_SHIFT_S * after + TP_SPLIT_S * split
                                + DRIVER_S * drv + ALERT_S * alert)
                job_rows = []
                for k in range(n_steps):
                    if sto_new:
                        dw = 0.10 + abs(rng.normal(0, 0.03))
                        if rng.random() < STALL_P:
                            stall = rng.uniform(*STALL_RANGE_S)
                            # TP-split steps are ~26 s, so the 1-worker loader has ~10 s slack per step
                            # and the prefetch buffer hides most of each recall (true interaction).
                            dw += SPLIT_STALL_EXPOSED * stall if split else stall
                    else:
                        dw = 0.05 + abs(rng.normal(0, 0.02))
                    warm = 30.0 * 0.5 ** k
                    if k == 0:
                        dw += 4.0
                    st = mean_compute + rng.normal(0, STEP_NOISE_S) + warm + dw
                    job_rows.append([job_id, k, fmt(st), fmt(dw)])
                steps.extend(job_rows)
                if after and j == DUP_J:
                    stall = [r for r in job_rows if float(r[3]) > 5.0]
                    steps.extend(stall + stall)      # replayed twice by the log shipper

                mean_step = mean_compute + ((0.25 if split else 1.45) if sto_new else 0.06)
                for n in nodes:
                    sm = 0.62 * BASE_COMPUTE_S / mean_step + rng.normal(0, 0.01)
                    nic = (38.0 if split else 6.0) + rng.normal(0, 0.5)
                    iow = (6.0 if sto_new else 1.5) + rng.normal(0, 0.3)
                    host_copy = (9.5 if (after and n in DRIVER_NEW_NODES) else 0.4) + rng.normal(0, 0.1)
                    sbe = int(140 + rng.integers(0, 20)) if (after and n == ALERT_NODE) else int(rng.integers(0, 2))
                    temp = 68.0 + rng.normal(0, 1.5)
                    nmet.append([job_id, n, fmt(sm), fmt(nic, 2), fmt(iow, 2), fmt(host_copy, 2), sbe, fmt(temp, 1)])

    def write(name: str, header: list[str], rows: list[list]) -> None:
        with open(out / name, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(header)
            w.writerows(rows)

    write("jobs.csv", ["job_id", "period", "start_utc", "status", "steps_logged", "dataset_tier", "nodes"], jobs)
    write("step_log.csv", ["job_id", "step", "step_time_s", "data_wait_s"], steps)
    write("placement.csv", ["job_id", "rank", "node", "local_gpu", "tp_group", "pp_stage", "dp_replica"], place)
    write("node_metrics.csv", ["job_id", "node", "sm_active_mean", "backend_tx_GBps_mean", "cpu_iowait_pct",
                               "host_bounce_copy_GBps", "gpu_ecc_sbe_count", "gpu_temp_c_mean"], nmet)
    inv = [[n, f"rack-{i // 4 + 1:02d}", i // 8, "R570" if n in DRIVER_NEW_NODES else "R550",
            "no" if n in DRIVER_NEW_NODES else "yes"] for i, n in enumerate(NODES)]
    write("node_inventory.csv", ["node", "rack", "block", "driver_branch", "peermem_module_loaded"], inv)
    write("alerts.csv", ["alert", "target", "start_utc", "end_utc", "severity", "detail"], [
        ["NodeGPUCorrectableECCHigh", "orion-n13/GPU3", "2026-10-12T07:14:00Z", "", "warning",
         "SBE rate 140-160/h; no DBE; no row-remap pending"],
        ["StorageReadLatencyP99High", "dataset-capacity-tier", "2026-10-12T09:02:00Z", "", "warning",
         "read p99 > 250 ms for 5m, intermittent"],
        ["BackendLinkFlap", "orion-be-leaf-r3:Ethernet12", "2026-10-09T03:40:00Z", "2026-10-09T03:41:00Z", "info",
         "single flap, before change window; port clean since"],
    ])
    (out / "change_log.yaml").write_text(CHANGE_LOG, encoding="utf-8")
    (out / "hypotheses.yaml").write_text(HYPOTHESES, encoding="utf-8")
    (out / "nccl_init_sample.log").write_text(NCCL_LOG, encoding="utf-8")
    print(f"wrote bundle to {out}")
    return 0


CHANGE_LOG = """\
# Change window CW-2026-10-12 (02:00-06:00 UTC). [SIMULATED] bundle for Chapter 22.
window: {start: "2026-10-12T02:00:00Z", end: "2026-10-12T06:00:00Z"}
changes:
  - id: CHG-7781
    team: Fleet
    summary: "GPU driver branch R550 -> R570 on orion-n17..orion-n32 (canary half of ORION-256)"
    scope: [orion-n17, orion-n18, orion-n19, orion-n20, orion-n21, orion-n22, orion-n23, orion-n24,
            orion-n25, orion-n26, orion-n27, orion-n28, orion-n29, orion-n30, orion-n31, orion-n32]
    validation_recorded: "nvidia-smi shows 8 GPUs; dcgmi diag -r 1 pass"
  - id: CHG-7790
    team: Platform
    summary: "Placement policy: allow jobs to start on partially free nodes (fragmentation relief)"
    scope: training partition
    validation_recorded: "pending-job count down 30 %"
  - id: CHG-7795
    team: Storage
    summary: "Move sweep datasets ds-web-2026q3 and ds-code-v4 from hot PFS tier to capacity tier"
    scope: datasets ds-web-2026q3, ds-code-v4
    validation_recorded: "bulk read test 40 GB/s from one client"
  - id: CHG-7802
    team: Training Infra
    summary: "Base container rebuilt with security patches; framework versions unchanged"
    scope: all training jobs
    validation_recorded: "smoke test passed"
"""

HYPOTHESES = """\
# Candidate discriminating tests for the CW-2026-10-12 regression. [ILLUSTRATIVE] estimates.
# info_value: expected fraction of remaining uncertainty the test resolves (0-1).
# cost_hours: engineer + machine hours. risk: low | medium | high.
# environment: offline (existing data), lab (reserved/drained nodes), production (live jobs).
tests:
  - id: T1
    hypothesis: H-placement
    action: "Derive TP-group node span per job from placement records (scontrol show job -d / placement.csv)"
    info_value: 0.9
    cost_hours: 0.5
    risk: low
    environment: offline
  - id: T2
    hypothesis: H-driver
    action: "Check NCCL INFO channel lines for the /GDRDMA suffix by node, and lsmod | grep nvidia_peermem on upgraded nodes"
    info_value: 0.7
    cost_hours: 0.5
    risk: low
    environment: offline
  - id: T3
    hypothesis: H-storage
    action: "Compare dataloader wait (data_wait_s) distribution by dataset tier from existing step logs"
    info_value: 0.8
    cost_hours: 0.25
    risk: low
    environment: offline
  - id: T4
    hypothesis: H-ecc
    action: "Compare step time of jobs that included orion-n13 with jobs that did not, controlling for other factors"
    info_value: 0.3
    cost_hours: 0.25
    risk: low
    environment: offline
  - id: T5
    hypothesis: H-driver
    action: "Roll back R570 on all 16 upgraded nodes during business hours"
    info_value: 0.6
    cost_hours: 8
    risk: high
    environment: production
  - id: T6
    hypothesis: H-driver
    action: "all_reduce_perf between two drained nodes: one R550, one R570, GDR on/off"
    info_value: 0.7
    cost_hours: 3
    risk: medium
    environment: lab
  - id: T7
    hypothesis: H-placement
    action: "A/B: same job config, TP-packed vs TP-split, on 16 reserved nodes, 5 repetitions"
    info_value: 0.9
    cost_hours: 6
    risk: medium
    environment: lab
  - id: T8
    hypothesis: H-storage
    action: "fio random-read 1 MiB on capacity tier from one drained node"
    info_value: 0.5
    cost_hours: 2
    risk: low
    environment: lab
  - id: T9
    hypothesis: H-network
    action: "Restart all running jobs with NCCL_DEBUG=INFO to capture topology"
    info_value: 0.4
    cost_hours: 4
    risk: high
    environment: production
"""

NCCL_LOG = """\
# [ILLUSTRATIVE] Excerpts from NCCL_DEBUG=INFO output and node checks, abridged ("...").
# Formats follow NCCL 2.18-2.28 INFO output [VENDOR-SPEC, 2026-10]; verify against the version you run.
# GDR evidence = the "/GDRDMA" suffix on NET channel lines (absent => host-staged), plus the peer-memory
# module check. DMA-BUF can also provide GPUDirect RDMA without nvidia_peermem; on these nodes the DMA-BUF
# path is not available (kernel/driver/RDMA-stack combination), so the module check is decisive here.
#
# --- job 41110 init, block 1 (orion-n09..n16, driver R550) ---
orion-n09:2211:2290 [0] NCCL INFO NET/IB : Using [0]mlx5_0:1/RoCE [1]mlx5_1:1/RoCE ... [7]mlx5_7:1/RoCE
orion-n09:2211:2290 [0] NCCL INFO Channel 00/0 : 0[0] -> 8[0] [send] via NET/IB/0/GDRDMA
orion-n09:2211:2290 [0] NCCL INFO Channel 01/0 : 0[0] -> 8[0] [send] via NET/IB/0/GDRDMA
# --- job 41119 init, block 2 (orion-n17..n24, driver R570) ---
orion-n17:3107:3188 [0] NCCL INFO NET/IB : Using [0]mlx5_0:1/RoCE [1]mlx5_1:1/RoCE ... [7]mlx5_7:1/RoCE
orion-n17:3107:3188 [0] NCCL INFO Channel 00/0 : 0[0] -> 8[0] [send] via NET/IB/0
orion-n17:3107:3188 [0] NCCL INFO Channel 01/0 : 0[0] -> 8[0] [send] via NET/IB/0
# --- node checks, 2026-10-13 ---
$ ssh orion-n09 'lsmod | grep nvidia_peermem'
nvidia_peermem         16384  0
$ ssh orion-n17 'lsmod | grep nvidia_peermem'
$                                   # no output: module not loaded after the R570 install
"""

if __name__ == "__main__":
    raise SystemExit(main())
