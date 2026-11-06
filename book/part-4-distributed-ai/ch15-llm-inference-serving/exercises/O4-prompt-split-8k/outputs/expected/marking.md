# Marking scheme: O4 Prompt workload split across prefill and decode pools

Type outline-mandated · kind computed · tier L1 · 10 points

**Evidence required:** KV bytes, Gb/s, transfer times, a three-row comparison, the overlap calculation per layer, and a statement of which values are modeled and which would need L3 measurement.

| Criterion | Points |
|---|---|
| KV bytes 2.684 GB per request, aggregate 214.7 Gb/s (107.4 per decode replica) | 2 |
| Transfer times: RDMA 15.8 ms, TCP 215.7 ms | 2 |
| Three-row comparison (shared 8, disagg RDMA and TCP 6P+2D) with ρ, TTFT, TPOT, worst ITL, link util | 3 |
| Per-layer overlap: 4.53 ms prefill vs 0.20 ms RDMA and 2.68 ms TCP per layer; TCP at 107 % cannot carry the aggregate | 2 |
| FP8 KV repeat (107.4 Gb/s, 7.9 / 108 ms) and modeled vs L3-measured statement | 1 |
