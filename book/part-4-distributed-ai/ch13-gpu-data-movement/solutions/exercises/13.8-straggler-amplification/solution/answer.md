# 13.8 — Straggler amplification: worked solution

**(a) Probability that a step contains at least one slow rank (Section 13.7) `[MODELED]`.**
With per-rank probability p = 0.05 % = 5 × 10⁻⁴, independent across ranks:

```text
P(≥ 1 slow) = 1 − (1 − p)^N
N =   256:  1 − 0.9995^256   = 1 − 0.8798 = 0.120  → 12.0 %
N = 1,024:  1 − 0.9995^1024  = 1 − 0.5991 = 0.401  → 40.1 %
N = 4,096:  1 − 0.9995^4096  = 1 − 0.1288 = 0.871  → 87.1 %
```

A "rare" per-rank event becomes the common case at ORION-XL scale: 87 % of steps are slowed by
somebody. For small p the approximation Np works only while Np ≪ 1 (256 × 5e-4 = 0.128 ≈ 12 %). At
N = 4,096 it would give 205 %, which is why the exact form is required.

**(b) GPU time lost to one straggler (64 ranks).** In a synchronous step every rank waits for the
slowest arrival:

```text
lost GPU-time per step = Σ_r (max a − a_r) = 63 × (774 − 600) ms = 63 × 0.174 s = 10.96 GPU-s
lost fraction          = 10.96 / (N × T_step) = 10.96 / (64 × 0.924 s) = 10.96 / 59.14 = 18.5 %
```

The slow rank itself waits 0, so the sum has 63 terms. The step time of 924 ms already contains the
communication (774 ms compute + 150 ms collective), so the denominator is the total GPU time in the
step. This matches the lab's 18.6 % for steps 0–19 (Section 13.7), where the per-step numbers vary
slightly around these means `[SIMULATED]`.

**Common wrong answers.** Using 64 instead of 63 waiting ranks (11.1 GPU-s). Dividing by 64 × 0.774 s
(compute only, giving 22.1 %). Computing p × N for N = 4,096.
