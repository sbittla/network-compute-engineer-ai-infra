# K2 — Latency metrics: worked solution

**Definitions (Section 15.1)** for a request with arrival time *a*, token emission times t₁…t_n and
finish time f = t_n:

```text
TTFT = t_1 − a                         (queue + prefill + first decode)
TPOT = (f − t_1) / (n_out − 1)         (mean time per output token after the first)
ITL_i = t_{i+1} − t_i,  i = 1…n−1      (every individual inter-token gap)
```

**A failure visible in ITL p99 but not in mean TPOT.** With continuous batching and no chunked prefill,
admitting a new 2,048-token prompt into a running batch makes one iteration a prefill. On a TP = 8 BF16
replica that takes ≈ 90 ms (2 × 70e9 × 2,048 / (8 × 989e12 × 0.40) = 90.6 ms `[MODELED]`), and every
running sequence gets no token during it. For a 256-token response that stall is *one* gap out of
255:

```text
mean TPOT rises by ≈ 90 ms / 255 ≈ 0.35 ms     (invisible against ≈ 12–20 ms)
ITL for that gap  = 12 ms + 90 ms ≈ 100 ms      (dominates ITL p99)
```

The mean spreads one large stall over hundreds of normal gaps. Percentiles over *individual gaps* keep
it. Users see it as a visible stutter in streaming output. Other examples that behave the same way:
preemption-by-recompute stalls, and the KV-transfer delay before token 2 in disaggregated serving
(case T1).

**Common wrong answer.** Defining TPOT as e2e / n_out, which includes TTFT and queueing.
