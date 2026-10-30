# Capstone D starter kit: capacity model and serving simulator for W-INFER

You will build the quantitative core of an LLM inference platform design. A **capacity model** tells
you how many KV-cache tokens a replica holds and what a prefill or decode iteration costs. A
**request-level discrete-event simulator** of continuous batching with paged-KV admission, chunked
prefill and preemption turns a request trace into TTFT, TPOT, per-token inter-token latency (ITL),
end-to-end latency, throughput and
goodput. Around those sit **SLO math** (error budget, burn rate), an **automated rollback gate** and a
**cost per million tokens**. Every serving-configuration argument in your design pack should be backed
by these outputs, labelled correctly.

> **Realism boundary:** Capacity numbers are `[MODELED]`; latency and throughput are `[SIMULATED]`. The
> simulator models one replica at iteration granularity with a roofline cost: an overhead plus the
> larger of compute and HBM-traffic time. It does not capture kernel efficiency changes with batch shape,
> tensor-parallel all-reduce variance, CPU scheduling overhead, tokenization, network or load-balancer
> latency, prefix caching, speculative decoding, or clock behaviour. Real serving stacks differ. The L2
> extension is how you find out by how much.

## 1. Goal and the real-world task it mirrors

Halcyon AI's Inference team must choose a serving configuration for the 70B chat model on HX8 nodes,
size the fleet for the traffic forecast, and define the SLOs, load tests and rollout gates that will
protect users. Before anyone books GPUs for a load test, a platform engineer builds exactly this model
to narrow the options.

## 2. Tier and realism

| Tier | What you do | Evidence class |
|---|---|---|
| L1 (required) | Implement `starter/serving.py`; pass `check.py`; sweep configurations and load | `[MODELED]`, `[SIMULATED]` |
| L2 (optional) | Run a supported open model on a real serving stack with the same trace shape | `[MEASURED]` on that node |
| L3 (optional) | Multi-replica routing, canary and rollback drill | `[MEASURED]` |

## 3. Setup

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r ../../../requirements.txt
# (instructor edition only) python tools/generate_data.py regenerates data/ byte-identically
python check.py
```

## 4. Inputs (`data/`)

| File | Contents |
|---|---|
| `trace_s1.csv` … `trace_s5.csv` | Five independent 15-minute traces for one node at load 1.0 (≈ 5 req/s, ≈ 4,500 requests each): arrival, prompt and output tokens, tenant (`chat`, or `rag-long` with ≈ 32k-token prompts). Results use a steady-state window that excludes the first and last 60 s, and are reported as the median and range across seeds |
| `model.yaml` | W-INFER architecture: 80 layers, 8 KV heads, head dim 128, BF16 KV |
| `hardware.yaml` | Per-GPU HBM capacity and bandwidth, peak FLOP/s by dtype, efficiencies, runtime reserve, per-iteration overhead |
| `configs.yaml` | Four candidate configurations (TP, dtype, `max_num_seqs`, `max_num_batched_tokens`, chunked prefill, `max_model_len`, `gpu_memory_utilization`, replicas per node) |
| `slo.yaml` | TTFT p95 ≤ 0.8 s end to end for prompts up to 2,048 tokens, with a 30 ms `[ILLUSTRATIVE]` frontend budget (engine target 0.77 s); TPOT p95 ≤ 50 ms (per-request mean); ITL p99 ≤ 100 ms (per-token gaps) `[ILLUSTRATIVE]`; 99.9 % availability over 30 days; warm-up/cool-down exclusion |
| `economics.yaml` | `[ILLUSTRATIVE]` cost per GPU-hour and fleet utilization |
| `vendor_sizing_sheet.csv` | A third-party sizing sheet. Check its units before you trust it |

The configuration knobs are named after vLLM's engine arguments (`--tensor-parallel-size`,
`--max-num-seqs`, `--max-num-batched-tokens`, `--enable-chunked-prefill`, `--gpu-memory-utilization`,
`--max-model-len`) `[VENDOR-SPEC, 2026-10]`. Defaults and semantics change between releases, so verify
them against the version you run.

To model a TP = 4 configuration with 2 replicas per node, simulate one replica at `rate_scale = 0.5`
(half the node's traffic). For load sweeps, multiply that by the node load factor.

## 5. Background

[Chapter 15](../../../book/part-4-distributed-ai/ch15-llm-inference-serving/) (prefill/decode, KV cache,
continuous batching, chunked prefill, quantization, the end-to-end request path),
[Chapter 4](../../../book/part-2-accelerated-compute/ch04-gpu-architecture-cuda-execution/) and
[Chapter 6](../../../book/part-2-accelerated-compute/ch06-gpu-performance-engineering/) (roofline),
[Chapter 18](../../../book/part-5-production-operations/ch18-observability-slos-incident-response/) (SLOs,
error budgets, burn-rate alerts), [Chapter 20](../../../book/part-5-production-operations/ch20-automation-safe-change/)
(canary and rollback), [Chapter 21](../../../book/part-5-production-operations/ch21-capacity-power-economics/) (cost).

Key formulas:

```text
KV bytes/token   = 2 × layers × kv_heads × head_dim × bytes        = 2 × 80 × 8 × 128 × 2 = 327,680 B (320 KiB)
KV budget        = tp × HBM × gpu_memory_utilization − weights − tp × runtime reserve
prefill compute  = (2 × params × tokens + 2 × L × d × ((p+c)² − p²)) / (tp × peak × MFU)   (linear + causal attention)
decode memory    = (weights + KV bytes read) / (tp × HBM BW × efficiency)
error budget     = (1 − availability) × window       → 99.9 % over 30 days = 43.2 min
burn rate        = error rate / (1 − availability)
```

## 6. Tasks (100 points)

| # | Task | Acceptance criterion | Points |
|---|---|---|---|
| 1 | `kv_bytes_per_token`, `capacity`, `attention_flops`, `iteration_time_s` | Checks 01–03 pass; capacity table for all four configurations in your pack | 15 |
| 2 | `simulate` (including per-token ITL capture and rejection of requests that can never fit) | Checks 04–05 pass | 20 |
| 3 | `summarize`, `replicate`, `aggregate`; run all configurations on all 5 seeds at node load × 1.0 and × 2.0 | Checks 06–09 pass; results table with median and range, unstable points flagged, labelled `[SIMULATED]` | 15 |
| 4 | Load sweep: the highest node load at which each configuration meets the SLO, for mixed traffic and for chat-only traffic | Table + chart in `templates/capacity-model.md` | 15 |
| 5 | `error_budget_minutes`, `burn_rate`, `rollback_decision` | Check 10 passes; SLO/SLI spec and rollout plan written | 15 |
| 6 | `cost_per_million_tokens`; fleet size and cost for the traffic forecast in `templates/capacity-model.md` | Check 11 passes; cost analysis | 10 |
| 7 | Load-test plan for the L2 extension | `templates/load-test-plan.md` | 10 |

## 7. Running the checker

```bash
python check.py
python check.py --impl solution    # instructor edition only
```

## 8. Extensions: L2/L3

> **Safety:** Load-test only on capacity reserved for you. Never point a load generator at a
> production endpoint, and never run a canary drill on live traffic without the rollout owner's approval.

Run a supported open model on a supported serving stack. For example, with vLLM:

```bash
vllm serve <model> --tensor-parallel-size 8 --max-num-seqs 256 --max-num-batched-tokens 2048 \
    --enable-chunked-prefill --gpu-memory-utilization 0.90 --max-model-len 32768
```

Replay a trace with the same arrival process and length distributions using a load generator that
records per-request TTFT and inter-token latency. vLLM ships a serving benchmark script, and other
stacks have equivalents, so check your version's documentation for its arguments. Compare two
configurations under an identical trace on identical hardware. Warm up first, run ≥ 5 repetitions,
and report p50/p95/p99 with spread. Record every field under `extensions` in `manifest.yaml`.
Then compare measured TTFT, TPOT and ITL percentiles with your simulator, and explain the gaps.

## 9. Deliverable

All templates in [`../templates/`](../templates/), your `serving.py`, and checker output.
