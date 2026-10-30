# Chapter 6 — GPU Performance Engineering

*Part II — Accelerated Compute · Course week 3 · Progressive Lab 4 (GPU baseline), part 2*

Knowing what a GPU should achieve and proving what it does: compute versus memory limits, arithmetic
intensity, the roofline with ORION's ceilings (dense-BF16 ridge ≈ 989 / 3.35 ≈ 295 FLOP/B), MFU and HFU,
why nvidia-smi utilization is not efficiency, clocks/power/thermal state as hidden variables, benchmark
protocols that control warm-up, repetitions, ordering, clocks, concurrency, input size and software
versions, and statistics — medians, IQR, run-level bootstrap confidence intervals, Cliff's delta, A/A noise
floors and practical thresholds — implemented without scipy. The worked example and lab show a naive
analysis reversing one decision and inventing another.

## Learning objectives

1. **Calculate** arithmetic intensity and **classify** kernels against the correct ceiling.
2. **Construct** an ORION roofline, place kernels on it, and **detect** physically inconsistent measurements.
3. **Compute** MFU and HFU and **explain** why GPU-Util is not SM efficiency.
4. **Design** a benchmark protocol with an environment manifest.
5. **Apply** robust statistics (median, IQR, bootstrap CI, Cliff's delta, noise floor) without scipy.
6. **Decide** whether an improvement is statistically and operationally meaningful and **identify** confounders.
7. **Operate** a performance-regression gate with explicit thresholds and safe actions.

## Prerequisites

[Chapter 4](../ch04-gpu-architecture-cuda-execution/) (execution model, profiling). Helpful:
[Chapter 5](../ch05-gpu-interconnects-host-topology/) (interconnect ceilings). Basic Python and numpy.

## Time budget

| Activity | Estimate |
|---|---|
| Reading | 2.5 h |
| Exercises | 3–4 h |
| Lab (L1) including `benchmark_report.md` | 4 h |
| Optional L2 extension | 2–3 h |

## Lab tiers

**L1** (required: CPU harness `[MEASURED]` on your machine; `[SIMULATED]` GPU result sets and kernel
counters) · **L2** (same protocol on a real GPU with CUDA events and telemetry).

## Deliverable (course outline)

*Reproducible benchmark harness, results table, and performance conclusion* — `harness.py`,
`results.json` and `benchmark_report.md` (Exercise 6.10).

## File map

| Path | Content |
|---|---|
| [manuscript.md](manuscript.md) | Chapter text (Sections 6.1–6.11, trade-offs, runbook, summary) |
| [exercises.md](exercises.md) | Exercises 6.1–6.19 including outline-mandated 6.11–6.13 |
| [lab/README.md](lab/README.md) | Lab 6 guide |
| `lab/manifest.yaml` | Environment manifest, decision protocol, L2 record fields |
| `lab/data/` | Benchmark result sets, A/A data, kernel counters, device ceilings |
| `lab/tools/generate_data.py` | Deterministic dataset generator (seed 6) — instructor copy only; removed from the student release because it encodes the planted faults |
| `lab/starter/harness.py`, `lab/starter/analysis.py` | Learner modules (TODOs) |
| `lab/check.py` | Checker: `python check.py [--impl starter\|solution]` |
| `solutions/` | Answer key and reference implementation (instructor only) |
| `review/REVIEW.md` | Editorial review log |

## Course placement

Week 3 — *GPU compute and interconnects* — after [Chapter 4](../ch04-gpu-architecture-cuda-execution/),
whose trace analysis this chapter turns into a repeatable baseline. The protocol is reused in Chapters 12,
16, 20 and 22 and in Capstone C.
