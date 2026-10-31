# D1 — RAG serving tier: worked solution

Constants `[VENDOR-SPEC, 2026-10]` (H100-class): HBM 3.35 TB/s and 80 GB per GPU, 989 TFLOP/s dense BF16, 1,979 TFLOP/s dense FP8. Planning factors `[ILLUSTRATIVE]` (`lab/data/configs.yaml`): HBM efficiency 0.70, 3 ms step overhead, prefill MFU 0.40, memory fraction 0.90, 2 GB reserve per GPU, 16-token blocks.
Workload: 20 req/s, 8,192-token prompts, 300-token outputs. SLOs TTFT p95 ≤ 1.5 s and TPOT p95 ≤ 40 ms
(a declared variation). Replicas are T-tp4-fp8. Every value is `[MODELED]` unless marked.

**Prefill** (8,192 tokens, TP = 4 FP8, 3.166e15 FLOP/s effective): linear 2 × 70e9 × 8,192 / 3.166e15 =
362.2 ms. Attention 2 × 80 × 8,192² × 8,192 / 3.166e15 = 27.8 ms. **t_p = 390.0 ms**. Demand = 20 ×
0.390 = **7.80 replica-s/s**.

| P | ρ | Mean TTFT | ≈ p95 TTFT (t_p + 3 W_q) |
|---|---|---|---|
| 11 | 0.709 | 0.865 s | ≈ 1.82 s ✗ |
| 12 | 0.650 | 0.752 s | ≈ 1.48 s (borderline) |
| 13 | 0.600 | 0.682 s | ≈ 1.27 s ✓ |

**Decode** (average context 8,192 + 150 = 8,342; c = 0.2914 ms per sequence; B = (20/D) × 300 × TPOT).
Each sequence ends at 8,492 tokens = 531 blocks, so 75 fit per replica with BF16 KV or 150 with FP8 KV.

| D | Mean TPOT | B per replica |
|---|---|---|
| 3 | 25.1 ms | 50.2 |
| 4 | 18.6 ms | 27.9 |
| 5 | 16.1 ms | 19.3 |

**Choice: 13P + 4D = 17 replicas** (D = 4 leaves headroom under 40 ms p95), 8.5 → 9 HX8 nodes plus 1
spare = **10 nodes**.

**Network budget.** KV per request = 8,192 × 327,680 = 2.684 GB. Aggregate = 20 × 2.684e9 × 8 =
**429.5 Gb/s**, 107.4 Gb/s per decode replica. **RDMA** (4 × 400G at 85 % = 1,360 Gb/s): **7.9 %**
utilization, 30 µs + 2.684e9 / 170e9 = **15.8 ms** per request, hidden by per-layer streaming (33.6 MB
per layer = 0.2 ms against 4.9 ms of prefill per layer). **TCP** (200 GbE at 50 % = 100 Gb/s): **107 %**,
so **infeasible**. Choose RDMA on the decode replicas' rail-local NICs in a dedicated traffic class (or
dedicated inference rails) with ECN. FP8 KV would halve demand to 215 Gb/s.

**Shared alternative** (acceptable if argued): 16 replicas, ρ = 0.4875, mean TTFT 0.575 s, mean TPOT
26.0 ms, but worst unchunked ITL ≈ 403 ms. With 512-token chunks (22.6 ms each) ITL is bimodal at ≈ 13 and
36 ms and TPOT p95 lands near 40 ms. Disaggregation buys TPOT headroom.

**Failure table.**

| Failure | Effect | Behaviour |
|---|---|---|
| Decode replica dies | ≈ 28 sequences lose KV | re-prefill at ≈ 0.39 s each (+11 replica-s on prefill), gated by admission control |
| Prefill replica dies | ρ on the other 12 → 0.65 | p95 ≈ 1.48 s, still within SLO |
| KV transfer timeout | one request stalls | retry once, then local prefill on the decode replica |

**L2/L3 measurements before committing** `[MEASURED]` targets: HBM efficiency and step overhead at
B ≈ 28 with 8k contexts; prefill MFU at 8k including the attention kernel; `ib_write_bw` between rail-local
NICs plus real KV bytes per request from the connector.
