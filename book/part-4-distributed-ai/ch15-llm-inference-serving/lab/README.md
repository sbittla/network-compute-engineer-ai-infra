# Lab 15 — Inference Capacity Model, Serving-Trace Analyzer, and Disaggregation Model

## 1. Goal and the real-world task it mirrors

Halcyon AI's Inference team is preparing the W-INFER 70B chat service for a launch and has been
paged twice for TTFT (time to first token) SLO breaches on a canary pool. You have three jobs, and
each one matches work an inference infrastructure engineer does in a normal week:

1. **Capacity model (Part A).** Build the spreadsheet-killer: a small, tested Python model that
   turns model shape, precision, tensor parallelism (TP), and HBM size into KV-cache budget,
   maximum concurrent sequences, prefill time, and the HBM-bandwidth bound on decode throughput.
   Then use it to compare two serving configurations and recommend one for a latency-sensitive
   objective and another for a throughput-oriented one.
2. **Serving-trace analyzer (Part B).** Given a per-request trace (arrival, scheduling, first
   token, finish, sampled token gaps) and replica telemetry from the canary pool, compute TTFT,
   TPOT, ITL and end-to-end percentiles, SLO attainment and goodput, and *find what went wrong*.
   The trace contains three distinct problems. Your analyzer must find each one and classify it
   correctly. A problem that matches the wrong cause counts as a miss.
3. **Disaggregation model (Part C).** Model the same workload in a shared prefill+decode pool and
   in disaggregated prefill and decode pools over RDMA and TCP. Estimate KV bytes per request,
   aggregate transfer bandwidth at the target rate, transfer time, and the latency effects.
   Then model speculative decoding.

## 2. Tier and realism boundary

**Tier L1** (laptop, no GPU). Parts A and C produce `[MODELED]` numbers from stated formulas and
the assumptions in `data/configs.yaml`. Part B analyses a `[SIMULATED]` trace produced by
a seeded generator (instructor copy only, `tools/generate_trace.py`). That script is a discrete-event simulator of four continuous-batching
replicas with a paged KV cache and recompute preemption.

> **Realism boundary:** The simulator has no kernels, CUDA graphs, chunked prefill, prefix
> caching, TP all-reduce variance, tokenizer or HTTP overheads, and no GPU clock or thermal
> behaviour. Its decode step is a bandwidth formula with a fixed overhead. The trace teaches you
> how to *diagnose*, and its shapes look like real ones. It is not a measurement of any engine
> or GPU. Treat every number from this lab as MODELED or SIMULATED.

## 3. Setup

```bash
cd book/part-4-distributed-ai/ch15-llm-inference-serving/lab
python -m pip install -r ../../../../requirements.txt     # numpy, pandas, pyyaml
python check.py                                           # progress meter on starter/serving_lab.py
```

Python 3.10 or newer. The checker finishes in a few seconds.

## 4. Background you need

| Topic | Manuscript section |
|---|---|
| Request lifecycle, TTFT/TPOT/ITL/goodput definitions | Section 15.1, Section 15.7 |
| Prefill vs decode arithmetic intensity | Section 15.2 |
| KV-cache sizing and memory budget | Section 15.3 |
| Continuous batching, paged KV cache, preemption | Section 15.4, Section 15.5 |
| Quantization effects on bytes moved | Section 15.6 |
| Little's law, M/D/1 waiting, phase SLOs | Section 15.7 |
| Disaggregation, KV transfer, transport choice | Section 15.9, Section 15.10 |
| Speculative decoding | Section 15.11 |

## 5. Data files

| File | Contents |
|---|---|
| `data/configs.yaml` | Model, GPU, workload, two serving configurations, disaggregation and speculative-decoding assumptions, trace SLOs |
| `data/requests.csv` | One row per request: `request_id, tenant, replica, arrival_s, sched_s, first_token_s, finish_s, prompt_tokens, output_tokens, preemptions` (times in seconds from trace start; `sched_s` = first admission to a batch) |
| `data/token_gaps.csv` | For a 5 % sample of requests (`request_id % 20 == 0`): `itl_ms`, the `;`-separated gaps between consecutive output tokens, in ms |
| `data/replica_telemetry.csv` | Every 5 s per replica: `num_running, num_waiting, kv_usage_pct, gpu_busy_pct, preemptions_total` (cumulative counter) |

The canary pool is four replicas (`r0`–`r3`), each serving W-INFER at **TP=2 with FP8 weights** on
two GPUs of one HX8 node (`orion-n29`, one of the 8 nodes in the Kubernetes inference partition;
W-TRAIN is not running at full size while it serves). The scheduler admits at most 48 concurrent sequences per
replica, and chunked prefill is disabled.

> **Deviation from the reference baseline:** ORION's baseline is TP = 8 BF16 or TP = 4 FP8.
> Halcyon canaries 4 × TP = 2 FP8 replicas per node as a cost-per-token experiment, to test whether
> 1–2k-token chat meets its SLOs at half the GPUs per replica. It is unsafe for long context: each
> replica keeps only 70 GB of KV (≈ 214k tokens), as Part A shows. Manuscript Section 15.3.

## 6. Tasks

Implement the functions in `starter/serving_lab.py`. The docstrings state formulas and units.
The loaders are already written for you.

**Part A — capacity model (30 points)**

1. `kv_bytes_per_token`. *Accept:* 327,680 B for W-INFER BF16 KV and 163,840 B for FP8 KV.
2. `kv_budget_bytes`, `max_concurrent_sequences`. *Accept:* 420 GB → 312 sequences of 4,096
   tokens (TP=8 BF16); 210 GB → 156 (TP=4 FP8); 70 GB → 52 (TP=2 FP8).
3. `prefill_time_s`, `decode_step_time_s`, `decode_tokens_per_s`. *Accept:* a 2,048-token prefill
   on TP=8 BF16 at 40 % MFU takes about 90.6 ms. The decode-step lower bound at batch 32 and
   context 2,176 is about 6.08 ms.
4. `compare_serving_configs`, `recommend_config`. *Accept:* the latency objective selects
   `L-tp8-bf16` and the throughput objective selects `T-tp4-fp8`. In your report, explain *why*
   using the TPOT and tokens/s/node columns.

**Part B — serving-trace analyzer (45 points)**

5. `request_metrics`, `latency_percentiles`, `itl_values_s`. Report TTFT, TPOT, ITL and e2e
   p50/p95/p99 for the whole trace and for the first 230 s (the healthy baseline).
6. `slo_report`. Report SLO attainment, goodput (SLO-meeting requests/s) and throughput for the
   whole trace and for the baseline.
7. `windowed`, `detect_issues`. Find every anomaly and classify it as `queueing_collapse`,
   `preemption_storm`, `capacity_shortfall` or `slow_replica`. *Accept:* the checker's B5–B7
   checks.
8. `telemetry_evidence`. For each episode, add the telemetry that *discriminates* between
   hypotheses: KV usage, waiting queue depth, preemption-counter delta, and GPU busy %. *Accept:*
   B8. In your report, explain why `gpu_busy_pct` does not help with any of the three diagnoses.

**Part C — disaggregation and speculative decoding (25 points)**

9. `kv_transfer_time_s`, `md1_wait_s`, `compare_designs`. Produce the three-row table (shared,
   disagg-rdma, disagg-tcp). *Accept:* C1–C3. In your report, state which values are MODELED and
   which assumption each one is most sensitive to.
10. `speculative_expected_tokens`, `speculative_speedup`. *Accept:* C4. Then explain why the
    speedup shrinks at large batch.

## 7. Running the checker

```bash
python check.py                    # your starter implementation; exits non-zero until all pass
python check.py --impl solution    # instructors only (needs ../solutions/lab/)
```

Each line reads `PASS`, `FAIL` (with a reason) or `TODO` (the function still raises
`NotImplementedError`).

## 8. Deliverable and grading rubric

**Deliverable (course outline, Chapter 15): an inference capacity model and tuning
recommendation.** Submit `serving_lab.py`, the checker output, and a report of at most two pages
containing:

| Item | Points |
|---|---|
| Part A checks A1–A6 pass | 20 |
| Configuration recommendation, latency vs throughput, with the numbers that justify it and one risk of each choice | 10 |
| Part B checks B1–B4 pass, with the percentile/SLO table for full trace vs baseline | 15 |
| Part B checks B5–B8 pass | 15 |
| Diagnosis narrative: for each anomaly, the symptom, the discriminating evidence, the root-cause hypothesis, and one safe mitigation | 15 |
| Part C checks C1–C4 pass | 10 |
| Disaggregation recommendation for the 40 req/s workload, transport choice, and what to measure at L2/L3 to confirm it; every number labelled MODELED/SIMULATED | 15 |
| **Total** | **100** |

## 9. Extensions — hardware-backed validation (L2/L3)

> **Safety:** Run these commands only on a dedicated lab host or lab cluster that you are
> authorized to load. Load generators can saturate shared frontend links, and RDMA tests can
> congest a shared fabric. Never point them at production endpoints or at a training fabric that
> is in use.

**L2: one GPU host, real serving engine.** The flags below are for vLLM. Flag names and the
benchmark entry point change between releases (`vllm bench serve` in recent releases;
`benchmarks/benchmark_serving.py` in older ones), so verify them with `--help` for the version you
install `[VENDOR-SPEC, 2026-10]`.

```bash
# Inventory for the manifest
nvidia-smi --query-gpu=name,driver_version,memory.total,clocks.max.sm,power.limit --format=csv
python -c "import vllm, torch; print(vllm.__version__, torch.__version__, torch.version.cuda)"

# Start a server (model must fit; use --tensor-parallel-size N on multi-GPU hosts)
vllm serve <model> --tensor-parallel-size 1 --max-num-seqs 64 \
    --gpu-memory-utilization 0.90 --max-model-len 8192

# Engine metrics while under load (names vary by version; check the /metrics output)
curl -s localhost:8000/metrics | grep -E 'vllm:(num_requests_(running|waiting)|num_preemptions|.*cache_usage)'

# Fixed-length synthetic load at a stated Poisson rate; repeat >= 5 times per configuration
vllm bench serve --model <model> --dataset-name random \
    --random-input-len 2048 --random-output-len 256 \
    --request-rate 4 --num-prompts 500 \
    --percentile-metrics ttft,tpot,itl,e2el --metric-percentiles 50,95,99

# GPU-side evidence in parallel (DCGM profiling fields: 1002 SM active, 1005 DRAM active)
dcgmi dmon -e 1002,1005 -d 1000
```

What to do with it:

* Sweep `--request-rate` to find the knee where TTFT p95 bends upward. Compare the knee with
  your Little's-law estimate.
* Compare `--max-num-seqs 64` with 256 at the same rate. Then repeat with `--kv-cache-dtype fp8`
  and with `--enable-chunked-prefill`, changing one variable at a time.
* Compare measured TPOT with `decode_step_time_s` for the same batch and context. The ratio tells
  you the real `hbm_efficiency` + overhead for your stack. Record it in the manifest. Do **not**
  copy it back into `configs.yaml` and call the model "validated".

**L3: two or more nodes, disaggregated serving over RDMA.** First baseline the transport:

```bash
# RDMA bandwidth between the prefill and decode nodes on the NIC local to the GPUs used
# --use_cuda=<gpu> exercises GPUDirect RDMA from/to that GPU's memory (perftest built with CUDA).
# -x 3 is the RoCEv2 GID index on this example host; confirm yours with `show_gids`
# (MLNX_OFED/DOCA) or `ibv_devinfo -v` before running.
ib_write_bw -d mlx5_0 -x 3 --use_cuda=0 -s 1048576 -D 10 --report_gbits             # decode node (server)
ib_write_bw -d mlx5_0 -x 3 --use_cuda=0 -s 1048576 -D 10 --report_gbits <decode-ip> # prefill node
nvidia-smi topo -m        # confirm GPU-NIC PIX locality for the GPUs serving each pool
```

Next, enable the engine's KV-transfer connector. In vLLM this is `--kv-transfer-config`, and the
connector names and JSON keys change between releases, so verify them `[VENDOR-SPEC, 2026-10]`.
Run the same `bench serve` workload against the shared and the disaggregated deployments, and
record TTFT, TPOT, and ITL p99. Also record switch-port ECN-mark, PFC-pause, and drop counters
before and after each run (Chapters 9 and 10). Measure the KV bytes per request from the
connector's logs or NIC counters, and compare them with `kv_bytes_per_request` from Part C.

Record everything listed under `extensions` in `manifest.yaml`. A result without its manifest is
not evidence.

## 10. Intentionally flawed inputs

The trace contains planted anomalies. Their descriptions, ground-truth windows, and the reasons
they were chosen are in the instructor folder (`solutions/lab/INSTRUCTOR_NOTES.md`) and are
deliberately left out of this guide.
