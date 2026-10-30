# Lab 12 — Instructor Notes

Reference implementation: `nccl_analysis.py` (passes `python ../../lab/check.py --impl solution`).
`python nccl_analysis.py` prints the summary table and labels.

## Planted problems

| Config | Planted cause (generator parameters) | Signature in the data | What a learner should conclude |
|---|---|---|---|
| `c3_2node_alt_map` | `NCCL_IB_HCA` limited to the four socket-0 HCAs and `NCCL_PXN_DISABLE=1`; GPUs 4–7 use NICs 2–3 across the inter-socket link without GPUDirect RDMA. Simulated with B = 185 GB/s, α = 39 µs, normal noise | Steady plateau ≈ 184 GB/s (CV ≈ 0.008), α +11 µs vs c2; NCCL excerpt shows 4 HCAs and `via NET/IB/2` without `GDRDMA` | Mapping/NIC-selection problem; half of node egress unused; verify with INFO log, env, `nvidia-smi topo -m`, per-NIC counters |
| `c6_8node_run2` | Node `orion-n12` replaced `orion-n08`; its rail-3 link has CRC errors → RoCE retransmissions. Simulated with B = 190 GB/s and 9 % lognormal jitter on sizes ≥ 1 MiB | Low plateau ≈ 177 GB/s *and* jitter CV ≈ 0.09; in-place vs out-of-place disagree by up to 20 %; header shows the node change | Degraded link on one node/rail; isolate with pairwise tests, per-rail `ib_write_bw`, RDMA/PHY counters (manuscript Section 12.13) |
| All files | "Avg bus bandwidth" averages over all sizes | 66–170 GB/s vs plateaus of 177–449 GB/s | Never use it as the bandwidth figure |

## Expected summary (`[SIMULATED]` data, `[MODELED]` fit)

| Config | Plateau | α (µs) | B (GB/s) | n½ (MB) | CV | Label |
|---|---|---|---|---|---|---|
| c1 | 449 | 14.1 | 448 | 3.6 | 0.007 | ok |
| c2 | 352 | 28.1 | 354 | 5.3 | 0.009 | ok |
| c3 | 184 | 39.2 | 185 | 3.9 | 0.008 | low_plateau_steady |
| c4 | 349 | 36.2 | 349 | 6.5 | 0.011 | ok |
| c5 | 345 | 47.3 | 346 | 8.3 | 0.016 | ok |
| c6 | 177 | 49.8 | 185 | 4.7 | 0.088 | low_plateau_jittery |

## Grading notes

- Common parser bug: assuming a fixed decimal count for the time column (it switches to 1 and 0
  decimals at 100 µs and 10 ms), or splitting on fixed character positions.
- Common analysis bug: unweighted least squares — α comes out negative or wildly wrong because the
  8 GiB rows dominate the residual. Accept any fit that recovers α within ±15 % and B within ±5 %.
- Learners who label c6 only "low" without noticing the jitter lose the distinction between
  mapping and link-health problems — deduct in the report section, not the checker.
