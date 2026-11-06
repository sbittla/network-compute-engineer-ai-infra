# W2 — Sizing a shared pool with Little's law: worked solution

Constants `[VENDOR-SPEC, 2026-10]` (H100-class): HBM 3.35 TB/s and 80 GB per GPU, 989 TFLOP/s dense BF16, 1,979 TFLOP/s dense FP8. Planning factors `[ILLUSTRATIVE]` (`lab/data/configs.yaml`): HBM efficiency 0.70, 3 ms step overhead, prefill MFU 0.40, memory fraction 0.90, 2 GB reserve per GPU, 16-token blocks.
Replica T-tp4-fp8: TP = 4, FP8 weights 70 GB, BF16 KV. Decode step t_d(B) = 10.463 ms + c·B with
c = ctx × 327,680 / 9.38e12. Model: Section 15.7 / lab `compare_designs` (shared pool). All values are
`[MODELED]`.

**(a) Prefill.** t_p = 2 × 70e9 × 4,096 / (4 × 1,979e12 × 0.40 = 3.166e15) = **181.1 ms**. The
quadratic attention term would add ≈ 6.9 ms (2 × 80 × 4,096² × 8,192 / 3.166e15). The lab model omits
it, and including it is credited. Demand = 25 × 0.1811 = **4.53 replica-s/s**.

**(b) Pool sizes.** Average decode context = 4,096 + 256 = 4,352 → c = 0.15203 ms per sequence.
Per-replica rate λ_r = 25 / n, ρ = λ_r × t_p, mean TTFT = t_p + ρ t_p / (2(1 − ρ)) (M/D/1), and
TPOT from the fixed point TPOT(1 − ρ) = t_d(B), with B = λ_r × 512 × TPOT.

| Replicas | λ_r | ρ_prefill | Mean TTFT | Mean TPOT | B |
|---|---|---|---|---|---|
| 6 | 4.17 | 0.755 | 0.460 s | **unstable** | — |
| 8 | 3.13 | 0.566 | 0.299 s | 54.8 ms | 87.7 |
| 10 | 2.5 | 0.453 | 0.256 s | 29.7 ms | 38.0 |
| 12 | 2.08 | 0.377 | 0.236 s | 22.7 ms | 24.2 |

*Fixed point for 10 replicas:* B = 2.5 × 512 × TPOT = 1,280 TPOT. TPOT × (1 − 0.4528) = 0.010463 +
0.00015203 × 1,280 × TPOT = 0.010463 + 0.19460 TPOT → TPOT = 0.010463 / (0.5472 − 0.1946) =
**29.7 ms**. *Six replicas are unstable* because the decode demand c·λ_r·O = 0.00015203 × 4.17 × 512 =
0.324 exceeds the time left after prefill, 1 − ρ = 0.245. The decoding population grows without bound.

**(c) Choice.** **10 replicas** (mean TPOT 29.7 ms ≤ 35 ms, mean TTFT 0.256 s, comfortable against
800 ms p95), plus 2 for N+1 and bursts: 12 replicas on 6 HX8 nodes. Worst unchunked ITL = t_d(38) + t_p
= (10.46 + 0.152 × 38) + 181.1 ≈ 16.2 + 181.1 = **197 ms**. That passes the TPOT SLO on average but is a
visible stutter, so recommend chunked prefill.

**(d) KV capacity.** Full length 4,608 tokens = 288 blocks → ⌊40,054 / 288⌋ = **139 sequences** per
replica, well above B = 38.

**Common wrong answers.** Applying the TTFT SLO to the mean. Ignoring instability. Omitting the (1 − ρ)
stall factor.
