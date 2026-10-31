# 10.W2 — FEC arithmetic and sparing at ORION-XL scale

All values `[MODELED]` from the prompt's `[ILLUSTRATIVE]` inputs. Method: Sections 10.2.1, 10.4.3
and 10.12.

**(a) 800G line rate and codeword rate**

```text
line rate = 800 Gb/s × (257/256) × (544/514) = 800 × 1.0625 = 850 Gb/s   (8 lanes × 106.25 Gb/s)
codewords = 850e9 b/s / 5,440 b per codeword = 156.25 × 10⁶ codewords/s
```

256b/257b transcoding adds 0.39 %, RS(544,514) adds 5.84 %; together exactly 1.0625.

**(b) Margin and fraction of codewords with ≥ 1 symbol error at BER 2 × 10⁻⁵**

```text
margin = log10(2.4e-4 / 2e-5) = log10(12) = 1.08 decades
p      ≈ 10 × BER = 2 × 10⁻⁴ per 10-bit symbol
544p   = 0.1088
P(≥1)  = 1 − e^(−0.1088) = 0.103
```

About 10 % of codewords are corrected, ≈ 0.103 × 156.25e6 ≈ 1.6 × 10⁷ per second on one 800G port.
That is normal PAM4 behaviour with more than a decade of margin; it is not a fault on its own (only
uncorrectables, a falling margin or a rising trend are).

**(c) Poisson sparing for 16,384 optics, AFR 1.5 %, lead time 21 days**

```text
λ = N × AFR × L/365 = 16,384 × 0.015 × 21/365 = 14.14 expected failures per lead time
P(X ≤ k) = Σ_{i=0}^{k} e^(−λ) λ^i / i!
```

| k | 18 | 19 | 20 | 21 | 22 | 23 | 24 |
|---|---|---|---|---|---|---|---|
| P(X ≤ k) | 0.875 | 0.918 | 0.948 | 0.968 | 0.982 | 0.990 | 0.994 |

≥ 95 %: **21 spares** (P(X ≤ 20) = 0.948 just misses). ≥ 99 %: **24 spares** (P(X ≤ 23) = 0.9896 just
misses 0.99; accept 23 only if the learner says explicitly that they rounded). Cross-check with the
normal approximation: 14.14 + 2.33 × √14.14 = 14.14 + 8.76 ≈ 22.9.

**(d) Why 3 % gives 492, and when to use each (≤ 120 words)**

3 % of 16,384 = 491.5 → **492 spares**, ≈ 20× the model-based count. The rate policy is meant to
absorb build-out: dead-on-arrival parts, infant mortality, handling damage, installer breakage, and
an AFR you do not yet know. The Poisson policy only covers independent steady-state failures with a
credible AFR and lead time. Use rate-based stocking during the build and the first months of
operation, then move to the model-based quantity plus a buffer for correlated failures (a bad
manufacturing lot, a firmware defect) once the fleet's own failure history supports the AFR.

**Common wrong answers.** 800 × 1.0625 computed as 800 × 1.058 (forgetting 257/256); reading the 95 %
row as "20" (0.948 < 0.95); using a lead time in years without /365.
