# Capstone C starter kit: benchmark harness and scaling analysis

This kit has two halves. The **harness** (`starter/harness.py`) is a reproducible benchmark harness
that runs at L1 on any laptop. It contains a CPU numpy proxy of a data-parallel step (matmul compute,
then a ring all-reduce) with warm-up, repetitions, percentiles and an environment manifest. The same
structure carries over to the L2/L3 PyTorch/NCCL procedure in Section 8. The **analysis**
(`starter/analysis.py`) works on supplied multi-run logs of W-TRAIN on ORION: 3 variants, 4 scales
and 5 repetitions. You must decide which runs are admissible, compute weak-scaling efficiency, test
whether each "optimization" is real, and connect the result to profiler and NCCL evidence.

> **Realism boundary:** The supplied run logs, profile summary and NCCL logs are `[SIMULATED]` by a
> step-time model (compute + exposed communication + slowest-node maximum + noise). The harness's
> timings are `[MEASURED]` on *your laptop* and are evidence of nothing about GPUs, NVLink, NICs or NCCL.
> The checker never tests a timing value. Physical claims about ORION require the L3 procedure.

## 1. Goal and the real-world task it mirrors

Training Infra reports that W-TRAIN "doesn't scale": per-GPU throughput at 256 GPUs is about 16 % below
the 32-GPU run. Two changes have been tried. Your job is the performance engineer's: build a harness
you trust, decide which runs count, quantify scaling and the effect of each change with honest
uncertainty, and explain the mechanism with profiler and NCCL evidence.

## 2. Tier and realism

| Tier | What you do | Evidence class |
|---|---|---|
| L1 (required) | Harness + analysis; all checks pass | harness `[MEASURED]` (CPU proxy); analysis `[SIMULATED]` |
| L2 (optional) | Port the harness to PyTorch Distributed on one 8-GPU node; nsys capture | `[MEASURED]` on that node |
| L3 (optional) | Multi-node NCCL and training-step runs with RDMA; ≥ 5 reps per configuration | `[MEASURED]` on that cluster |

## 3. Setup

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r ../../../requirements.txt
# (instructor edition only) python tools/generate_data.py regenerates data/ byte-identically
python check.py
```

## 4. The supplied data (`data/`)

| File | Contents |
|---|---|
| `runs.csv` | `run_id, variant, n_gpus, rep, step, step_time_s, tokens` for 96 runs: 3 variants × 4 scales × 8 repetitions (60 steps each, in log order) |
| `manifests.csv` | One environment manifest per run (image, PyTorch, CUDA, driver, NCCL, NCCL network, GDR, RDMA devices in container, bucket size, notes) |
| `profile_summary.csv` | nsys-style per-step breakdown in **milliseconds**: busy and exposed time per category, at 32 and 256 GPUs |
| `nccl_tests.csv` | `all_reduce_perf` sweeps (1 MiB–8 GiB): 8 GPUs in one node and 16 GPUs on two nodes. Reference points from [VERIFIED_FACTS.md](../../../docs/VERIFIED_FACTS.md) `[VENDOR-SPEC, 2026-10]`: on one 8 × H100-class node a plain ring reaches busbw ≈ 0.80–0.85 × 450 ≈ 360–380 GB/s (its **algbw** ceiling is ≈ 450 / 1.75 ≈ 257 GB/s); busbw near 450 GB/s implies NVLS. Across ORION nodes with all 8 rails expect ≈ 350+ GB/s busbw, i.e. ≈ 44 GB/s per rail (busbw ÷ 8) against the 50 GB/s line rate. The `nccl_debug_*.log` excerpts are `[ILLUSTRATIVE]`: exact wording varies by NCCL version |
| `nccl_debug_*.log` | `NCCL_DEBUG=INFO` excerpts from rank 0 of each variant |

**Experiment design.** Weak scaling over data parallelism: one W-TRAIN replica is TP = 8 × PP = 4 =
32 GPUs (4 nodes) with 128 sequences of 4,096 tokens. DP = 1, 2, 4, 8 gives 32, 64, 128 and 256 GPUs;
at 256 the global batch is W-TRAIN's 1,024 sequences. There is no 8-GPU training point, because W-TRAIN's
≈ 1.12 TB of training state does not fit in one node's 640 GB of HBM `[MODELED]`. The 8-GPU evidence is
the intra-node `all_reduce_perf` sweep.

**Variants** (each changes one thing from the previous):

| Variant | Change |
|---|---|
| `baseline` | As deployed |
| `ib_gdr` | Pod spec fixed so the RDMA devices are visible in the container |
| `ib_gdr_bucket` | `ib_gdr` + DDP `bucket_cap_mb` 25 → 100 |

## 5. Background

[Chapter 11](../../../book/part-4-distributed-ai/ch11-distributed-training-architecture/) (parallelism,
weak vs strong scaling), [Chapter 12](../../../book/part-4-distributed-ai/ch12-collective-communication-nccl/)
(NCCL transports, `NCCL_DEBUG`, nccl-tests bus bandwidth),
[Chapter 13](../../../book/part-4-distributed-ai/ch13-gpu-data-movement/) (GPUDirect RDMA, bounce buffers),
[Chapter 6](../../../book/part-2-accelerated-compute/ch06-gpu-performance-engineering/) (profiling) and
[Chapter 22](../../../book/part-5-production-operations/ch22-cross-layer-performance-engineering/)
(benchmark discipline, significance, the diagnostic loop).

## 6. Tasks (100 points)

| # | Task | Acceptance criterion | Points |
|---|---|---|---|
| 1 | Harness: `ring_allreduce`, `summarize`, `capture_manifest`, `run_benchmark` | H1–H4 pass; one harness result (JSON) in your pack with manifest | 15 |
| 2 | `steady_state`, `run_summary`, `validate_runs` | A1–A3 pass; admissibility table with reasons in the pack | 15 |
| 3 | `scaling_table` | A4 passes; weak-scaling table and chart with spread | 15 |
| 4 | `permutation_pvalue`, `holm`, `compare_variants`, `compare_family` | A5–A6 pass; comparison table with the test statistic stated, raw and Holm-adjusted p-values (8 tests) and CIs; a sentence on why 5 runs per point could not have survived the correction | 15 |
| 5 | `exposed_comm`, `nccl_transport`; read `nccl_tests.csv` | A7–A8 pass; profiler-evidence summary | 15 |
| 6 | Root-cause narrative using the diagnostic loop | `templates/root-cause-narrative.md` | 15 |
| 7 | L2/L3 procedure written as a runnable plan (or executed) | `templates/benchmark-plan.md` | 10 |

## 7. Running the checker

```bash
python check.py
python check.py --impl solution    # instructor edition only
```

## 8. Extensions: L2/L3 procedure

> **Safety:** Use nodes allocated to you. Do not change NCCL, NIC or switch settings on shared
> production systems. Benchmark runs on a shared fabric disturb other tenants. Book the partition.

All environment variables and flags below are `[VENDOR-SPEC, 2026-10]`; verify them against the
NCCL, PyTorch and nccl-tests documentation for your versions.

```bash
# Topology and RDMA visibility (on every node, inside the container the job will use)
nvidia-smi topo -m
ibv_devinfo                                   # empty output inside the container = the baseline's defect
ls /dev/infiniband/

# Collective bandwidth, 2 nodes x 8 GPUs, after warm-up iterations (-w) and with repetitions (-n)
mpirun -np 16 -H nodeA:8,nodeB:8 -x NCCL_DEBUG=INFO -x NCCL_DEBUG_SUBSYS=INIT,NET \
    ./build/all_reduce_perf -b 1M -e 8G -f 2 -g 1 -w 5 -n 20

# Training-step proxy with PyTorch Distributed, one launcher per node
torchrun --nnodes 4 --nproc_per_node 8 --rdzv_backend c10d --rdzv_endpoint <host>:29500 train_proxy.py

# Profile a few steady-state steps on one rank
nsys profile -t cuda,nvtx,osrt -o step_profile --capture-range=cudaProfilerApi python train_proxy.py
```

Check the NCCL log for `Using network IB` versus `Using network Socket`, and for `/GDRDMA` on channel
lines. `NCCL_IB_HCA` restricts which HCAs NCCL uses and `NCCL_NET_GDR_LEVEL` controls when GPUDirect
RDMA is used. Change them only as a controlled experiment, one at a time. Record everything listed
under `extensions` in `manifest.yaml`, run at least 5 repetitions per configuration after a stated
warm-up, and report the median with min/max or IQR.

## 9. Deliverable

Filled templates in [`../templates/`](../templates/), your two modules, and checker output.
