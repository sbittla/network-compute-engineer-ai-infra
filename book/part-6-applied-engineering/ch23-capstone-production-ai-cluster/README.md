# Chapter 23 — Capstone: Design and Operate a Production-Scale AI Cluster

**Part VI — Applied Engineering · Course week 14 · Lab tier L1 (L2/L3 extensions)**

A practitioner's guide to executing a production-scale AI-cluster design-and-operate project end to
end: framing the problem and an assumptions register, recording Architecture Decision Records
(ADRs), checking a design's internal arithmetic, failure-domain analysis with a goodput model,
running a design review with a 40-item checklist, assembling benchmark evidence that separates
measured from modeled values, running a safe failure exercise, presenting, and prioritising a
next-step backlog. A fully worked mini-capstone on the ORION reference cluster ties Chapters 1–22
together. The lab builds a design-review linter that checks a capstone design bundle for
completeness and internal consistency before humans review it.

The capstone briefs are in [`capstones/`](../../../capstones/) (Tracks A–H) and are scored with
[`capstones/RUBRIC.md`](../../../capstones/RUBRIC.md).

## Learning objectives

1. **Frame** an AI-cluster design problem as a workload model, objectives, constraints and an
   assumptions register in which every load-bearing number has a label, an owner and a validation
   plan.
2. **Record** architecture decisions as ADRs that state the options considered, the evidence used
   and the condition that would reopen the decision.
3. **Verify** a design's internal consistency (counts, port budgets, oversubscription, cables, rack
   power, checkpoint bandwidth) by explicit arithmetic and with an automated linter.
4. **Analyse** failure domains from GPU to facility and estimate the goodput cost of failures with
   the Young/Daly checkpoint model.
5. **Run** a design review using a structured checklist, classify findings by severity and reach an
   explicit outcome.
6. **Assemble** benchmark evidence that separates measured, modeled, simulated and illustrative
   values, with manifests, repetitions and spread.
7. **Design** and execute a safe failure exercise (tabletop or isolated lab) and report detection
   time, recovery time and lost GPU-hours.
8. **Present** the capstone and a prioritised next-step backlog to a technical audience.

## Prerequisites

Chapters 1–22, in particular Chapter 2 (data-centre anatomy), Chapter 11 (parallelism), Chapter 14
(checkpointing), Chapter 19 (failure domains), Chapter 21 (capacity and power) and Chapter 22
(cross-layer performance engineering). Python 3.10+, `pyyaml`.

## Estimated time

| Activity | Time |
|---|---|
| Read manuscript | 3–4 h |
| Exercises (excluding the capstone itself) | 4–6 h |
| Lab (L1) | 3–4 h |
| Capstone project (outline-mandated) | 25–40 h across week 14 and preceding weeks |

## Deliverable (course outline)

**Complete capstone portfolio**: one capstone track (A–H) with problem statement, assumptions
register, architecture and ADRs, failure-domain analysis, benchmark evidence table, failure-exercise
report, a design-review record (checklist, findings, outcome), the linter report for your bundle,
presentation, and a prioritised next-step backlog.

## File map

| Path | Content |
|---|---|
| [manuscript.md](manuscript.md) | Chapter text (≈ 10,000 words) |
| [exercises.md](exercises.md) | Standard exercise set plus outline-mandated exercises |
| [lab/README.md](lab/README.md) | Lab guide: design-review linter |
| `lab/manifest.yaml` | Environment manifest |
| `lab/data/` | Two design bundles: `bundle_orion_reference/` (consistent), `bundle_kestrel_capA/` (flawed) |
| `lab/tools/generate_bundles.py` | Deterministic generator for `data/` (seed 23) — instructor copy only, removed from the student release |
| `lab/starter/design_lint.py` | Learner module with TODOs |
| `lab/check.py` | Checker: `python check.py [--impl starter\|solution]` |
| `solutions/` | Instructor-only answer key and reference linter |
| [review/REVIEW.md](review/REVIEW.md) | Editorial review log |

## Connections

Builds on every earlier chapter (see manuscript Table 23.1). Applied directly in Capstones A–H.
Feeds [Chapter 24](../ch24-career-paths-engineering-practice/) (turning the capstone into a portfolio
and an interview presentation) and reuses the hypothesis-ranking and before/after reporting method
of [Chapter 22](../../part-5-production-operations/ch22-cross-layer-performance-engineering/).
