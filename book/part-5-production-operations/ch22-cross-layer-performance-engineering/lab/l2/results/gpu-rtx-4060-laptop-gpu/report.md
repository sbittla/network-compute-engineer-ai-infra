# Lab 22 L2: inject a regression on one GPU and attribute it with the lab's method

`[MEASURED]` on **NVIDIA GeForce RTX 4060 Laptop GPU**, 2026-11-01T00:06:20Z.

| Environment | Value |
|---|---|
| device | cuda |
| cpu_model | 13th Gen Intel(R) Core(TM) i7-13700HX |
| cpu_count | 24 |
| mem_total_gib | 7.8 |
| os | Linux-6.18.54.1-microsoft-standard-WSL2-x86_64-with-glibc2.35 |
| torch | 2.5.1+cu124 |
| cuda_runtime | 12.4 |
| driver_version | 592.82 |
| pcie.link.gen.max | 4 |
| pcie.link.width.max | 8 |
| clocks.max.sm | 3105 |
| power.limit | [N/A] |

**Status:** ran
**Invariants:** all passed

## Measured facts

- Input batch 32.0 MiB; H2D pinned 10.39 GB/s, pageable 6.356 GB/s `[MEASURED]`.
- Controlled A/B, median step (ms; ≥ 5 reps after 3 warm-ups):

| Configuration | median | p95 | IQR | n |
|---|---|---|---|---|
| baseline | 16.90 | 17.26 | 0.271 | 30 |
| pageable | 19.55 | 21.66 | 2.064 | 30 |
| small_batch | 22.84 | 28.38 | 0.397 | 30 |
| both | 27.83 | 34.82 | 3.984 | 30 |

- Natural experiment: 48 jobs, per-job mean step after - before = **+9.04 ms**. Before-period spread σ = 0.187 ms per job mean, so MDE ≈ 2.8 σ √(2/n) = 0.185 ms (Section 22.6.1).

## Attribution (estimator: solutions/lab/regression_lab.py (estimate_effects, attribute, bootstrap_shares; TERMS swapped))

| Term | Effect (ms/step) ± SE HC3 (factors) | Exposure change | Contribution (ms) | Share | Bootstrap 95 % share interval |
|---|---|---|---|---|---|
| common shift (period indicator) | +3.02 | 1.000 | +3.02 | 33.4 % ± 10.8 pp | 14 to 55 % |
| pageable H2D input (injected) | +6.02 ± 2.12 | 0.500 | +3.01 | 33.3 % ± 11.8 pp | 11 to 55 % |
| micro-batches + grad accumulation (injected) | +6.55 ± 1.18 | 0.500 | +3.27 | 36.2 % ± 6.5 pp | 20 to 53 % |
| placebo flag (no change) | -1.33 ± 1.47 | 0.500 | -0.66 | -7.3 % ± 8.1 pp | -24 to 8 % |
| interaction pageable x small_batch | +1.59 ± 2.96 | 0.250 | +0.40 | 4.4 % ± 8.2 pp | -11 to 22 % |
| residual |  |  | +0.00 | 0.0 % |  |

R² = 0.806.

## Corroboration (Table 22.6: statistical, direct, mechanism model)

| Factor | OLS (ms) | Direct A/B (ms) | Mechanism model (ms) | Verdict |
|---|---|---|---|---|
| pageable H2D input (injected) | +6.02 ± 2.12 | +2.65 ± 0.35 | +2.05 | inconclusive: SE too large for this effect |
| micro-batches + grad accumulation (injected) | +6.55 ± 1.18 | +5.93 ± 0.08 |  | inferred cause, corroborated |
| interaction pageable x small_batch | +1.59 ± 2.96 | +2.34 ± 0.77 |  | inconclusive: SE too large for this effect |
| placebo flag (no change) | -1.33 ± 1.47 | +0.00 ± 0.00 |  | ruled out (no effect) |

## What to conclude

- Recovery of the injected regressions, read from the verdict column: micro-batches + grad accumulation (injected): recovered and corroborated (OLS +6.55 vs +5.93 ms direct); pageable H2D input (injected): direction recovered, but OLS +6.02 ms is 2.3× the +2.65 ms direct A/B; inconclusive at this n. The placebo gives -1.33 ± 1.47 ms (verdict: ruled out (no effect)). A factor that happens to coincide with an incident is not its cause.
- Mechanism: 32.0 MiB at the slower copy rate costs +2.05 ms per step, 77 % of the +2.65 ms measured in the A/B, so direct and mechanism evidence agree; the statistical estimate is too noisy to add support, and the cause rests on the A/B and the model. The unexplained remainder is host-side cost a bandwidth number does not capture (staging-buffer management, cache effects).
- The common shift (+3.02 ms, 16× the 0.185 ms MDE, 33 % of the +9.04 ms delta) is large: the before-jobs ran first, so block-order drift (temperature, clocks) dominates it. Interleave before and after jobs, or add a drift covariate, before trusting the shares.
- This is a **laptop Ada GPU** on PCIe Gen4 x8, not an HX8 node. The lab's W-TRAIN factors (TP split, GDR host-staging across nodes, storage tier) need multi-node hardware (L3). This run validates the *method* on regressions whose truth is known.

- 16 before-jobs, then 32 after-jobs (8 per pageable x small_batch cell, order shuffled, placebo on a random half); 30 steps per job, the first 5 dropped as warm-up.
- All timings are host wall clock around a synchronized step (CUDA events would miss host-side staging).
- Before-jobs run first and after-jobs second, as in production. Slow drift (GPU temperature, clocks) therefore lands in the 'after' common-shift term, exactly the confounding Section 22.4.3 warns about.
