# W2 — Scaling efficiency and detectability (solution)

Inputs `[ILLUSTRATIVE]` from the prompt; derived values `[MODELED]`. Manuscript Sections 22.5 and 22.6.1.

**(a) Throughput and weak-scaling efficiency.** Tokens per step = DP × 128 sequences × 4,096 tokens:
1,048,576 (DP 2), 2,097,152 (DP 4), 4,194,304 (DP 8). Per-GPU work is constant, so
`E_weak = X(N) / ((N/64) × X(64)) = T(64) / T(N)`.

| GPUs | Step (s) | Tokens/s | Tokens/s per GPU | E_weak |
|---|---|---|---|---|
| 64 | 17.38 | 1,048,576 / 17.38 = 60,332 | 942.7 | 100 % |
| 128 | 17.62 | 2,097,152 / 17.62 = 119,021 | 929.9 | 17.38 / 17.62 = **98.6 %** |
| 256 | 17.90 | 4,194,304 / 17.90 = 234,318 | 915.3 | 17.38 / 17.90 = **97.1 %** |

**(b) Straggler share of the gap.** A synchronous step waits for the slowest of n nodes; the expected
maximum of n normal samples grows with n (Section 22.5.2). Relative to 8 nodes:

```text
16 nodes: (1.77 − 1.42) × 0.5 s = 0.175 s  of the 17.62 − 17.38 = 0.24 s gap → 0.065 s remains
32 nodes: (2.07 − 1.42) × 0.5 s = 0.325 s  of the 17.90 − 17.38 = 0.52 s gap → 0.195 s remains
```

Much of each remainder is DP exposure. Ring all-reduce bytes per GPU = 2 × (DP − 1)/DP × 4.375 GB:
4.38, 6.56 and 7.66 GB at DP 2, 4, 8 → 0.097, 0.146 and 0.170 s at 45 GB/s. Only ≈ 70 ms hides behind
the last micro-batch's backward pass, so exposure is ≈ 0.03, 0.08 and 0.10 s: +0.05 s at 16 nodes and
+0.07 s at 32 nodes. Unexplained ≈ 0.015 s (16 nodes) and ≈ 0.12 s (32 nodes; 0.52 − 0.325 − 0.073 =
0.122 s), consistent with Section 22.10.5's ≈ 0.12 s. The straggler term dominates, so per-node jitter
is the cheapest efficiency lever at full scale.

**(c) Can 5 runs per arm detect 0.15 s?**

```text
MDE(n = 5) = 2.8 × σ × √(2/n) = 2.8 × 0.11 × √(2/5) = 2.8 × 0.11 × 0.632 = 0.195 s
```

0.195 s > 0.15 s: **No**, 5 runs per arm cannot reliably detect the claimed saving (power would be
well below 80 %). Required n per arm:

```text
n = 2 × (2.8 × σ / δ)² = 2 × (0.308 / 0.15)² = 2 × 2.053² = 2 × 4.216 = 8.43 → 9 runs per arm
```

Run them interleaved on the same reserved nodes (Section 22.6.2) so drift does not masquerade as effect.

**Common wrong answers.** Using strong-scaling efficiency (gives ≈ 24 % at 256 GPUs); forgetting the √2
for two arms; rounding n down to 8; comparing the MDE with σ instead of with the claimed effect.
