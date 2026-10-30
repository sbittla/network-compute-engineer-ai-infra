# Capstone C — Exemplar Summary (abridged, distinction level)

INSTRUCTOR ONLY. Written as the learner would write it. Supplied-log results are `[SIMULATED]`, and the
harness result is `[MEASURED]` on a laptop as a CPU proxy only.

## 1. Summary

W-TRAIN's weak-scaling efficiency at 256 GPUs was 0.842 in the baseline. Every inter-node collective,
DP all-reduce and PP send/recv alike, ran over NCCL's TCP socket transport on the frontend network,
because the containers could not see the RDMA devices. Making the HCAs visible (`ib_gdr`) raised
efficiency to 0.979. The step-time speedup is 1.176 at 256 GPUs (bootstrap 95 % CI [1.169, 1.185];
exact permutation p = 0.00016, Holm-adjusted 0.0012 across 8 tests). It is significant at every scale,
including 1.1 % at 32 GPUs, where only PP traffic crosses nodes. The bucket-size change is not
significant at any scale (Holm p ≥ 0.34), and we do not recommend it on this evidence.

## 2. Method

- **Warm-up:** drop the first 5 steps of each run and after any restart. Step 0 is ≈ 3.1× steady state,
  and steps 1–4 decay to ≈ 1.03×.
- **Statistic:** median of steady steps per run, then the median of run medians, with min/max of run
  medians. Tests use an exact permutation test on the difference of means of run medians, with
  Holm–Bonferroni across the family of 8 tests (2 comparisons × 4 scales).
- **Design:** 8 repetitions per point. With 5 versus 4, the smallest exact p (1/126 ≈ 0.008) could
  never survive Holm over 8 tests.
- **Admissibility,** decided before looking at variant comparisons:

| Run | Decision | Reason |
|---|---|---|
| r0419 | exclude | Restarted at step 42 from the step-36 checkpoint (steps 36–41 repeat; second warm-up) |
| r0444 | exclude | Image `2026.09.3` and NCCL 2.21.5 differ from the variant's environment |
| r0458 | exclude | Median 19.22 s vs 17.96 s for its peers (+7.1 %). The manifest note records an SW thermal slowdown clock-event reason on orion-n19 GPU3 in 100 % of sampled steps, with SM clock ≈ 1,710 MHz vs ≈ 1,830 MHz on peers (−6.6 %) `[ILLUSTRATIVE]`. A synchronous job runs at its slowest GPU, so a −6.6 % clock explains a ≈ +7 % step |
| r0421 | exclude (rule), cause unknown | Flagged by the MAD outlier rule only. We report results with and without it and claim no cause |

Including all four moves no conclusion: the 256-GPU speedup stays at 1.176 (CI [1.167, 1.184]).

- **Harness** (`run_benchmark(4, 256, 1_000_000, 3, 10, 0)` on the author's laptop): median 22 ms, IQR
  1.6 ms, checksum stable across runs. The manifest records Python, numpy, BLAS and the CPU. It is
  labelled a `[MEASURED]` CPU proxy and is used only to validate the ring algorithm and the harness
  discipline.

## 3. Results

| Variant | E(64) | E(128) | E(256) |
|---|---|---|---|
| baseline | 0.907 | 0.863 | 0.842 |
| ib_gdr | 0.992 | 0.983 | 0.979 |
| ib_gdr_bucket | 0.991 | 0.987 | 0.982 |

**Model check** (docs/VERIFIED_FACTS.md: with PP, only the last micro-batch's backward, ≈ 70 ms, can hide
DP communication). DP bytes per GPU = 2(n−1)/n × 4.375 GB = 7.66 GB at DP = 8.

- **Baseline:** over sockets at ≈ 2.5 GB/s per GPU that takes ≈ 3.06 s, so ≈ 2.99 s is exposed. Add
  ≈ 0.2 s of exposed PP traffic and ≈ 17.8 s of compute including the slowest-node effect, and the
  prediction is ≈ 21.0 s. Observed: 21.12 s.
- **ib_gdr:** T_DP = 0.191 s, so max(0, 0.191 − 0.07) = 0.12 s is exposed (≈ 0.7 %). The remaining
  ≈ 1.2 % of the 2.1 % loss is the slowest-of-32-nodes effect: the expected maximum of 32 deviations is
  ≈ 2.0 σ, against ≈ 1.0 σ for 4 nodes.

## 4. Profiler and NCCL evidence

- At 256 GPUs, exposed communication is 15.3 % of the baseline step and 0.8 % for ib_gdr. The baseline
  spends ≈ 1.9 s per step in device↔host copies, the host-staged bounce-buffer path.
- The NCCL baseline log (excerpt `[ILLUSTRATIVE]`; wording varies by version) shows `NET/IB : No device
  found.`, then `Using network Socket`. In the ib_gdr log, channel lines read `via NET/IB/0/GDRDMA`. That
  suffix is the evidence that GPUDirect RDMA is in use.
- nccl-tests at 8 GiB, one node: ≈ 370 GB/s busbw (≈ 211 GB/s algbw) in both variants. That is a healthy
  plain ring. The ≈ 257 GB/s ceiling is the ring's *algbw* limit, so intra-node is not the problem.
- Two nodes: ≈ 20 GB/s busbw for the baseline versus ≈ 361 GB/s for ib_gdr, which is ≈ 45 GB/s per rail
  (busbw ÷ 8) against the 50 GB/s line rate.

## 5. Root cause and prevention

The pod spec did not request the RDMA device resource, so `/dev/infiniband` was absent in the container.
NCCL fell back silently to sockets, which is a correct behaviour that masked a platform defect.
**Prevention** (see `templates/runbook.md`): a launcher preflight fails any multi-node job whose rank-0
NCCL log reports `Using network Socket` on the backend partition. A scheduler-side alert fires when a
job's E(N) regresses by more than 3 % from its recorded baseline. RDMA devices are granted through the
device plugin, so training pods do not run privileged.

## 6. Next steps

1. **P0:** L3 confirmation on 4 → 32 nodes with ≥ 8 runs per point.
2. **P1:** retest the bucket change only if a profile shows exposed DP communication above 2 % of the step.
