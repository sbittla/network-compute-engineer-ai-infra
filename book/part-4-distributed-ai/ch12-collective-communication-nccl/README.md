# Chapter 12 — Collective Communication and NCCL

**Part IV — Distributed AI Systems · Course week 9 · Progressive Lab 5 (core lab)**

Every parallelism strategy from Chapter 11 becomes a collective — all-reduce, reduce-scatter,
all-gather, broadcast, all-to-all. This chapter explains each with small worked examples, costs them
with the alpha-beta model (ring, tree, in-network reduction), teaches the nccl-tests definitions of
`algbw` and `busbw`, opens NCCL's topology detection, channels, algorithms, and LL/LL128/Simple
protocols, covers the environment variables practitioners actually use, and shows how rank mapping
and NIC selection change performance. PyTorch Distributed (`init_process_group`, `torchrun`, NCCL and
gloo backends) ties it to training code.

## Learning objectives

1. Explain the six collectives with worked examples, including all-reduce = reduce-scatter + all-gather.
2. Calculate collective time with the alpha-beta model and identify latency-, transition-, and
   bandwidth-dominated regions.
3. Compute `algbw` and `busbw` from nccl-tests output and justify busbw as the comparison metric.
4. Describe NCCL topology detection, channels, rings/trees, and protocols.
5. Use NCCL debugging/control variables safely; initialize PyTorch Distributed with NCCL and gloo.
6. Diagnose rank-mapping/NIC-selection errors and degraded rails from benchmark evidence.
7. Produce a collective benchmark report with scaling and bottleneck analysis.

## Prerequisites

Chapter 11 (parallelism → collectives), Chapter 5 (HX8 topology, `nvidia-smi topo -m`), Chapter 8
(RDMA/RoCEv2 basics).

## Estimated time

| Activity | Time |
|---|---|
| Reading | 3 h |
| Exercises | 3.5 h |
| Lab (L1) | 3 h |
| L2/L3 extension (optional) | 3–6 h |

## Lab tier

L1 required (log analysis on simulated nccl-tests output); optional L1 gloo script (needs PyTorch);
L2/L3 extensions with real nccl-tests and perftest commands.

## Deliverable (course outline)

Collective benchmark report with scaling and bottleneck analysis (Exercises 12.11–12.12 + lab report).

## File map

| Path | Contents |
|---|---|
| [manuscript.md](manuscript.md) | Chapter text |
| [exercises.md](exercises.md) | Standard exercise set + outline-mandated exercises (12.10–12.12) |
| [lab/README.md](lab/README.md) | Lab guide |
| `lab/manifest.yaml` | Environment manifest |
| `lab/data/` | Six nccl-tests logs, configs, NCCL INFO excerpts (generated, seed 12) |
| `lab/tools/` | Data generator — instructor copy only (removed from the student release) |
| `lab/starter/nccl_analysis.py` | Learner module with TODOs |
| `lab/optional/gloo_allreduce.py` | Optional CPU-only PyTorch gloo sweep (not run by the checker) |
| `lab/check.py` | Automated checker |
| `solutions/` | Instructor answer key and reference implementation |
| [review/REVIEW.md](review/REVIEW.md) | Editorial review log |

## Connections

Builds on Chapters 5, 8, 11. Feeds Chapter 13 (byte-level data path, GPUDirect RDMA), Chapter 16
(nccl-tests in node acceptance), Chapter 22, and Capstone C.
