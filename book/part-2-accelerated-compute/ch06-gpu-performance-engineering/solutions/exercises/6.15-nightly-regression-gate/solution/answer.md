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
| End-to-end W-TRAIN proxy (TP = 8, one node each), 6 × 3-minute runs incl. the A/A pair, plus setup | 30 | 8.00 |
| **Total** | **60** | **16.0** |

## Workloads

Microbenchmarks localize a regression (which kernel, which library); the end-to-end proxy decides whether it
matters. Both are needed; neither alone blocks on its own without the other's context.

## Node selection and stratification (2 points)

Rotate the two gate nodes through the fleet nightly, but compare each night's result against **the same
node's history** (stratify by node), plus one fixed reference node every night to separate software drift from
node drift.

## Clock policy

Production clocks with telemetry (`clocks_event_reasons`, SM clock, temperature); exclude runs with
non-routine limiters by the pre-registered rule. A separate weekly locked-clock benchmark tracks code
performance alone.

## Samples and decision rule (2 points)

≥ 6 runs per arm, each a fresh process, interleaved candidate/baseline; one A/A pair per night. **Block
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
