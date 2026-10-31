# O4 — Prompt workload split across prefill and decode pools: worked solution

Workload: 10 req/s, 8,192-token prompts, 256-token outputs, T-tp4-fp8 replicas, lab transport
assumptions (RDMA 4 × 400G at 85 % + 30 µs; TCP 1 × 200 GbE at 50 % + 1 ms). Model: lab
`compare_designs` (Section 15.10). All values are `[MODELED]`.

**KV and bandwidth.**

```text
KV per request = 8,192 × 327,680 = 2,684,354,560 B (2.68 GB)
aggregate      = 10 × 2.684e9 × 8 = 214.7 Gb/s   (same as 40 req/s × 2k: equal prompt tokens/s)
per decode replica (2)            = 107.4 Gb/s
RDMA: 30 µs + 2.684e9 / 170e9   = 15.8 ms
TCP:  1 ms  + 2.684e9 / 12.5e9  = 215.7 ms
```

| Design | ρ_prefill | Mean TTFT | Mean TPOT | Worst ITL | Link util |
|---|---|---|---|---|---|
| Shared (8) | 0.453 | 0.512 s | 23.0 ms | 375 ms | — |
| Disagg RDMA (6P+2D) | 0.604 | 0.638 s | 16.7 ms | 32.5 ms | 7.9 % |
| Disagg TCP (6P+2D) | 0.604 | 0.638 s | 17.5 ms | 232 ms | 107 % (infeasible) |

These use the lab's linear prefill (362.2 ms). The disaggregated mean TTFT (0.64 s) leaves little margin
under a 0.8 s p95 target, so the prefill pool needs a 7th replica at this prompt length.

**Per-layer streaming overlap.** Prefill per layer = 362.2 / 80 = 4.53 ms. KV per layer = 2.684e9 / 80
= 33.6 MB, which takes 0.20 ms over RDMA (170 GB/s) and 2.68 ms over TCP (12.5 GB/s). Both are below
4.53 ms, so an **uncontended** TCP link could in principle hide the transfer if the engine streams layer
by layer. But at 107 % utilization the link cannot carry the aggregate at all, and host-staged TCP adds
CPU and copy cost. With FP8 KV the TCP load drops to 54 %.

**FP8 KV.** 107.4 Gb/s aggregate (53.7 Gb/s per decode replica), 7.9 ms per request over RDMA, 108 ms
over TCP.

**Modeled vs L3.** All values above are MODELED. Achievable link efficiency, fixed latency, per-layer
streaming in the actual connector, transfer-tail behaviour under contention, and real KV bytes per request
need L3 measurement (`ib_write_bw` between rail-local NICs, connector-level transfer timing).
