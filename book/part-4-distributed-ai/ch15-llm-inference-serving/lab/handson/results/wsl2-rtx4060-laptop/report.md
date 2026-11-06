# Chapter 15 hands-on: serve an LLM (run `wsl2-rtx4060-laptop`)

GPU: NVIDIA GeForce RTX 4060 Laptop GPU, 8188 MiB, 592.82; kernel 6.18.54.1-rxe+; captured 2026-11-05T03:02:51+00:00.
Tools: 0.30.0; 2.13.0+cu130 13.0; NVIDIA GeForce RTX 4060 Laptop GPU, 592.82, 8188 MiB, 3105 MHz, [N/A]; Qwen/Qwen2.5-1.5B-Instruct@989aa7980e4cf806f80c7fef2b1adb7bc71aa306.
KV-usage metric exposed by this vLLM: `vllm:kv_cache_usage_perc`.

## Step 1: latency and throughput against concurrency

closed loop, C concurrent clients; prompt uniform 256-1024 tokens (random token IDs), output exactly 128 tokens (ignore_eos); N = max(16, 4C) requests per repetition.

| C | TTFT p50 ms | TTFT p95 ms | TPOT p50 ms | ITL p50 ms | ITL p99 ms | output tok/s | req/s | peak KV % |
|---|---|---|---|---|---|---|---|---|
| 1 | 86.52 | 119.62 | 13.52 | 13.55 | 20.2 | 70.8 | 0.55 | 1.0 |
| 2 | 137.91 | 236.69 | 13.96 | 13.85 | 21.16 | 132.1 | 1.03 | 1.8 |
| 4 | 279.77 | 498.79 | 14.36 | 14.05 | 21.25 | 237.4 | 1.85 | 3.2 |
| 8 | 385.95 | 642.91 | 16.13 | 14.49 | 79.63 | 417.2 | 3.26 | 6.2 |
| 16 | 585.13 | 1202.45 | 19.99 | 15.49 | 225.08 | 642.3 | 5.02 | 12.0 |
| 32 | 724.42 | 1994.39 | 29.67 | 17.48 | 240.07 | 904.7 | 7.07 | 22.7 |

All values `[MEASURED]` (step 1), median over repetitions. Weights / TPOT at C=1 = 236.7 GB/s of weight reads per decode step (derived from `[MEASURED]` values).

## Step 2: prefix caching off vs on

shared prefix 1,536 tokens + 64 unique tokens per request; output 16 tokens; c=1 (24 requests) and c=8 (48 requests); identical prompts in both modes.

| Mode, C | TTFT p50 ms | TTFT p95 ms | prefix hit rate | output tok/s |
|---|---|---|---|---|
| off-c1 | 206.7 | 212.02 | 0.0 | 38.7 |
| off-c8 | 582.11 | 1154.35 | 0.0 | 74.8 |
| on-c1 | 31.67 | 38.36 | 0.92 | 64.9 |
| on-c8 | 95.13 | 267.84 | 0.94 | 374.7 |

TTFT p50 speed-up from prefix caching: C=1: 6.53x, C=8: 6.12x `[MEASURED]` (step 2).

## Step 3: KV pressure and preemption

32 concurrent clients, 64 requests, prompt 1,024 tokens, output 512 tokens (peak 32 x 1,536 = 49,152 tokens of KV demand).

| --gpu-memory-utilization | peak KV % | preemptions | max running | max waiting | TTFT p95 ms | ITL p99 ms | ITL max ms | output tok/s |
|---|---|---|---|---|---|---|---|---|
| 0.55 | 100.0 | 20.0 | 32.0 | 27.0 | 5368.92 | 238.43 | 8284.56 | 876.8 |
| 0.80 | 43.7 | 0.0 | 32.0 | 28.0 | 3716.57 | 244.41 | 256.33 | 1162.9 |

All values `[MEASURED]` (step 3).

## Step 4: KV capacity, theory against usable

KV bytes per token = 2 x 28 x 2 x 128 x 2 = 28,672 B. GPU memory 8585740288 B; weights 3199750635.52 B (engine log) `[MEASURED]`.
Theoretical (all memory minus weights): 187,848 tokens = 45 sequences of 4,096 tokens.

| util | free at start GiB | after fraction, tokens | engine KV tokens | reserve GiB (non-torch / activation / graphs) | 4k seqs | with 90 % headroom | usable / theoretical |
|---|---|---|---|---|---|---|---|
| 0.45 | 6.93 | 23,152 | 7,616 | 0.415 (0.14 / 0.27 / 0.08) | 1 | 0 | 0.0 |
| 0.55 | 6.93 | 53,097 | 37,552 | 0.415 (0.14 / 0.27 / 0.08) | 9 | 8 | 0.178 |
| 0.65 | 6.93 | 83,042 | 67,504 | 0.415 (0.14 / 0.27 / 0.08) | 16 | 14 | 0.311 |
| 0.8 | 6.93 | 127,959 | 112,416 | 0.415 (0.14 / 0.27 / 0.08) | 27 | 24 | 0.533 |
| 0.9 | | 157,903 | refused to start: ValueError: Free memory on device cuda:0 (6.93/8.0 GiB) on startup is less than desired GPU memory utilization (0.9, 7.2 GiB). Decrease GPU memory utilization or reduce GPU memory used by other proces | | | | |

Table 15.3a, walked on this GPU at --gpu-memory-utilization 0.80:

| Step | KV tokens | 4k sequences |
|---|---|---|
| Theoretical: GPU memory - weights | 187,848 | 45 |
| Memory fraction 0.80 (--gpu-memory-utilization) | 127,959 | 31 |
| Runtime reserve: non-torch + peak activation + CUDA graphs (engine profile) | 112,416 | 27 |
| Block rounding (16-token blocks; 4,096 = 256 blocks exactly) | 112,416 | 27 |
| Admission headroom: run at <= 90 % KV usage | 101,174 | 24 |

Usable / naive: 0.533 here; the chapter's TP = 4 FP8 replica: 140 / 186 = 0.753 `[MODELED]`.

Engine KV tokens and weights `[MEASURED]` (step 4, engine start-up log); the other columns are arithmetic on them.

## Step 5: --max-num-seqs under the same 32-client load

32 concurrent clients, 96 requests, prompt uniform 256-1024, output 128; --gpu-memory-utilization 0.80.

| --max-num-seqs | max running | max waiting | TTFT p50 ms | TTFT p95 ms | TPOT p50 ms | output tok/s | engine KV tokens |
|---|---|---|---|---|---|---|---|
| 4 | 4.0 | 28.0 | 14530.51 | 14845.3 | 14.6 | 246.8 | 117600 |
| 16 | 16.0 | 25.0 | 3470.13 | 4091.67 | 21.21 | 658.2 | 116064 |
| 64 | 32.0 | 25.0 | 885.17 | 2239.86 | 29.89 | 879.7 | 112416 |

All values `[MEASURED]` (step 5).

## Host memory

Lowest MemAvailable during the run: 364 MiB; largest server process-tree RSS: 4942 MiB `[MEASURED]`. Whole run: 1017 s `[MEASURED]`.
