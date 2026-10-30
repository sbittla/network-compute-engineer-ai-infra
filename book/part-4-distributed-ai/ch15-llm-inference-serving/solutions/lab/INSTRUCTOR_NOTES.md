# Lab 15 — Instructor Notes (planted anomalies and expected results)

All values below come from `lab/tools/generate_trace.py --seed 15` (`[SIMULATED]`) and the
reference implementation `serving_lab.py` in this folder. If you regenerate with a different
seed, re-derive them with the reference solution.

## Trace at a glance

| Item | Value |
|---|---|
| Requests | 4,539 (4,479 `chat`, 60 `longctx`) over 600 s |
| Replicas | r0 1,263 · r1 1,133 · r2 1,313 · r3 830 (least-loaded routing sends less to the slow replica) |
| KV pool per replica | 13,351 blocks × 16 tokens = 213,616 tokens (TP=2, FP8 weights, BF16 KV) |
| Scheduler | max 48 running sequences, 8,192 prefill tokens/iteration, LIFO recompute preemption, no chunked prefill |
| Healthy baseline (arrivals < 230 s) | TTFT p50/p95/p99 = 0.138 / 0.449 / 0.621 s; TPOT p50/p95/p99 = 27.5 / 45.0 / 52.3 ms; queue p95 = 0.107 s; SLO attainment 98.2 %; goodput 5.90 req/s of 6.00 req/s offered |
| Whole trace | chat TTFT p50/p95/p99 = 0.269 / 24.5 / 42.0 s; chat TPOT p50/p95 = 46.2 / 90.1 ms; SLO attainment 48.8 %; goodput 3.69 req/s vs throughput 7.57 req/s; 1,919 output tokens/s |
| Sampled ITL (227 requests, 72,157 gaps) | p50 35.3 ms, p95 123 ms, p99 368 ms, p99.9 1.09 s, max 8.5 s |

## Planted anomaly 1 — queueing collapse under an arrival burst

* **Ground truth:** an extra 20 req/s of chat traffic in [240, 285) s, on top of the 6 req/s
  base (4.3× the median window arrival count).
* **Signature:** queue p95 climbs from about 0.1 s to 8.1 s, 22.9 s and then 42.6 s across the
  three burst windows. It stays high for about 60 s after the burst ends while the backlog drains
  (25.6 s, 18.5 s, 11.2 s, 3.2 s). The detected episode runs from 240 to 345 s. Every replica sits
  at `num_running = 48` (the admission cap) with `num_waiting` up to about 97, while KV usage
  stays at **30–43 %**.
* **Why it teaches:** the system is **slot-bound, not memory-bound**. KV headroom is plentiful,
  so the binding limit is the admission cap plus decode throughput. Learners who reach for
  "add KV memory" are wrong. The correct levers are admission control and load shedding at the
  gateway, more replicas, or a higher concurrency cap *after* checking TPOT headroom. The episode
  also shows that queueing outlives the burst: the drain rate equals spare capacity, so the tail
  persists after the arrival rate returns to normal.

## Planted anomaly 2 — preemption storm from a long-context tenant

* **Ground truth:** a `longctx` tenant sends 1.2 req/s in [420, 470) s, with prompts of
  8k–12k tokens and outputs of 3k–5k tokens.
* **Signature:** KV usage rises from about 8 % to 98–100 % on the replicas that receive these
  requests (r0 and r1 most). Preemptions begin at about 465 s (43 in total, on 37 requests: 34 chat
  and 3 longctx) and continue until the end of the trace. Queue p95 then reaches 86 s in the
  495 s window, **with no increase in arrivals**. Recomputing a preempted long sequence costs about
  1 s of prefill and stalls every other sequence on that replica, which produces ITL outliers
  above 1 s.
* **Classification trap:** queueing is high here too. A detector that keys only on queue p95
  labels this a burst. The reference detector separates the two causes: an episode is a
  `queueing_collapse` only when arrivals spike. A high-queue episode that overlaps preemptions is
  attributed to the storm. Check B6 fails if the storm's queueing is reported as
  `capacity_shortfall`.
* **Why it teaches:** the same symptom (TTFT p95 explodes) has a different root cause and a
  different fix: per-tenant admission control or concurrency limits, KV-aware routing (the
  router here balances by request *count*, which is blind to KV), a separate long-context pool,
  FP8 KV cache, or more KV memory per replica (TP=4 instead of TP=2).

## Planted anomaly 3 — slow replica

* **Ground truth:** every iteration on r3 takes 1.65× longer (in a real fleet, think of an
  applied power cap, HBM or SM clocks held low, a degraded NVLink, or a noisy neighbour).
* **Signature:** r3's median TPOT is 75.5 ms against a peer median of 42.5 ms across the whole
  trace (43.2 ms against 26.9 ms in the healthy baseline). r3 receives 830 requests while its
  peers receive about 1,240 each, because least-loaded routing partly compensates. Its
  `gpu_busy_pct` is 100 %, the same as every other replica.
* **Why it teaches:** this is a per-replica fault, so it shows up only when you group by replica.
  Pool-level percentiles mix it into the overall TPOT p95. GPU utilization ("busy") is useless
  for spotting it. The next step is to check clocks and throttle reasons (`nvidia-smi -q -d
  PERFORMANCE`), power limits, and NVLink counters on the r3 host (manuscript Section 15.14).

## Non-anomalies learners sometimes flag

* `gpu_busy_pct` is 100 % almost everywhere. That is expected for a continuous-batching engine
  with any work queued, and it does not mean the GPU is saturated (Chapter 6).
* `longctx` SLO attainment is 100 % because its SLO is looser (TTFT 3 s, TPOT 80 ms). Learners
  who apply chat SLOs to it get spurious violations. Check that per-tenant SLOs are applied.
* Token gaps are sampled at 5 %. Learners should say that ITL percentiles come from a sample and
  that p99.9 from about 72k gaps over 227 requests is noisy, because the gaps within one request
  are correlated.

## Expected Part A and Part C outputs `[MODELED]`

| Quantity | L-tp8-bf16 | T-tp4-fp8 |
|---|---|---|
| KV budget per replica | 420 GB | 210 GB |
| Max sequences at 4,096 tokens | 312 | 156 |
| Batch used (min of cap and max_seqs) | 32 | 128 |
| TPOT at ctx 2,176 | 11.68 ms | 20.19 ms |
| Tokens/s per node | 2,740 | 12,678 |
| 2k prefill | 90.6 ms | 90.6 ms |

| Design (40 req/s, 2,048 in / 256 out, TP=4 FP8 replicas) | shared (8) | disagg RDMA (6P+2D) | disagg TCP (6P+2D) |
|---|---|---|---|
| Prefill utilization ρ | 0.453 | 0.604 | 0.604 |
| Mean TTFT | 128 ms | 160 ms | 160 ms |
| Mean TPOT | 23.3 ms | 17.1 ms | 17.3 ms |
| Worst ITL | 103 ms | 21.1 ms | 71.8 ms |
| Decode batch per replica | 29.8 | 87.7 | 87.7 |
| KV transfer per request | — | 3.98 ms | 54.7 ms |
| Aggregate KV bandwidth | — | 214.7 Gb/s | 214.7 Gb/s |
| Per decode replica | — | 107.4 Gb/s | 107.4 Gb/s |
| Utilization of achievable link | — | 7.9 % | 107.4 % (infeasible) |

The 6P+2D split comes from the manuscript's P:D sweep (Table 15.8): 4:4 starves prefill
(ρ = 0.906), 7:1 fails TPOT (47 ms) and KV capacity (B = 484 > 278), and 6:2 beats 5:3 on TTFT
(160 vs 210 ms) with TPOT 17.1 ms.

Speculative decoding with α = 0.8, k = 4, and draft cost 0.05 gives E[tokens] = 3.3616 and a
speedup of 2.80× at small batch.
