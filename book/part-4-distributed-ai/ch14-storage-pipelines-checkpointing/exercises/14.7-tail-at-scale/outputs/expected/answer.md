# 14.7 — Tail at scale: worked solution

**Expression (Section 14.6).** If each of N independent reads exceeds a per-read percentile with
probability 1 − q, the probability that a step that waits for all N reads sees at least one slow read is

```text
P(step slow) = 1 − q^N
```

| Ranks N | Beyond p99 (q = 0.99) | Beyond p99.9 (q = 0.999) |
|---|---|---|
| 256 | 1 − 0.99^256 = 1 − 0.0763 = **0.92** | 1 − 0.999^256 = 1 − 0.774 = **0.23** |
| 4,096 | 1 − 0.99^4096 ≈ 1 − e^−41 ≈ **1.0** | 1 − 0.999^4096 = 1 − 0.0166 = **0.98** |

All values are `[MODELED]` under the independence assumption.

**Interpretation.** At 256 ranks, 92 % of steps contain a read slower than the per-read p99, so the
per-read p99 is effectively the *median step's* experience. At 4,096 ranks even the p99.9 is hit on
98 % of steps. Storage for synchronous jobs must therefore be accepted on its **p99.9 (or p99.99)**
latency, not on throughput or p50. The design should also reduce exposure: prefetch deeply enough to
absorb a tail read, and issue fewer synchronous reads per step (larger shards, local staging,
Section 14.7).

**Caveat on independence.** Real tails are correlated. A slow storage target (target 5 in the lab) or a
write burst (13–17 s in the lab trace) slows many reads in the *same* step. That makes some steps much
worse and others better than the independent model. The expectation argument still motivates judging
storage on p99.9.

**Common wrong answer.** Reporting 0.99^256 (the probability of *no* slow read) as the answer.
