# Chapter 5 — GPU Interconnects and Host Topology

*Part II — Accelerated Compute · Course week 3 · Implements course-outline Section 20.4 (NUMA geometry,
multi-rail mapping and GPUDirect RDMA)*

How bytes move inside an 8-GPU server and out to the fabric: PCIe hierarchy and bandwidth, ACS, NVLink
and NVSwitch, peer-to-peer versus host-staged transfers (counting the copies), NUMA and CPU affinity, and
— in depth — topology discovery from `nvidia-smi topo -m`, `lstopo`/hwloc, `lspci` and LLDP, producing a
machine-readable GPU UUID/BDF → NIC/HCA BDF, NUMA, slot and rail mapping. The chapter teaches how to
verify GPUDirect RDMA instead of assuming it, treats multi-rail assignment as a joint placement problem,
and quantifies with a labelled model how two flawed nodes halve a 128-GPU job's all-reduce bandwidth.

## Learning objectives

1. **Explain** the PCIe hierarchy and **calculate** per-direction bandwidth for a generation and width.
2. **Compare** NVLink/NVSwitch P2P, PCIe P2P and host-staged transfers, counting copies and sync points.
3. **Interpret** `nvidia-smi topo -m` labels (X, NV#, PIX, PXB, PHB, NODE, SYS) and `lstopo` output and
   **identify** the shortest GPU–NIC pairings.
4. **Build** a machine-readable GPU→NIC/HCA/NUMA/slot/rail mapping, cross-checking independent sources.
5. **Validate** GPUDirect RDMA prerequisites and **demonstrate** that the path is active.
6. **Design** rank/GPU/NIC/rail placement as a joint problem and **model** aligned vs misaligned
   all-reduce bandwidth and variance with stated assumptions.
7. **Plan** hardware validation with nccl-tests and NCCL's topology output.

## Prerequisites

[Chapter 3](../../part-1-foundations/ch03-linux-host-systems-diagnostics/) (NUMA, `lspci`, sysfs) and
[Chapter 4](../ch04-gpu-architecture-cuda-execution/) (copies, pinned memory, streams).

## Time budget

| Activity | Estimate |
|---|---|
| Reading | 2.5–3 h |
| Exercises | 3–4 h |
| Lab (L1) including `topology_report.md` | 4 h |
| Optional L2 capture / L3 nccl-tests comparison | 2 h / 4 h |

## Lab tiers

**L1** (required: parse raw captures of four hosts, build the mapping CSV, detect faults, run the
`[MODELED]` all-reduce comparison) · **L2** (capture a real host) · **L3** (aligned vs misaligned
nccl-tests on ≥ 2 nodes).

## Deliverable (course outline)

*Topology map, locality recommendations, and validation checklist*; from Section 20.4: raw topology
outputs, annotated topology diagram, GPU-to-HCA mapping CSV, aligned/misaligned benchmark methodology and
results (measured if hardware is available, otherwise labelled modeled), and limitations — all in the
lab's `topology_report.md` (Exercises 5.10, 5.14).

## File map

| Path | Content |
|---|---|
| [manuscript.md](manuscript.md) | Chapter text (Sections 5.1–5.12, trade-offs, runbook, summary) |
| [exercises.md](exercises.md) | Exercises 5.1–5.21 including outline-mandated 5.11–5.15 |
| [lab/README.md](lab/README.md) | Lab 5 guide |
| `lab/manifest.yaml` | Environment manifest (L1) and L2/L3 record fields |
| `lab/data/hosts/` | Raw captures for `orion-n01`, `-n02`, `-n17`, `-n23` |
| `lab/data/path_model.yaml` | `[ILLUSTRATIVE]` path-class parameters for the `[MODELED]` all-reduce estimate |
| `lab/tools/generate_data.py` | Deterministic dataset generator (seed 5) — instructor copy only; removed from the student release because it encodes the planted faults |
| `lab/starter/topo_mapper.py` | Learner module (TODOs) |
| `lab/check.py` | Checker: `python check.py [--impl starter\|solution]` |
| `solutions/` | Answer key and reference implementation (instructor only) |
| `review/REVIEW.md` | Editorial review log |

## Course placement

Week 3 — *GPU compute and interconnects* — with [Chapter 4](../ch04-gpu-architecture-cuda-execution/) and
[Chapter 6](../ch06-gpu-performance-engineering/). The mapping CSV is reused in Chapters 12, 16, 17 and 19
and in Capstones A and G.
