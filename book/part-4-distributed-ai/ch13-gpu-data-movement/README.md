# Chapter 13 — GPU-to-GPU and GPU-to-NIC Data Movement

**Part IV — Distributed AI Systems · Course week 9 · Progressive Lab 5 (with Chapters 11 and 12)**

Follows the bytes of a training step: NVLink/NVSwitch peer-to-peer inside the node; PCIe, locality,
and GPUDirect RDMA between GPU and NIC; the end-to-end path to a remote GPU with and without
GPUDirect RDMA (copies counted); compute/communication overlap with CUDA streams; straggler
amplification in synchronous training; and the cross-layer diagnosis of "GPU utilization low while
network utilization high" — communication vs synchronization vs data imbalance. Ends with a
vendor-labelled plan to validate GPUDirect RDMA and GPU/NIC locality on real hardware. Topology
*mapping* itself is taught in Chapter 5 and referenced, not repeated.

## Learning objectives

1. Trace a communication path GPU memory → PCIe → NIC → fabric → remote GPU, with and without
   GPUDirect RDMA, counting copies and crossings.
2. Explain NVLink P2P paths, GPU↔NIC locality classes, and their effect on bandwidth and variance.
3. Explain CUDA-stream overlap and calculate exposed communication.
4. Calculate straggler amplification.
5. Diagnose low GPU utilization with a busy network from per-rank telemetry; reject decoys.
6. Design measurements that validate GPUDirect RDMA and locality.
7. Produce an annotated data-path diagram and a cross-layer diagnosis.

## Prerequisites

Chapter 5 (topology mapping), Chapter 8 (RDMA), Chapters 11–12 (traffic and NCCL).

## Estimated time

| Activity | Time |
|---|---|
| Reading | 3 h |
| Exercises | 3.5 h |
| Lab (L1) | 2.5 h |
| L2/L3 extension (optional) | 3–6 h |

## Lab tier

L1 required (telemetry diagnosis); L2 instrumentation and L3 GPUDirect RDMA validation optional.

## Deliverable (course outline)

Annotated data-path diagram and cross-layer diagnosis (Exercises 13.9–13.10 + lab report).

## File map

| Path | Contents |
|---|---|
| [manuscript.md](manuscript.md) | Chapter text |
| [exercises.md](exercises.md) | Standard exercise set + outline-mandated exercises (13.9–13.11) |
| [lab/README.md](lab/README.md) | Lab guide |
| `lab/manifest.yaml` | Environment manifest |
| `lab/data/` | Telemetry bundle and job manifest (generated, seed 13) |
| `lab/tools/` | Data generator — instructor copy only (removed from the student release) |
| `lab/starter/telemetry_diag.py` | Learner module with TODOs |
| `lab/check.py` | Automated checker |
| `solutions/` | Instructor answer key and reference implementation |
| [review/REVIEW.md](review/REVIEW.md) | Editorial review log |

## Connections

Builds on Chapters 5, 8, 11, 12. Feeds Chapter 18 (dashboards and alerts), Chapter 19 (fault
isolation), Chapter 22 (cross-layer performance), and Capstones C and G.
