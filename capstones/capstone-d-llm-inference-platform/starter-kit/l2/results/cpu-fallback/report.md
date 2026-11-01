# Capstone D L2: continuous-batching serving latency and goodput on one GPU

`[MEASURED]` on **CPU fallback: 13th Gen Intel(R) Core(TM) i7-13700HX**, 2026-11-01T00:13:45Z.

| Environment | Value |
|---|---|
| device | cpu |
| cpu_model | 13th Gen Intel(R) Core(TM) i7-13700HX |
| cpu_count | 24 |
| mem_total_gib | 7.8 |
| os | Linux-6.18.54.1-microsoft-standard-WSL2-x86_64-with-glibc2.35 |
| torch | 2.5.1+cu124 |
| cuda_runtime | 12.4 |

**Status:** ran
**Invariants:** all passed

## Workload

Random-weight decoder (13 M parameters, torch.float32, 59 MB weights). Trace: first 80 requests of `trace_s1.csv`, lengths / 8 (prompt cap 512, output cap 64), arrivals compressed 8x -> **43.1 req/s offered**, mean prompt 210, mean output 30 tokens.
SLO (data/slo.yaml): TTFT p95 <= 0.8 s (engine target 0.77 s), TPOT p95 <= 50 ms, ITL p99 <= 100 ms.

## Measured vs simulated, identical trace

| max_num_seqs | source | TTFT p50 (ms) | TTFT p95 (ms) | TPOT p50 (ms) | TPOT p95 (ms) | ITL p99 (ms) | goodput | out tok/s |
|---|---|---|---|---|---|---|---|---|
| 2 | measured | 2577 | 4748 | 4.9 | 7.0 | 38.7 | 14 % | 343 |
| 2 | L1 simulator | 959 | 1949 | 2.8 | 3.4 | 14.8 | 44 % | 1302 |
| 16 | measured | 458 | 1226 | 20.8 | 25.7 | 97.7 | 68 % | 680 |
| 16 | L1 simulator | 24 | 57 | 6.0 | 12.5 | 41.3 | 100 % | 1302 |

Measured SLIs use the L1 definitions in `instructor/reference/serving.py` (`summarize`, warm-up/cool-down exclusion set to 0 for this short replay); goodput = share of requests meeting both the TTFT target and the TPOT SLO. Simulator rows: `serving.simulate` on the same trace with this device's measured ceilings (GEMM 0.4 TFLOP/s, copy 68 GB/s, efficiency 1.0) and a one-point overhead calibration (1.46 ms per iteration) `[SIMULATED]`.

## Decode iterations (max_num_seqs = 16 run)

| Batch | steps | median (ms) | p95 (ms) | memory floor (ms) |
|---|---|---|---|---|
| 1 | 18 | 3.89 | 5.44 | 0.91 |
| 2 | 25 | 4.61 | 6.46 | 1.03 |
| 3 | 4 | 4.10 | 4.39 | 1.10 |
| 4 | 12 | 4.88 | 6.26 | 1.15 |
| 6 | 1 | 5.55 | 5.55 | 1.23 |
| 7 | 2 | 5.81 | 6.24 | 1.29 |
| 8 | 2 | 8.14 | 8.52 | 1.37 |
| 9 | 3 | 6.10 | 7.42 | 1.45 |
| 10 | 7 | 6.21 | 9.04 | 1.41 |
| 11 | 2 | 6.23 | 6.58 | 1.47 |
| 12 | 4 | 7.11 | 8.25 | 1.56 |
| 13 | 2 | 7.62 | 7.63 | 1.65 |
| 14 | 3 | 7.71 | 8.95 | 1.70 |
| 16 | 121 | 8.39 | 11.33 | 1.79 |

## Not runnable here

- **supported serving stack (vLLM/SGLang) with an open model, TP=8 on an HX8 node**. Probe: vllm installed=False, sglang installed=False, HF cache=False, network interfaces=['lo'] (container runs with --network none), GPUs=0. Needs: serving stack image, open model weights, 8-GPU node for TP=8. Fallback: minimal continuous-batching engine on a random-weight model, same trace shape.
- **L3 multi-replica routing, canary and rollback drill**. Probe: single host, no load balancer, no second node. Needs: 2+ nodes, load balancer. Fallback: two configurations compared under the identical trace on one replica.

## What to conclude

- Same model, same GPU, same trace: raising max_num_seqs 2 -> 16 moved goodput 14 % -> 68 % and TTFT p95 4748 -> 1226 ms. With few slots the queue, not the model, sets TTFT.
- Decode steps barely slow as the batch grows (each step streams the weights once), which is why continuous batching buys throughput almost for free until KV capacity or the TPOT SLO binds.
- Where measured and simulated rows differ, the usual causes are: the engine prefills one prompt per iteration (the simulator packs prefill and decode into one budgeted iteration), Python launch overhead that varies with batch, and other tenants on the GPU. Name the cause before trusting either number.
- _CPU fallback: no GPU was used; a smaller fp32 model served the trace slice. GPU-only invariants (flat memory-bound decode, memory-peak bound) were skipped._ On a CPU, decode is closer to compute-bound, so TPOT grows visibly with batch: the throughput-vs-latency trade-off the GPU hides at small batch.

- Trace: first N requests of data/trace_s1.csv; prompt and output lengths / 8 (capped), inter-arrival times / compress. Arrivals replayed in real time (open loop).
- Latencies are engine-side wall clock (perf_counter) including queueing; each step synchronises on its sampled tokens, as a real engine must before streaming them.
- A short warm-up replay precedes each measured replay; one measured replay per configuration (every request is one sample: percentiles are over requests and token gaps).
