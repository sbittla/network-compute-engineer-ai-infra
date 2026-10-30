# Chapter 6 — Exercises

Difficulty: ★ foundational · ★★ intermediate · ★★★ advanced. Tier: **L1** laptop/paper · **L2** single GPU
host · **L3** multi-node. Use ORION ceilings (Table 6.1: 989 TFLOP/s dense BF16, 1,979 FP8, 67 FP32 SIMT,
3.35 TB/s HBM) unless stated. Label every number and show formula → substitution → result.

**Chapter deliverable (course outline):** *reproducible benchmark harness, results table, and performance
conclusion* — produced by Exercise 6.10 (the lab) and its `benchmark_report.md`.

---

## Knowledge checks

**6.1** ★ L1 — Define arithmetic intensity and the ridge point; compute the ridge for dense BF16, FP8 and
FP32 SIMT on ORION. *Evidence required:* definitions and three ridge values with arithmetic.

**6.2** ★ L1 — Why is an elementwise kernel's performance judged in GB/s and a large GEMM's in TFLOP/s?
*Evidence required:* intensity argument for both.

**6.3** ★ L1 — A profiled kernel shows 4.6 TB/s of "DRAM" bandwidth on an ORION GPU. Give two explanations
and say what you would check. *Evidence required:* two mechanisms, one counter or experiment each.

**6.4** ★ L1 — Define MFU and HFU. Why can HFU exceed MFU, and which should you report when comparing two
clusters? *Evidence required:* formulas, recomputation argument, recommendation.

**6.5** ★ L1 — List five sources of run-to-run variation on a GPU benchmark and one control for each.
*Evidence required:* five source–control pairs.

**6.6** ★★ L1 — Why is the run, not the iteration, the unit of replication? What goes wrong with a CI
computed from 300 iterations of one run? *Evidence required:* correlation argument and consequence.

**6.7** ★★ L1 — What do `clocks_event_reasons` report, what were they called on older drivers, and how
does hardware slowdown differ from software thermal slowdown? *Evidence required:* definition, legacy
names, ordering of thresholds.

## Worked problems

**6.8** ★★ L1 — *Intensity and batch size.* For a BF16 linear layer with *K* = *N* = 4,096: (a) for *M* =
4,096 tokens compute *W*, minimum *Q*, *I*, the bound and the time at roof; (b) repeat for *M* = 64;
(c) find the smallest *M* for which the layer is compute-bound on ORION. *Evidence required:* all
arithmetic; label `[MODELED]`.

**6.9** ★★ L1 — *MFU.* A 13 × 10⁹-parameter dense model trains on 64 ORION GPUs with 512 sequences ×
4,096 tokens per step at 5.2 s per step; nvidia-smi shows 98 % utilization. (a) MFU; (b) HFU with full
activation recomputation; (c) the MFU someone would report using the FP8 peak by mistake; (d) what the
98 % tells you. *Evidence required:* three numbers with arithmetic and one explanation.

## Hands-on lab

**6.10** ★★ L1 (L2 extension) — Complete [Lab 6](lab/README.md): harness, statistics, decisions,
roofline, and `benchmark_report.md`. *Evidence required:* checker output (all PASS), `results.json` with
5 runs, and the report per the lab rubric.

## Outline-mandated exercises

**6.11** ★★ L1 — *Roofline from supplied data.* Classify and express as a fraction of the binding roof:

| Kernel | Precision | FLOP | DRAM bytes | Measured time |
|---|---|---|---|---|
| K1 softmax | BF16 | 1.0 × 10⁹ | 1.6 × 10⁹ | 0.60 ms |
| K2 GEMM | BF16 | 4.4 × 10¹² | 0.6 × 10⁹ | 7.4 ms |
| K3 decode attention | BF16 | 8.6 × 10⁹ | 2.15 × 10⁹ | 0.75 ms |
| K4 reduction | FP32 SIMT | 2.0 × 10¹¹ | 0.4 × 10⁹ | 5.0 ms |

Rank them by optimization opportunity and name the lever for each. *Evidence required:* table with
intensity, ridge, bound, fraction of roof; ranked list with levers.

**6.12** ★★ L1 — *Benchmark protocol.* Write a one-page protocol for comparing two NCCL versions'
all-reduce performance on two ORION nodes, controlling warm-up, repetitions, concurrency, input size,
software versions and measurement noise, with a pre-registered decision rule. *Evidence required:* the
protocol with every control and the decision rule; manifest fields.

**6.13** ★★ L1 — *Is the improvement real?* Run medians (ms) for an inference kernel: baseline 12.41,
12.37, 12.52, 12.44, 12.39, 12.47; candidate 12.10, 12.22, 12.05, 12.31, 12.95, 12.12. The candidate's
fifth run logged `sw_power_cap` on most iterations. The A/A floor is 0.9 %; the practical threshold is 2 %.
Using the lab's `permutation_test` and `bootstrap_ratio_ci` (seed 11, 4,000 replicates), decide with and without the fifth run
and justify which decision stands. *Evidence required:* medians, relative changes, p-values, bootstrap bands, decisions,
justification.

## Troubleshooting case

**6.14** ★★★ L1 — A kernel team reports their new GELU kernel is 12 % faster (microbenchmark at batch 1,
hidden 4,096, median of 1,000 iterations in one process). After deployment, W-TRAIN step time is
unchanged within noise. GELU accounts for ≈ 4 % of step time in the production profile. Explain the
discrepancy with at least three mechanisms, quantify the expected end-to-end gain, and design the
experiment that would have predicted it. *Evidence required:* mechanisms, Amdahl arithmetic, experiment design.

## Design challenge

**6.15** ★★★ L1 — Design a nightly performance-regression gate for ORION (32 HX8 nodes) with a budget of
16 GPU-hours per night. Choose workloads (microbenchmarks vs end-to-end), node selection and
stratification, clock policy, sample sizes, decision thresholds, what blocks a promotion, and how you keep
the A/A floor under 1 %. Defend one choice against a rejected alternative. *Evidence required:* a design
with budget arithmetic, the decision rule, and the rejected alternative.

## Reflection and review

**6.16** ★ L1 — Your laptop harness showed a 10–20 % run-to-run spread. Which manifest fields would you
inspect, and why does this not invalidate the supplied GPU analysis?

**6.17** ★ L1 — In the worked example, Cliff's δ for candidate C is −0.28 on iterations but −0.67 on run
medians, while the change is only 0.50 %. Explain the difference and what it says about relying on effect
sizes alone.

**6.18** ★★ L1 — Which of this chapter's numbers would change if ORION ran with a 500 W power cap, and how
would you re-baseline?

**6.19** ★ L1 — Name one decision in the lab's protocol you would change for a serving-latency SLO
benchmark, and why.

**6.20** ★★ L1 — Suppose the protocol had no version-mismatch rule, so run A3 (PyTorch 2.3.1) stays in the
baseline. Recompute the C vs A comparison with the lab code and explain why exclusion rules must be
pre-registered and applied symmetrically to every arm.

*Evidence required for 6.16–6.20:* short written answers (≤ 150 words each) citing specific mechanisms or data.
