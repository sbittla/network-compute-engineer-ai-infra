# DEL — Inference capacity model and tuning recommendation: worked solution

A model memo outline. The checker must show 18/18. All numbers are `[MODELED]` unless marked.

**1. Launch layout (40 req/s, 2k prompts, 256 outputs).** Shared pool of **8 × T-tp4-fp8 replicas with
chunked prefill** on 4 HX8 nodes, plus 1 node for N+1 = **5 nodes** (Section 15.12). ρ_prefill = 40/8 ×
0.0906 = 0.453, mean TTFT 0.128 s, mean TPOT 23.3 ms, decode batch ≈ 30. Without chunking the worst ITL is
≈ 103 ms, so use chunked prefill to bound it.

**2. Tiers.** Latency tier **L-tp8-bf16**: TPOT 11.7 ms at batch 32, 2,740 tokens/s per node. Throughput tier
**T-tp4-fp8**: TPOT 20.2 ms at batch 128, 12,678 tokens/s per node (4.6×).

**3. Disaggregation decision.** Not at launch. Disaggregated 6P+2D over RDMA would cut TPOT to 17.1 ms and
worst ITL to 21.1 ms, but the shared pool with chunking meets the SLOs with fewer moving parts. KV budget
if adopted: 40 × 2,048 × 327,680 × 8 = **214.7 Gb/s** (107.4 Gb/s per decode replica, 7.9 % of 4 × 400G
at 85 %). TCP on 200 GbE would need 107 %, so RDMA is the only viable transport. The budget is linear in
prompt tokens per second. Re-evaluate when ρ_prefill > 0.55 (R3).

**4. Phase SLOs and alerts.** TTFT p95 ≤ 800 ms (page at > 800 ms for 5 min). TPOT p95 ≤ 50 ms (page at
> 50 ms for 5 min). ITL p99 ≤ 100 ms with chunking (ticket at 2× baseline). Preemptions > 1/min per
replica (ticket: KV pressure). Per-replica median TPOT > 1.4× the pool median (drain candidate; this is
the lab's slow-replica rule). Queue depth > 2 × replicas for 2 min (admission control).

**5. Validation plan (lab Section 9).** L2: batch sweep for step time against batch and context with the
real engine; prefill time against prompt length (MFU); serving benchmark at 40 req/s with real prompt and
output distributions, reporting TTFT, TPOT and ITL percentiles. L3: `ib_write_bw` between rail-local NICs
and KV connector timing, only if disaggregation is pursued. Record the manifest fields from
`lab/manifest.yaml`: engine and version, model and quantization, GPU and driver, CUDA, TP size,
concurrency cap, chunk size, dataset, date, and `[MEASURED]` labels.

Deduct heavily for any modeled number presented as measured.
