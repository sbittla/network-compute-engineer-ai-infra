# Chapter 1 — The AI Infrastructure Landscape

**Course week 1** (shared with Chapter 2) · Part I — Foundations

An AI training cluster behaves as one synchronous computer whose speed is set by its slowest component
and whose reliability is set by its least reliable one; an inference fleet is a set of tightly coupled
replicas judged on latency percentiles. This chapter builds that mental model with numbers from ORION,
the book's 256-GPU reference cluster: training versus inference reference architectures, scale-up
(NVLink) versus scale-out (RDMA) communication, a ceiling model that classifies workloads as compute-,
memory-, communication-, or I/O-bound, the economics of utilization and failure, and the employer and
role landscape. The lab builds a workload-characterization tool that also catches the flawed data
real capacity reviews contain.

## Learning objectives

1. **Explain** five ways an AI cluster differs from a conventional cloud fleet and give a number for
   each on ORION.
2. **Draw** reference architectures for a training workload and an online-inference workload, and
   identify their compute, network, storage, orchestration, and observability dependencies.
3. **Calculate** per-step communication volume for tensor-parallel and data-parallel traffic and
   **decide** which belongs in the scale-up domain and which on the scale-out fabric.
4. **Classify** a workload as compute-, memory-, communication-, or I/O-bound from a resource profile,
   and **name** the telemetry that would confirm the classification.
5. **Diagnose** a cross-layer slowdown with the diagnostic loop.
6. **Map** employer groups and engineering roles to the skills in this book, and **build** a
   role-to-skill matrix for your target role.

## Prerequisites

Linux command line, basic Python, IP networking fundamentals. No CUDA, RDMA, or ML background needed.

## Time budget

| Activity | Estimate |
|---|---|
| Reading the manuscript | 2.5–3 h |
| Exercises (mandated + standard set) | 4–5 h |
| Lab (L1) | 2–3 h |
| L2/L3 extension (optional) | 3–4 h with hardware access |

## Lab tier

L1 (laptop; synthetic, `MODELED`). Optional L2 (one GPU node) and L3 (multi-node RDMA) extensions.

## Deliverable (from the course outline)

Annotated architecture diagrams (training and online inference) and a one-page workload comparison
(Exercises 1.1–1.2 and the lab's `comparison.md`), plus the role-to-skill matrix (Exercise 1.3).

## File map

| Path | Contents |
|---|---|
| [manuscript.md](manuscript.md) | Chapter text |
| [exercises.md](exercises.md) | Mandated exercises 1.1–1.3, knowledge checks, worked problems, lab, troubleshooting, design, reflection |
| [lab/README.md](lab/README.md) | Workload-characterization lab guide |
| `lab/data/` | Synthetic profiles and ORION ceilings (the seeded generator in `lab/tools/` is instructor material) |
| `lab/starter/workload_model.py` | Learner implementation (TODOs) |
| `lab/check.py` | Checker: `python check.py [--impl starter|solution]` |
| `solutions/` | Instructor answer key and reference lab implementation |
| [review/REVIEW.md](review/REVIEW.md) | Editorial review log |

## Connections

Builds toward Chapter 2 (data-center anatomy), Chapter 3 (host diagnostics), Chapters 5–6 (topology,
roofline), 7–10 (networking), 11–13 (distributed training and NCCL), 15 (inference), 19 and 21
(reliability, capacity, cost), 22 (cross-layer performance), 24 (careers), and Capstones A and D.
