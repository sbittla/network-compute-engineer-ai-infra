# O5 — Speculative decoding trade-off: worked solution

**Expected tokens per verification step** (Leviathan et al., Section 15.11): E = (1 − α^(k+1)) / (1 − α).

| α \ k | 2 | 4 | 8 |
|---|---|---|---|
| 0.6 | 1.96 | 2.31 | 2.48 |
| 0.8 | 2.44 | 3.36 | 4.33 |
| 0.9 | 2.71 | 4.10 | 6.13 |

**Speedup, memory-bound verification (cost 1):** S = E / (0.05k + 1).

| α \ k | 2 | 4 | 8 |
|---|---|---|---|
| 0.6 | 1.78 | 1.92 | 1.77 |
| 0.8 | 2.22 | 2.80 | 3.09 |
| 0.9 | 2.46 | 3.41 | 4.38 |

**Verification cost at B = 128 on T-tp4-fp8 (roofline)** `[MODELED]`. Verification streams the same
bytes as a decode step: (70e9 + 128 × 2,176 × 327,680) / 9.38e12 = **17.19 ms** of HBM time at 70 %
efficiency. Its compute is B(k + 1) tokens × 2 × 70e9 FLOP / (4 × 1,979e12 × 0.40) = B(k + 1) ×
44.2 µs. Then v_k = (max(compute, 17.19 ms) + 3 ms) / 20.19 ms:

- k = 2: 384 tokens → 16.98 ms, still below 17.19 ms (memory-bound), so **v = 1.00**.
- k = 4: 640 tokens → 28.30 ms of compute, above the 17.19 ms of HBM time (compute-bound), so v = 31.30 / 20.19 = **1.55**.
  Equivalently, intensity including KV bytes ≈ 556 FLOP/B > effective ridge 591 × 0.40/0.70 ≈ 338 FLOP/B
  (a weight-only intensity against the peak ridge would wrongly call k = 2 compute-bound).
- k = 8: 1,152 tokens → 50.93 ms, so v = 53.93 / 20.19 = **2.67**.

**Speedup at B = 128:** S = E / (0.05k + v_k).

| α \ k | 2 (v = 1.00) | 4 (v = 1.55) | 8 (v = 2.67) |
|---|---|---|---|
| 0.6 | 1.78 | 1.32 | 0.81 |
| 0.8 | 2.22 | 1.92 | 1.41 |
| 0.9 | 2.46 | 2.34 | 1.99 |

**Recommendation.** On the *interactive* (small-batch, memory-bound) tier use **k = 4**, and k = 8 only if
α ≥ 0.9 is measured: gains beyond k = 4 are small at α = 0.6–0.8 (1.92 → 1.77, 2.80 → 3.09) while longer
drafts cost draft compute and KV memory. On the *throughput* tier, enable speculation only with a **short
draft, k = 2**: verification stays memory-bound and keeps ≈ 1.8–2.5×, while k = 8 is a net loss at α = 0.6
(0.81×). Re-derive v_k for the real batch size and measure α on production prompts.

**Common wrong answer.** Assuming a constant verification cost instead of deriving it per k.
