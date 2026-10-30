# Lab 11 — W-TRAIN Step-Time, Memory, and Checkpoint-Interval Model

## 1. Goal and the real-world task it mirrors

Before a large training run starts, a training-infrastructure engineer is asked two questions: *which
parallel layout should we use on this cluster?* and *how often should we checkpoint?* The honest
answer is a model — memory per GPU, compute time, communication time on each link class, pipeline
bubble, and overlap — that ranks candidate layouts and tells you what to measure. You will build that
model for W-TRAIN (70B dense transformer) on ORION-256, use it to reject unsafe configurations and
recommend one, and add a checkpoint-interval / expected-lost-work calculator for ORION-256 and
ORION-XL.

## 2. Tier and realism boundary

**L1** (laptop, Python only, < 1 s). Every output is `[MODELED]`. The efficiency, bandwidth, latency,
and overlap parameters in `data/cluster_orion.yaml` are `[ILLUSTRATIVE]` assumptions. The model cannot
show GEMM efficiency changes with TP degree or micro-batch size, NCCL algorithm selection, congestion,
stragglers, allocator fragmentation, or real failure distributions. See manuscript Section
"Realism boundaries".

## 3. Setup

```bash
cd book/part-4-distributed-ai/ch11-distributed-training-architecture/lab
python -m pip install -r ../../../../requirements.txt     # pandas, pyyaml (numpy pulled in by pandas)
python check.py                                           # progress meter on starter/stepmodel.py
```

Python ≥ 3.10. Files: `data/model_wtrain.yaml`, `data/cluster_orion.yaml`, `data/candidates.csv`
(12 candidate layouts, shuffled), `data/reliability_scenarios.csv` (4 checkpoint scenarios).

## 4. Background

Manuscript Sections 11.2 (memory), 11.3–11.5 (DP/TP/PP volumes), 11.8 (placement), 11.9 (scaling),
11.10 (worked example), 11.12 (Young/Daly). Every formula you need is in the docstrings of
`starter/stepmodel.py`.

## 5. Tasks

1. **Validation and bubble (10 pts).** Implement `validate_config` and `bubble_fraction`.
   *Acceptance:* baseline returns `[]`; TP = 16 returns both `kv_heads_not_divisible_by_tp` and
   `tp_spans_nodes`; bubble(4, 128) = 0.0229.
2. **Memory (20 pts).** Implement `memory_per_gpu`. *Acceptance:* baseline = 12.03 GB model state +
   11.41 GB activations + 4.0 GB overhead = 27.44 GB. Then find, without running the checker, which
   candidates overflow 80 GB and which fit but violate the 68 GB headroom policy.
3. **Communication (20 pts).** Implement `allreduce_time_s` and `comm_model`. *Acceptance:* baseline
   TP = 1.203 TB, DP = 7.66 GB, PP = 2.15 GB per GPU per step; one 67 MB NVLink all-reduce ≈ 391 µs.
4. **Step time and recommendation (20 pts).** Implement `step_time` and `recommend`, then run
   `python starter/stepmodel.py` to print the full candidate table, recommendation, and checkpoint
   table. *Acceptance:* baseline 17.45 s and 39.9 % MFU; a
   recommendation that is valid, within headroom, and fastest.
5. **Checkpoint calculator (15 pts).** Implement `young_daly_interval_s`, `waste_fraction`, and
   `expected_lost_work_s`; produce `reliability_table`. *Acceptance:* ORION-256 synchronous τ_opt ≈
   66 min; ORION-XL synchronous τ_opt ≈ 16.4 min.
6. **Report (15 pts).** One page: the candidate table (sorted by step time), your recommendation with
   its memory headroom and risk, the planted traps and why each is unsafe, the checkpoint table, and
   which three assumptions you would measure first on real hardware.

## 6. Running the checker

```bash
python check.py                    # your starter implementation (TODO / FAIL / PASS per check)
python check.py --impl solution    # reference implementation (instructors)
```

The checker prints one line per check and exits non-zero until all 10 pass. It never crashes on
unimplemented functions; they show as `TODO`.

## 7. Deliverable and grading rubric (100 pts)

| Item | Points |
|---|---|
| Tasks 1–5 pass the checker (10 checks; partial credit per check) | 70 |
| Report: candidate table and recommendation with headroom/risk argument | 10 |
| Report: every planted trap identified with the reason (overflow, headroom, TP across nodes, GQA) | 10 |
| Report: checkpoint table plus investment recommendation (C vs R vs MTBF) | 5 |
| Report: assumptions to measure first, with method | 5 |

This lab plus Exercises 11.10–11.12 form the chapter deliverable: *parallelism design, timing model,
and recovery plan*.

## 8. Extensions (L2/L3)

**L2 — calibrate memory and compute on one 8-GPU host.** Run a scaled-down W-TRAIN-shaped model
(e.g., 8–16 layers, h = 8192) under Megatron-LM or PyTorch with TP = 8 on one node; flags such as
`--tensor-model-parallel-size 8 --sequence-parallel --micro-batch-size 1 --recompute-granularity
selective` exist in Megatron-LM `[VENDOR-SPEC, 2026-10 — verify for your version]`. Record:

```bash
nvidia-smi --query-gpu=index,name,memory.used,memory.total,clocks.sm,power.draw --format=csv -l 5
python -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.nccl.version())"
```

and, inside the training script, `torch.cuda.max_memory_allocated()` and
`torch.cuda.max_memory_reserved()` per rank after ≥ 20 warm-up steps. Compare peak memory per layer
with the model's s·b·h·34/t estimate, and measured step time with `compute_s` (scaled to your layer
count) to back out real kernel efficiency.

**L3 — validate the layout ranking on ≥ 2 nodes.** On two or more HX8-class nodes with rail-aligned
RDMA NICs, run the baseline and the recommended layout for ≥ 200 measured steps each after ≥ 20
warm-up steps, ≥ 3 repetitions, one variable changed at a time. Launch, e.g.:

```bash
srun --nodes=2 --ntasks-per-node=8 --gpus-per-node=8 --exclusive \
     python train.py --tensor-model-parallel-size 8 --pipeline-model-parallel-size 2 ...
# or: torchrun --nnodes=2 --nproc-per-node=8 --rdzv-backend=c10d --rdzv-endpoint=$HEAD:29500 train.py ...
```

Capture an Nsight Systems trace (`nsys profile -t cuda,nvtx -o step_trace python train.py ...`) for
exposed communication. Record in a copy of `manifest.yaml` (extension `L3`): nodes, tp/pp/dp,
micro_batch, zero_stage, NCCL/driver/firmware versions, topology, step_time p50/p95, MFU, exposed
communication, run_count, checkpoint_blocking_s, restart_s. Report measured versus modeled step time
and explain the gap.

> **Safety:** Run L3 only on a dedicated or reserved allocation. Do not change NCCL settings, power
> limits, or placement policies on shared production jobs.

## 9. Intentionally flawed inputs

The candidate list contains deliberate traps. Their identities and explanations are in
`../solutions/` (instructors only). Part of your grade is finding them yourself.
