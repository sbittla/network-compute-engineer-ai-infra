# Chapter 22 — Cross-Layer Performance Engineering

**Part V — Operating Production AI Infrastructure · Course week 14 (with Chapters 23 and 24)**

A training job is one synchronous machine built from GPUs, hosts, PCIe, NICs, fabric, storage, a
scheduler, and software. When its step time regresses after a change window in which several teams
changed several things, the cause can sit in any layer. This chapter integrates the book into one
method: decompose the step, build a hypothesis tree, rank discriminating tests by information value,
cost, and risk, attribute the regression across simultaneous changes from a natural experiment,
analyse scaling efficiency, tune one evidence-backed change at a time, and write a before/after report
that separates measured facts, inferred causes, and remaining uncertainty. The worked example and lab
use ORION and the W-TRAIN workload; the troubleshooting scenario traces a "network" slowdown to a
thermal straggler.

## Learning objectives

1. **Decompose** a training step into compute, exposed communication, pipeline bubble, data wait, and
   host overhead, and **name** the evidence source that measures each term on ORION.
2. **Define** a regression precisely (metric, population, statistic, window, noise floor) and
   **explain** why mean, median, and p99 can tell different stories about the same change.
3. **Build** a hypothesis tree for a cross-layer regression and **rank** candidate tests by information
   value, cost, and risk, rejecting tests that are unsafe for production.
4. **Design** discriminating tests whose predicted outcomes differ under competing hypotheses.
5. **Attribute** a regression to simultaneous changes using a natural experiment, **quantify**
   uncertainty, and **recognise** confounding, collinearity, and interaction.
6. **Calculate** weak- and strong-scaling efficiency and the minimum detectable effect of a benchmark,
   and **use** them to decide whether a claimed improvement is real.
7. **Write** a before/after report that separates measured facts, inferred causes, and remaining
   uncertainty, and **avoid** the common anti-patterns.

## Prerequisites

Chapters 3, 5, 6, 9, 11–14, 16–18, and 20 (see the manuscript's "Prerequisites and connections").
Comfort with pandas and basic least-squares regression helps for the lab.

## Estimated time

| Activity | Time |
|---|---|
| Reading | 3.5 h |
| Exercises (knowledge checks, worked problems, troubleshooting, design, reflection) | 4 h |
| Lab (L1) | 3 h |
| Optional L2/L3 extension | 2–4 h on reserved hardware |

## Lab tier

**L1** (laptop, < 10 s runtime, `[SIMULATED]` bundle). L2/L3 extensions confirm the GPUDirect RDMA and
placement mechanisms with `all_reduce_perf` on reserved nodes.

## Deliverable (course outline)

**Evidence-based root-cause report and validated optimization**: the lab's before/after report, edited
for the change owners, with a validation plan (predicted effect, canary scope, MDE, abort condition) for
each recommended fix (Exercise O3).

## File map

| Path | Contents |
|---|---|
| [manuscript.md](manuscript.md) | Chapter text |
| [exercises.md](exercises.md) | Standard exercise set + outline-mandated exercises O1–O3 |
| [lab/README.md](lab/README.md) | Lab guide: attribute a cross-layer W-TRAIN regression |
| `lab/manifest.yaml` | Environment manifest (tier, seed, extensions) |
| `lab/data/` | Multi-source bundle: jobs, step log, placement, inventory, node metrics, alerts, change log, candidate tests |
| `lab/tools/generate_data.py` | Seeded generator (seed 2214) — instructor copy only, removed from the student release |
| `lab/starter/regression_lab.py` | Learner module with TODOs |
| `lab/check.py` | Checker: `python lab/check.py [--impl starter\|solution]` |
| `solutions/` | Instructor only: exercise key, planted-flaw list, reference implementation |
| [review/REVIEW.md](review/REVIEW.md) | Editorial review log |

## Connections

Builds on Chapters 3–20; applied in [Chapter 23](../../part-6-applied-engineering/ch23-capstone-production-ai-cluster/)
and [Capstone C](../../../capstones/capstone-c-distributed-training-performance/),
[Capstone B](../../../capstones/capstone-b-network-telemetry-troubleshooting/), and
[Capstone F](../../../capstones/capstone-f-reliability-game-day/).
