# Capstone D L2: continuous-batching serving latency and goodput on one GPU

`[MEASURED]` on **NVIDIA GeForce RTX 4060 Laptop GPU**, 2026-11-01T00:13:09Z.

| Environment | Value |
|---|---|
| device | cuda |
| cpu_model | 13th Gen Intel(R) Core(TM) i7-13700HX |
| cpu_count | 24 |
| mem_total_gib | 7.8 |
| os | Linux-6.18.54.1-microsoft-standard-WSL2-x86_64-with-glibc2.35 |
| torch | 2.5.1+cu124 |
| cuda_runtime | 12.4 |
| driver_version | 592.82 |
| pcie.link.gen.max | 4 |
| pcie.link.width.max | 8 |
| clocks.max.sm | 3105 |
| power.limit | [N/A] |

**Status:** ran
**Invariants:** all passed

## Workload

Random-weight decoder (403 M parameters, torch.float16, 839 MB weights). Trace: first 160 requests of `trace_s1.csv`, lengths / 8 (prompt cap 1024, output cap 128), arrivals compressed 4x -> **23.5 req/s offered**, mean prompt 237, mean output 34 tokens.
SLO (data/slo.yaml): TTFT p95 <= 0.8 s (engine target 0.77 s), TPOT p95 <= 50 ms, ITL p99 <= 100 ms.

## Measured vs simulated, identical trace

| max_num_seqs | source | TTFT p50 (ms) | TTFT p95 (ms) | TPOT p50 (ms) | TPOT p95 (ms) | ITL p99 (ms) | goodput | out tok/s |
|---|---|---|---|---|---|---|---|---|
| 2 | measured | 3461 | 8499 | 5.6 | 6.6 | 15.3 | 9 % | 341 |
| 2 | L1 simulator | 4071 | 9599 | 6.1 | 6.5 | 8.2 | 7 % | 811 |
| 16 | measured | 13 | 108 | 8.5 | 14.5 | 39.7 | 100 % | 759 |
| 16 | L1 simulator | 12 | 37 | 6.8 | 8.6 | 17.9 | 100 % | 811 |

Measured SLIs use the L1 definitions in `instructor/reference/serving.py` (`summarize`, warm-up/cool-down exclusion set to 0 for this short replay); goodput = share of requests meeting both the TTFT target and the TPOT SLO. Simulator rows: `serving.simulate` on the same trace with this device's measured ceilings (GEMM 26.9 TFLOP/s, copy 197 GB/s, efficiency 1.0) and a one-point overhead calibration (1.62 ms per iteration) `[SIMULATED]`.

## Decode iterations (max_num_seqs = 16 run)

| Batch | steps | median (ms) | p95 (ms) | memory floor (ms) |
|---|---|---|---|---|
| 1 | 66 | 4.51 | 5.16 | 4.33 |
| 2 | 69 | 4.82 | 6.04 | 4.40 |
| 3 | 112 | 4.88 | 6.55 | 4.45 |
| 4 | 77 | 5.33 | 7.27 | 4.58 |
| 5 | 116 | 5.40 | 9.23 | 4.66 |
| 6 | 123 | 5.31 | 7.85 | 4.75 |
| 7 | 92 | 6.76 | 8.21 | 4.95 |
| 8 | 23 | 7.30 | 8.19 | 4.88 |
| 9 | 58 | 6.90 | 8.14 | 5.10 |
| 10 | 31 | 7.84 | 8.33 | 5.25 |
| 11 | 25 | 8.32 | 11.08 | 5.41 |
| 12 | 9 | 8.54 | 8.92 | 5.53 |
| 13 | 12 | 8.76 | 9.11 | 5.61 |
| 14 | 18 | 9.02 | 10.22 | 5.65 |
| 15 | 9 | 9.49 | 11.11 | 5.75 |
| 16 | 38 | 9.86 | 10.20 | 5.85 |

## Not runnable here

- **supported serving stack (vLLM/SGLang) with an open model, TP=8 on an HX8 node**. Probe: vllm installed=False, sglang installed=False, HF cache=False, network interfaces=['lo'] (container runs with --network none), GPUs=1. Needs: serving stack image, open model weights, 8-GPU node for TP=8. Fallback: minimal continuous-batching engine on a random-weight model, same trace shape.
- **L3 multi-replica routing, canary and rollback drill**. Probe: single host, no load balancer, no second node. Needs: 2+ nodes, load balancer. Fallback: two configurations compared under the identical trace on one replica.

## What to conclude

- Same model, same GPU, same trace: raising max_num_seqs 2 -> 16 moved goodput 9 % -> 100 % and TTFT p95 8499 -> 108 ms. With few slots the queue, not the model, sets TTFT.
- Decode steps barely slow as the batch grows (each step streams the weights once), which is why continuous batching buys throughput almost for free until KV capacity or the TPOT SLO binds.
- Where measured and simulated rows differ, the usual causes are: the engine prefills one prompt per iteration (the simulator packs prefill and decode into one budgeted iteration), Python launch overhead that varies with batch, and other tenants on the GPU. Name the cause before trusting either number.
- This is a **laptop Ada GPU with a ~0.4 B-parameter random model, not W-INFER 70B on an HX8 node**: only the mechanisms transfer, not the milliseconds.

- Trace: first N requests of data/trace_s1.csv; prompt and output lengths / 8 (capped), inter-arrival times / compress. Arrivals replayed in real time (open loop).
- Latencies are engine-side wall clock (perf_counter) including queueing; each step synchronises on its sampled tokens, as a real engine must before streaming them.
- A short warm-up replay precedes each measured replay; one measured replay per configuration (every request is one sample: percentiles are over requests and token gaps).
