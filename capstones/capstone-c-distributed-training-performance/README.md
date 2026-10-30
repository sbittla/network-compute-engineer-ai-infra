# Capstone C: Distributed Training Performance Optimization

W-TRAIN, the 70B dense model, "doesn't scale" on ORION: per-GPU throughput at 256 GPUs is about 16 %
below the 32-GPU run. Two changes have been tried, and the team cannot agree whether either helped.
You will build a reproducible benchmark harness and an environment manifest. You will then analyze
baseline and optimized multi-run results, quantify scaling efficiency with honest uncertainty,
connect the numbers to profiler and NCCL evidence, and write the root-cause narrative. This is the
daily work of an AI performance engineer. The hard part is rarely the fix. It is proving which runs
count, which differences are real, and why.

## Audience and prerequisites

**Audience (course outline, Section 16):** GPU/HPC engineer, AI Performance Engineer.

**Recommended preparation:** Chapters [6](../../book/part-2-accelerated-compute/ch06-gpu-performance-engineering/),
[11](../../book/part-4-distributed-ai/ch11-distributed-training-architecture/),
[12](../../book/part-4-distributed-ai/ch12-collective-communication-nccl/),
[13](../../book/part-4-distributed-ai/ch13-gpu-data-movement/) and
[22](../../book/part-5-production-operations/ch22-cross-layer-performance-engineering/); plus
[5](../../book/part-2-accelerated-compute/ch05-gpu-interconnects-host-topology/) (GPU↔NIC locality) and
[17](../../book/part-5-production-operations/ch17-kubernetes-slurm-scheduling/) (how RDMA devices reach containers).

## Scenario

Training Infra runs W-TRAIN on ORION ([REFERENCE_CLUSTER.md](../../docs/REFERENCE_CLUSTER.md) §3) as a
weak-scaling family. One replica is TP = 8 inside a node × PP = 4 across nodes, which is 32 GPUs.
Data parallelism adds replicas up to 256 GPUs. Platform moved training into containers last month. Since
then, multi-node efficiency has drifted down, and nobody has looked at an NCCL log. Two candidate
fixes were run: Platform corrected the pod spec so RDMA devices are visible in the container
(`ib_gdr`), and a Training Infra engineer raised the DDP gradient bucket size (`ib_gdr_bucket`). You
receive 96 runs' worth of logs and manifests, a profile summary, nccl-tests sweeps and NCCL debug
excerpts. Some runs should not be used.

## Problem statement

Determine whether W-TRAIN's scaling loss is real, find its root cause, and establish which of the two
changes produce a statistically supported improvement at which scales. The method must be one another
engineer can rerun on hardware. Success means:

1. a harness and manifest that make every measurement reproducible and correctly labelled;
2. an admissibility decision for every run, with reasons;
3. weak-scaling efficiency per variant with run-to-run spread, and speedups with p-values and CIs;
4. a root-cause narrative tying the scaling loss to a mechanism, backed by profiler and NCCL evidence;
5. an honest statement about the change that did not help.

## Required artifacts

The first six rows are the Capstone C artifacts from the course outline (Section 16). The remaining
rows are required of every capstone.

| Artifact | Template / location | Expected evidence label |
|---|---|---|
| Reproducible benchmark harness | `starter-kit/starter/harness.py`, [benchmark-plan.md](templates/benchmark-plan.md) | `[MEASURED]` (L1 CPU proxy) |
| Environment manifest | [environment-manifest.yaml](templates/environment-manifest.yaml) | — |
| Baseline and optimized measurements | [results-table.csv](templates/results-table.csv) | `[SIMULATED]` supplied logs; `[MEASURED]` if L2/L3 |
| Scaling-efficiency analysis | [scaling-analysis.md](templates/scaling-analysis.md) | `[SIMULATED]` |
| Profiler evidence | [profiler-evidence.md](templates/profiler-evidence.md) | `[SIMULATED]` |
| Root-cause narrative | [root-cause-narrative.md](templates/root-cause-narrative.md) | — |
| Problem statement; architecture; assumptions | [performance-report.md](templates/performance-report.md) §1–3, [assumptions-register.csv](templates/assumptions-register.csv) | |
| Implementation or simulation boundary | [performance-report.md](templates/performance-report.md) §4 | |
| Test plan; results | [benchmark-plan.md](templates/benchmark-plan.md), [results-table.csv](templates/results-table.csv) | kept apart by label |
| Failure analysis; security considerations | [performance-report.md](templates/performance-report.md) §9–10, [runbook.md](templates/runbook.md) (launcher preflight, scaling-regression alert) | |
| Final engineering review | [final-engineering-review.md](templates/final-engineering-review.md) | |

## Milestones

| Milestone | Week | What you hand in |
|---|---|---|
| M0: choose | 8 | Capstone choice; skim the logs and manifests; list suspicious runs |
| M1: proposal | 10 | Problem statement, benchmark plan v1, harness checks H1–H4 passing, one harness JSON |
| M2: analysis | 12 | Checks A1–A6 passing; admissibility and scaling tables |
| M3: draft | 13 | All checks; profiler evidence; root-cause narrative; peer review booked |
| M4: final | 14 | Complete report, final engineering review, 15-minute presentation |

## Tier options

| Tier | Scope | What it adds |
|---|---|---|
| **L1 (required)** | [starter-kit](starter-kit/): CPU-proxy harness + analysis of supplied logs | Full marks achievable with correct labels |
| **L2 (optional)** | Port the harness to PyTorch Distributed on one 8-GPU node; nsys capture; intra-node nccl-tests | `[MEASURED]` single-node evidence |
| **L3 (optional)** | Multi-node nccl-tests and training proxy with RDMA, ≥ 5 runs per configuration | `[MEASURED]` scaling evidence |

**Advanced extension (course outline):** multi-node GPU tests with NCCL and supported RDMA hardware;
clearly report run-to-run variation and limitations. The procedure is in the
[starter-kit README, Section 8](starter-kit/README.md#8-extensions-l2l3-procedure).

> **Realism boundary:** The supplied logs come from a step-time model, not a cluster. The CPU harness
> measures your laptop. Neither says anything about how fast ORION's GPUs or fabric really are. What
> transfers is the method: warm-up policy, repetitions, admissibility rules, significance testing, and
> reading NCCL's own account of which transport it used.

## How the chapters map to the artifacts

| Artifact | Chapters |
|---|---|
| Harness, manifest, benchmark discipline | 6, 22 |
| Scaling analysis (weak vs strong, collective bytes) | 11, 12 |
| Profiler evidence, NCCL transport, GPUDirect RDMA | 6, 12, 13 |
| Root cause (container RDMA visibility) | 13, 16, 17 |

## Grading

Graded with the [capstone rubric](../RUBRIC.md). For Capstone C, excellent work looks like this:

| Dimension | What excellent looks like in Capstone C |
|---|---|
| Problem framing and assumptions (10) | Weak vs strong scaling is chosen and justified; warm-up and outlier rules are written down before the results |
| Architecture and technical correctness (20) | Collective byte counts and the GPU→NIC→fabric path are right; the baseline's real path (socket transport, host bounce buffers) is drawn |
| Implementation / reproducibility (15) | All 12 checks pass; harness JSON with manifest; one command regenerates every table |
| Measurement and analysis (20) | Every run's admissibility is decided; efficiencies carry spread; speedups carry exact p-values and CIs; the non-significant change is reported as such |
| Reliability, security and operations (15) | A launcher preflight that fails jobs on the wrong transport; RDMA device exposure handled by policy, not by privileged pods |
| Troubleshooting and engineering judgment (10) | Hypotheses ranked and discriminated with intra- vs inter-node evidence; proven cause separated from correlation |
| Communication and portfolio quality (10) | A reviewer can see the 16 % gap, its cause and the fix in one page |

## File map

```text
capstone-c-distributed-training-performance/
├── README.md            this brief
├── templates/           report, benchmark plan, manifest, results, scaling, profiler evidence,
│                        root-cause narrative, assumptions, final review
├── starter-kit/         L1 harness + analysis: data/, tools/ (instructor edition only), starter/{harness,analysis}.py, check.py
├── instructor/          grading guide, exemplar, reference implementation (removed in student edition)
└── review/REVIEW.md     editorial review log
```
