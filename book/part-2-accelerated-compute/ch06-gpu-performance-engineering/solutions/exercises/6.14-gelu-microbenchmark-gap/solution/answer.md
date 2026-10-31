# 6.14 — A 12 % faster GELU, an unchanged step time (model answer, 10 points)

Relies on manuscript Section 6.1 (discipline), Section 6.6 (protocol) and Section 6.11 (troubleshooting
method). Arithmetic `[MODELED]`; `solve.py` asserts it.

## Mechanisms (4 points; at least three)

1. **Amdahl's law.** GELU is ≈ 4 % of step time; even a perfect 12 % cut on that share moves the step by
   0.48 %, below the ≈ 1 % noise floor. "Unchanged within noise" is the expected outcome.
2. **Shape mismatch.** At batch 1, hidden 4,096 the input is 1 × 4,096 × 2 B = 8,192 B: it fits in the 50 MB L2 and
   the kernel is launch- and latency-dominated. Production GELU streams hundreds of MB from HBM and is
   memory-bound; an improvement in the small-shape regime (fewer instructions, better launch config) may vanish
   at production shapes.
3. **Fusion in production.** With `torch.compile` or a fused MLP, GELU may already be fused into the preceding
   GEMM's epilogue, so the standalone kernel is never called in W-TRAIN.
4. **One-process measurement.** A median of 1,000 iterations in one process measures within-run noise only;
   the 12 % may partly be run luck (allocation, clocks, kernel selection).
5. **Different hardware state.** Clocks, thermal state or GPU model of the microbenchmark host vs production.

## Expected end-to-end gain (3 points)

If the kernel's time drops by 12 %: step change = 0.04 × 0.12 = **0.48 %**. If "12 % faster" means 1.12×
throughput, the kernel time drops by 1 − 1/1.12 = 10.7 % and the step by 0.04 × 0.107 = **0.43 %**. Either way
≈ 0.4–0.5 % at best, smaller than the noise floor, so it could never have been seen without a much larger
experiment.

## The experiment that would have predicted it (3 points)

1. Profile production first (nsys/PyTorch profiler on W-TRAIN): GELU's share of step time, whether it is a
   standalone kernel or fused, and its actual shapes and dtypes.
2. Benchmark old vs new kernel **at production shapes** on an ORION GPU with the full protocol: ≥ 5 fresh
   processes per arm, warm-up discarded, interleaved, A/A floor.
3. Predict the end-to-end change with Amdahl (share × kernel change) and compare it with the end-to-end noise
   floor and MDE *before* deploying; if the prediction is below the MDE, say so and do not claim an
   end-to-end win.
