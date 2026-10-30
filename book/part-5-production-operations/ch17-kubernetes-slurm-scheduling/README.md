# Chapter 17 — Kubernetes, Slurm, and Workload Scheduling

**Part V — Operating Production AI Infrastructure · Course week 8 · Progressive Lab 7 (part 2)**

A GPU cluster is only as productive as the decisions that put work onto it. This chapter explains how
Kubernetes (device plugin, extended resources, GPU Operator, labels/taints, Topology Manager, MIG,
time-slicing, DRA) and Slurm (`gres`, partitions, QOS, fair share, `topology.conf`, node states) turn
physical GPUs into schedulable resources; how gang scheduling, quotas, priority, and fair share decide
who runs; how topology decides where; and how to diagnose the most common platform ticket — a job
pending despite apparently free GPUs — on the ORION reference cluster.

## Learning objectives

1. **Explain** how a GPU becomes a schedulable resource in Kubernetes and Slurm, and where physical
   and schedulable counts diverge.
2. **Configure** labels, selectors, taints, tolerations, MIG, and time-slicing so that work lands only
   where intended, and read the YAML and `slurm.conf` that express those intents.
3. **Calculate** gang feasibility, fragmentation, quota headroom, fair-share ordering, and the
   GPU-hour cost of partial-allocation deadlock and preemption.
4. **Design** a workload placement policy that considers GPU type, topology, rail health, quotas,
   fairness, and gang placement.
5. **Compare** Kubernetes and Slurm for interactive inference, batch training, and tightly coupled
   multi-node jobs.
6. **Diagnose** a job pending despite free GPUs from scheduler, device-plugin, topology, quota, and
   node-health evidence, using the diagnostic loop.
7. **Integrate** scheduler state with the Chapter 16 node lifecycle.

## Prerequisites

Chapter 5 (HX8 host topology), Chapter 7 (rail-optimized fabric), Chapter 11 (parallelism layout),
Chapter 15 (serving), and Chapter 16 (node lifecycle — Progressive Lab 7 part 1). Linux and Python
literacy; no Kubernetes or Slurm experience is assumed.

## Time budget

| Activity | Time |
|---|---|
| Reading (manuscript) | 2.5–3 h |
| Exercises | 3–4 h |
| Lab (L1) | 3–4 h |
| L2/L3 extensions (optional) | 2–4 h |

## Lab tier

**L1** (required): standard-library Python simulator and diagnoser over a synthetic ORION snapshot,
< 5 s. **L2/L3** (optional): reproduce pending causes on a lab GPU node; measure placement effects with
`all_reduce_perf` on ≥ 2 RDMA nodes.

## Deliverable (from the course outline)

**Workload placement policy and scheduling troubleshooting guide** (exercise 17-DEL, built from 17-M2
and 17-M3, with the lab placement report as appendix).

## File map

| Path | Contents |
|---|---|
| [manuscript.md](manuscript.md) | Chapter text |
| [exercises.md](exercises.md) | Knowledge checks, worked problems, lab, troubleshooting case, design challenge, mandated exercises, reflection, deliverable |
| [lab/README.md](lab/README.md) | Lab guide (Progressive Lab 7, part 2) |
| `lab/manifest.yaml` | Environment manifest |
| `lab/data/` | `cluster_state.json`, `job_queue.json`, `pending_cases.json` (seed 17) |
| `lab/tools/generate_data.py` | Seeded dataset generator — instructor copy only (stripped from the student release) |
| `lab/starter/orion_sched.py` | Learner module with TODOs |
| `lab/check.py` | Checker: `python check.py [--impl starter\|solution]` |
| `solutions/` | Instructor only: answer key and reference implementation |
| [review/REVIEW.md](review/REVIEW.md) | Editorial review log |

## Connections

Builds on [Chapter 16](../ch16-bare-metal-fleet-lifecycle/) (node lifecycle). Feeds
[Chapter 18](../ch18-observability-slos-incident-response/) (scheduling SLIs),
[Chapter 19](../ch19-reliability-security-multitenancy/) (tenant isolation),
[Chapter 20](../ch20-automation-safe-change/) (policy as code, safe rollout),
[Chapter 21](../ch21-capacity-power-economics/) (utilization and fragmentation), and Capstones E and G.
