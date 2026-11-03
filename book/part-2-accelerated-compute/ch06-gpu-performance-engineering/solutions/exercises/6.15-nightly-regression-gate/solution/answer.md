# 6.15 — Nightly performance-regression gate for ORION (model answer, 10 points)

Relies on manuscript Sections 6.5–6.8 and Section 6.11 (troubleshooting: node and driver confounds).
Budget arithmetic `[MODELED]`; `solve.py` checks it.

## Budget (2 points)

16 GPU-hours per night = **two dedicated HX8 nodes × 8 GPUs × 1 hour**. Reserved GPUs count whether or not a
stage uses all of them.

| Stage (both nodes in parallel) | Minutes | GPU-hours |
|---|---|---|
| Microbenchmark suite: GEMM BF16/FP8 at 3 shapes, LayerNorm, attention, on 2 GPUs per node | 20 | 5.33 |
| Single-node `all_reduce_perf`, 8 GPUs | 10 | 2.67 |
| End-to-end W-TRAIN proxy (TP = 8), 12 × 2-minute runs per node + 6 min setup: rotating node 6 candidate + 6 baseline interleaved; reference node 6 + 6 baseline (A/A) | 30 | 8.00 |
| **Total** | **60** | **16.0** |

## Workloads

Microbenchmarks localize a regression (which kernel, which library); the end-to-end proxy decides whether it
matters. Both are needed; neither alone blocks on its own without the other's context.

## Node selection and stratification (2 points)

One gate node rotates through the fleet nightly and runs the A/B comparison; its result is also compared with
**the same node's history** (stratify by node). The second is a fixed reference node that runs the A/A pair
every night: it sets that night's noise floor and separates software drift from node drift. Check the arithmetic:
end-to-end, each node runs 2 arms × 6 runs × 2 min = 24 min, plus 6 min setup = 30 min; 16 GPUs × 60 min = 16
GPU-hours.

## Clock policy

Production clocks with telemetry (`clocks_event_reasons`, SM clock, temperature); exclude runs with
non-routine limiters by the pre-registered rule. A separate weekly locked-clock benchmark tracks code
performance alone.

## Samples and decision rule (2 points)

6 runs per arm end to end (5 per arm in the microbenchmark stage), each a fresh process, interleaved
candidate/baseline; one 6 + 6 A/A pair per night on the reference node. Six runs per arm let the exact test reach
*p* = 2/924 ≈ 0.002; effects near 2 % are confirmed by a second night rather than by more runs in one night. **Block
promotion** if the exact permutation test on run medians gives *p* < 0.05 **and** the regression exceeds
max(A/A floor, 2 %); **warn** when the change lies between the floor and 2 %, or when *p* < 0.05 only on the
microbenchmarks.

## Keeping the A/A floor under 1 % (2 points)

Dedicated nodes, persistence mode, ≥ 10 warm-up iterations, pinned container digests, interleaving, same node
for both arms, NUMA pinning, and dropping nights whose A/A pair exceeds 1 % (the gate reports "inconclusive"
instead of passing).

## Rejected alternative (2 points)

Running the gate on whichever production nodes are free: cheaper and no reservation, but it confounds node,
power state, tenant and driver variation with the code change: the Section 6.11 failure, where a node
difference was mistaken for a driver regression. Dedicated, stratified nodes cost 16 GPU-hours and buy a
decision you can trust.
