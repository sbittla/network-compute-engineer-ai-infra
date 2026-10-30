# Chapter 14 — Storage, Data Pipelines, and Checkpointing

**Part IV — Distributed AI Systems · Course week 11 · Progressive Lab 6**

A 256-GPU training job reads its dataset continuously, writes a checkpoint of nearly a terabyte
every few minutes, and must find, validate, and load the last good checkpoint whenever something
fails. This chapter follows those bytes along the host↔storage data path — GPU memory, PCIe, host
memory, local NVMe, the frontend fabric, and the parallel file system — and teaches the arithmetic
and operational checks behind three decisions: how to keep the input pipeline from being
metadata-bound, how to checkpoint (synchronously, asynchronously with PyTorch DCP or Megatron-LM, or
in multiple levels) at the right interval, and how to commit and validate checkpoints so that a
restart resumes correctly. Everything is grounded in W-TRAIN's 980 GB checkpoint on ORION-256.

## Learning objectives

1. **Explain** the host↔storage data path on an HX8 node and identify which hop bounds a workload.
2. **Calculate** NVMe throughput from queue depth and latency (Little's law), and checkpoint size,
   write time, overhead, and recovery point exposure for a stated model and storage bandwidth.
3. **Distinguish** a metadata-bound pipeline from a bandwidth-bound one using an I/O trace, and
   choose a data format and prefetch depth that removes the bottleneck.
4. **Design** a checkpoint strategy — synchronous, asynchronous, or multi-level — that balances
   overhead, storage capacity, restart time, and failure frequency, using the Young/Daly interval and
   a lost-accelerator-hours model.
5. **Describe** how PyTorch Distributed Checkpoint (DCP) and Megatron-LM structure sharded and
   asynchronous saves: staging buffers, consistency boundaries, and commit markers.
6. **Validate** a checkpoint before restore and select the latest valid one automatically.
7. **Diagnose** storage-induced training regressions with the diagnostic loop.
8. **Plan** a storage benchmark with warm-up, repetitions, percentiles, and an environment manifest.

## Prerequisites

Chapter 3 (Linux I/O tools), Chapter 5 (host topology, PCIe), Chapter 7 (frontend fabric),
Chapter 11 (W-TRAIN parallelism and sharded optimizer state), Chapter 13 (GPUDirect). Python and
basic statistics (percentiles).

## Estimated time

| Activity | Time |
|---|---|
| Reading | 3.5 h |
| Exercises (knowledge checks, worked problems, troubleshooting, design, reflection) | 4 h |
| Lab (L1) including memo | 4–5 h |
| Optional L2/L3 extensions | 3–6 h (hardware-dependent) |

## Lab tier(s)

**L1** (laptop): checkpoint planner `[MODELED]`, I/O trace analyzer and checkpoint validator on
`[SIMULATED]` data. **L2/L3 extensions:** fio NVMe acceptance, `dcp.save` vs `dcp.async_save`
timing and restore test, shared-PFS checkpoint and time-to-resume measurement.

## Deliverable (course outline)

**I/O benchmark plan and checkpoint/recovery design**, including (per the definitive-edition
integration map) a checkpoint benchmark, RPO/RTO analysis, and a restore test — Exercise 14.18
(and 14.19 at L2).

## File map

| Path | Contents |
|---|---|
| [manuscript.md](manuscript.md) | Chapter text (Sections 14.1–14.14, trade-offs, runbook, realism boundaries) |
| [exercises.md](exercises.md) | Exercises 14.1–14.19 (all outline-mandated exercises marked) |
| [lab/README.md](lab/README.md) | Progressive Lab 6 guide, rubric, L2/L3 extensions |
| `lab/manifest.yaml` | Environment manifest |
| `lab/data/` | Planner inputs, simulated I/O trace, simulated fio JSON, checkpoint store |
| `lab/tools/generate_data.py` | Seeded, byte-identical data generator (instructor copy only) |
| `lab/starter/storage_lab.py` | Learner module (functions raise `NotImplementedError`) |
| `lab/check.py` | Checker: `python check.py [--impl starter\|solution]` |
| `solutions/` | Instructor answer key and reference lab implementation |
| [review/REVIEW.md](review/REVIEW.md) | Editorial review log |

## Connections

Builds toward Chapter 18 (checkpoint and data-pipeline SLIs), Chapter 19 (failure isolation and
coordinated restart), Chapter 21 (pricing lost accelerator-hours), Chapter 15 (model-weight
loading), and Capstones A (storage sizing) and G (asynchronous checkpoint and restore plan at
512 nodes).
