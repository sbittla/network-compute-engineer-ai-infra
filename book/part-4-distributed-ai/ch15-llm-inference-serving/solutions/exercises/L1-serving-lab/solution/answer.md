# L1 — Lab 15: capacity model, serving-trace analyzer, disaggregation model: worked solution

**Checker.** `python lab/check.py` must end `19/19 passed, 0 failed, 0 TODO`. The rubric is lab
Section 8 (100 points). Reference values: `solutions/lab/INSTRUCTOR_NOTES.md`.

**Report expectations.**

1. *Configuration recommendation (Part A)* `[MODELED]`: latency tier **L-tp8-bf16** with TPOT 11.7 ms
   at batch 32 (2,740 tokens/s per node). Throughput tier **T-tp4-fp8** with TPOT 20.2 ms at batch 128
   (12,678 tokens/s per node, 4.6×). Risks: L is expensive per token (8 GPUs per replica, batch capped at 32).
   T depends on FP8 weight quality and its KV (156 sequences of 4k) caps batch at long contexts.
2. *Trace table (Part B)* `[SIMULATED]`: full trace vs baseline TTFT p50/p95/p99, TPOT, ITL from the 5 %
   sample. Throughput 7.57 req/s against goodput 3.69 req/s.
3. *Diagnoses:*
   - **Burst (240–345 s):** arrivals 4.3× the median window, `running` at the 48 cap on every replica,
     KV only 30–43 %, so it is slot-bound queueing collapse (queue p95 up to ≈ 43 s). Mitigate with gateway
     admission control or load shedding, or more replicas.
   - **Preemption storm (465–600 s):** arrivals flat, KV 98–100 %, the preemption counter rising (+38),
     running below the cap with a queue. Memory-bound, not a burst. Mitigate with per-tenant limits,
     KV-aware routing, or by moving long contexts to a larger-KV pool.
   - **Slow replica r3:** median TPOT 75.5 ms vs peers 42.5 ms with the same busy %. Drain it and check
     clocks, power limits and errors.
4. *Disaggregation (Part C)* `[MODELED]`: at 40 req/s with 2k prompts the KV stream is 214.7 Gb/s
   (107.4 Gb/s per decode replica). Over RDMA (4 × 400G at 85 %) that is 7.9 % utilization and 4.0 ms
   per transfer. Over TCP (200 GbE at 50 %) it needs **107 %** of achievable bandwidth, so it is
   infeasible. Disaggregated RDMA 6P+2D gives TPOT 17.1 ms and worst ITL 21.1 ms against the shared
   pool's 23.3 ms and 103 ms. L2/L3 measurements to confirm: `ib_write_bw` between rail-local NICs, real
   KV bytes per request from the connector, HBM efficiency and step overhead.

Every number must carry `[MODELED]` or `[SIMULATED]`. Deduct heavily for modeled values presented as
measured.
