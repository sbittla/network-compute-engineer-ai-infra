# Chapter 11 — Distributed Training Architecture

**Part IV — Distributed AI Systems · Course week 9 · Progressive Lab 5 (with Chapters 12 and 13)**

A 70B-parameter model needs ≈ 1.1 TB of training state and ≈ 1.8 × 10¹⁸ FLOP per step, so it is cut
across hundreds of GPUs — and every cut creates communication. This chapter explains data (DDP,
ZeRO/FSDP), tensor, pipeline, sequence/context, and expert parallelism as traffic patterns with
measurable bytes, frequency, and latency sensitivity; accounts for memory and communication per GPU on
the ORION reference cluster; places each pattern on NVLink or the rails; models step time, bubble,
MFU, and scaling efficiency; and designs a failure-aware workflow using the Young/Daly checkpoint
interval.

## Learning objectives

1. Explain the mechanism and per-step communication pattern of DP, ZeRO/FSDP, TP, PP, CP, and EP.
2. Calculate per-GPU memory and identify configurations that overflow an 80 GB GPU.
3. Calculate per-GPU communication volume per step per dimension and convert it into time.
4. Design a topology-aware placement (TP inside NVLink; DP/PP rail-local).
5. Estimate step time, bubble, MFU, and strong/weak scaling efficiency, including sensitivity to
   compute, communication, and synchronization.
6. Diagnose stragglers, hangs, and rank loss from their signatures.
7. Design a failure-aware workflow: checkpoint interval, restart, and expected lost work.

## Prerequisites

Chapters 4 and 5 (GPU execution, HX8 topology), Chapter 7 (rail-optimized leaf-spine). Python and
basic linear algebra. No ML training experience required.

## Estimated time

| Activity | Time |
|---|---|
| Reading | 3.5 h |
| Exercises | 4 h |
| Lab (L1) | 2.5 h |
| L2/L3 extension (optional) | 4–8 h |

## Lab tier

L1 required (pure Python model). L2/L3 optional extensions calibrate the model on real GPUs.

## Deliverable (course outline)

Parallelism design, timing model, and recovery plan — Exercises 11.10–11.12 plus the lab report.

## File map

| Path | Contents |
|---|---|
| [manuscript.md](manuscript.md) | Chapter text |
| [exercises.md](exercises.md) | Standard exercise set + outline-mandated exercises (11.10–11.12) |
| [lab/README.md](lab/README.md) | Lab guide: step-time/memory model and checkpoint calculator |
| `lab/manifest.yaml` | Environment manifest |
| `lab/data/` | W-TRAIN, ORION, candidate configs, reliability scenarios (generated) |
| `lab/tools/` | Data generator — instructor copy only (removed from the student release) |
| `lab/starter/stepmodel.py` | Learner module with TODOs |
| `lab/check.py` | Automated checker |
| `solutions/` | Instructor answer key and reference implementation |
| [review/REVIEW.md](review/REVIEW.md) | Editorial review log |

## Connections

Builds on Chapters 4, 5, 7. Feeds Chapter 12 (collectives), Chapter 13 (data movement and
stragglers), Chapter 14 (checkpoint storage), Chapter 19 (fault isolation), Chapter 22 (cross-layer
performance), and Capstones C and G.
