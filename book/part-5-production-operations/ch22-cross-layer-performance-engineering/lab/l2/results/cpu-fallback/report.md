# Lab 22 L2: inject a regression on one GPU and attribute it with the lab's method

`[MEASURED]` on **CPU fallback: 13th Gen Intel(R) Core(TM) i7-13700HX**, 2026-11-01T00:07:15Z.

| Environment | Value |
|---|---|
| device | cpu |
| cpu_model | 13th Gen Intel(R) Core(TM) i7-13700HX |
| cpu_count | 24 |
| mem_total_gib | 7.8 |
| os | Linux-6.18.54.1-microsoft-standard-WSL2-x86_64-with-glibc2.35 |
| torch | 2.5.1+cu124 |
| cuda_runtime | 12.4 |

**Status:** ran
**Invariants:** all passed

## Measured facts

- Input batch 4.0 MiB; H2D contiguous 12.453 GB/s, strided gather 1.065 GB/s `[MEASURED]`.
- Controlled A/B, median step (ms; ≥ 5 reps after 3 warm-ups):

| Configuration | median | p95 | IQR | n |
|---|---|---|---|---|
| baseline | 15.75 | 20.23 | 3.961 | 30 |
| pageable | 22.42 | 26.18 | 4.670 | 30 |
| small_batch | 24.66 | 30.50 | 2.241 | 30 |
| both | 31.14 | 40.18 | 3.440 | 30 |

- Natural experiment: 48 jobs, per-job median step after - before = **+8.46 ms**. Before-period spread σ = 0.456 ms per job median, so MDE ≈ 2.8 σ √(2/n) = 0.451 ms (Section 22.6.1).

## Attribution (estimator: solutions/lab/regression_lab.py (estimate_effects, attribute, bootstrap_shares; TERMS swapped))

| Term | Effect (ms/step) ± SE HC3 (factors) | Exposure change | Contribution (ms) | Share | Bootstrap 95 % share interval |
|---|---|---|---|---|---|
| common shift (period indicator) | -0.11 | 1.000 | -0.11 | -1.3 % ± 2.2 pp | -6 to 3 % |
| strided fp64 input gather (injected) | +6.73 ± 0.23 | 0.500 | +3.36 | 39.8 % ± 1.3 pp | 28 to 53 % |
| micro-batches + grad accumulation (injected) | +10.32 ± 0.18 | 0.500 | +5.16 | 61.0 % ± 1.0 pp | 48 to 73 % |
| placebo flag (no change) | +0.06 ± 0.15 | 0.500 | +0.03 | 0.4 % ± 0.9 pp | -1 to 2 % |
| interaction pageable x small_batch | +0.05 ± 0.30 | 0.250 | +0.01 | 0.2 % ± 0.9 pp | -2 to 2 % |
| residual |  |  | +0.00 | 0.0 % |  |

R² = 0.9966.

## Corroboration (Table 22.6: statistical, direct, mechanism model)

| Factor | OLS (ms) | Direct A/B (ms) | Mechanism model (ms) | Verdict |
|---|---|---|---|---|
| strided fp64 input gather (injected) | +6.73 ± 0.23 | +6.67 ± 1.04 | +3.60 | inferred cause, corroborated |
| micro-batches + grad accumulation (injected) | +10.32 ± 0.18 | +8.90 ± 0.77 |  | inferred cause, corroborated |
| interaction pageable x small_batch | +0.05 ± 0.30 | -0.19 ± 1.25 |  | agree (≈ 0) |
| placebo flag (no change) | +0.06 ± 0.15 | +0.00 ± 0.00 |  | ruled out (no effect) |

## What to conclude

- The lab's estimator, fed real per-job means, recovers both injected regressions within their uncertainty (pageable +6.73 vs +6.67 ms direct; small batch +10.32 vs +8.90 ms) and gives the placebo +0.06 ± 0.15 ms. A factor that happens to coincide with an incident is not its cause.
- The data-path effect is also explained by mechanism: 4.0 MiB at the slower copy rate costs +3.60 ms per step, 54 % of the +6.67 ms measured in the A/B. Statistical, direct and mechanism evidence agree, so it is a strong inferred cause. The unexplained remainder is the host-side cost a bandwidth number does not capture (staging-buffer management, cache effects).
- The common-shift term (-0.11 ms) absorbs whatever drifted between the before and after blocks, such as temperature or clocks. Compare it with the MDE before calling it real.
- _CPU fallback: no GPU was visible, so the data-path factor is a strided gather on the host rather than a pageable PCIe copy. The design, estimator and corroboration are identical. GPU-only invariants (PCIe ceiling, pinned >= pageable) were skipped._

- 16 before-jobs, then 32 after-jobs (8 per pageable x small_batch cell, order shuffled, placebo on a random half); 50 steps per job, the first 5 dropped as warm-up.
- All timings are host wall clock around a synchronized step (CUDA events would miss host-side staging).
- Before-jobs run first and after-jobs second, as in production. Slow drift (GPU temperature, clocks) therefore lands in the 'after' common-shift term, exactly the confounding Section 22.4.3 warns about.
