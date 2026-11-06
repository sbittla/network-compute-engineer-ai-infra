# Chapter 15 hands-on lab: serve an LLM on one GPU

## 1. What you will do

You run the job of an inference engineer bringing up a new serving configuration. You start a real
engine, vLLM 0.30.0, serving a real instruct model, Qwen2.5-1.5B-Instruct, on one GPU. You drive it with a
load generator you can read in full (`loadgen.py`, about 150 lines of async HTTP with streaming), and you
measure what Sections 15.1 to 15.5 describe: TTFT, ITL, TPOT and throughput as concurrency rises, what
prefix caching buys on a shared prefix, how the KV cache fills and preempts, and how
`--gpu-memory-utilization` and `--max-num-seqs` set capacity. Last, you walk Table 15.3a from theoretical
to usable KV capacity with this GPU's measured numbers.

## 2. What is real here, and what is not

Real: the engine, the model weights, the CUDA kernels, continuous batching, the paged KV cache, prefix
caching and recompute preemption are vLLM's own, running on a real GPU. Every latency comes from
streamed server-sent events timed on the client, and every KV and scheduler number comes from the
engine's start-up log or its Prometheus `/metrics` endpoint.

Not real, or not ORION:

- **One small model on one laptop GPU.** W-INFER is 70B on TP = 4 or 8 H100-class GPUs with 3.35 TB/s of
  HBM each; here a 1.5B model runs on an RTX 4060 Laptop GPU with 8 GB of GDDR6 at about 256 GB/s, TP = 1.
  Absolute milliseconds and tokens/s do not transfer. What transfers is the mechanism and the shape:
  decode time set by bytes read per step, throughput rising with batch while each step slows, TTFT
  rising with queueing, prefix caching removing prefill work, a full KV pool preempting, and the ordered
  subtractions of Table 15.3a.
- **Synthetic prompts.** Prompts are random token IDs, so prompt length is exact and no tokenizer is
  involved, and output length is fixed with `ignore_eos`. Real chat traffic has length distributions
  (the canary trace in Part B of the Level 1 lab) and real text; the model's answers here are nonsense,
  which does not matter to the serving path.
- **Closed-loop load.** C clients each send the next request when the last one finishes. That measures
  capacity at a fixed concurrency, not behaviour under Poisson arrivals at a stated rate, which is what
  Section 15.7's queueing model and `vllm bench serve --request-rate` describe.
- **WSL2 and a shared display GPU.** Windows keeps about 1 GiB of the 8 GiB for itself, so the engine sees
  6.9 GiB free at start-up. There is no DCGM, no NVLink and no TP all-reduce. vLLM detects WSL and turns
  off pinned host memory.
- **No disaggregation, no RDMA KV transfer.** One GPU cannot show Sections 15.9-15.10.

The Level 3 extension in [../README.md](../README.md) (Section 9) covers what one GPU cannot: a
multi-GPU engine with TP, `vllm bench serve` at stated request rates, and disaggregated prefill and
decode over RDMA.

## 3. Requirements

| Item | Need |
|---|---|
| GPU | Yes, NVIDIA with 8 GB or more and a driver that supports CUDA 13 (tested: RTX 4060 Laptop, driver 592.82) |
| Docker | No |
| Root | No (`apt-get install python3-venv` only if `venv` is missing) |
| Disk | About 12 GB: the vLLM virtual environment (`~/.venvs/ch15-vllm`, about 9 GB with PyTorch 2.13 and CUDA 13 libraries) and the model (3.1 GB under `~/.cache/huggingface`) |
| RAM | 7 GB. The engine's processes peak at about 5 GB of resident memory during start-up; the run records the lowest available memory |
| Network | Only in `setup.sh` (PyPI and the Hugging Face Hub); `run.sh` runs offline (`HF_HUB_OFFLINE=1`) |
| Time | setup 10-20 min the first time (downloads); run about 17 min with a warm torch.compile cache (ten engine start-ups of 35-75 s each, plus the load), up to 25 min on the first run, plus any wait for the GPU lock |

## 4. Safety

- The lab installs into its **own** virtual environment, `~/.venvs/ch15-vllm`, and does not touch the
  shared hands-on environment or the system Python.
- The server listens on **127.0.0.1:18015** only, under the served model name `ch15-qwen`. Each server
  runs in its own session (`setsid`), and stopping it kills the whole session, including vLLM's
  engine-core child process. `teardown.sh` kills anything left with that name, frees the port and checks
  both; `run.sh` calls it on exit, even after a failure.
- The run holds the shared GPU lock (`/tmp/handson-gpu.lock`) for its whole length, since a vLLM server
  claims most of the GPU's memory. No clocks, power limits, interfaces or routes change.
- torch.compile is limited to 4 worker threads (`TORCHINDUCTOR_COMPILE_THREADS=4`): by default it starts
  one per CPU, and 24 of them crowd a 7 GB WSL2 machine during model load.

## 5. Setup

```bash
cd book/part-4-distributed-ai/ch15-llm-inference-serving/lab/handson
bash setup.sh          # idempotent; pinned: vllm==0.30.0, Qwen/Qwen2.5-1.5B-Instruct@989aa79...
```

`lab.env` holds the pinned versions, the port and the venv path. `setup.sh` prints the versions it
installed (vLLM 0.30.0, PyTorch 2.13.0 with CUDA 13.0, transformers 5.22.1, aiohttp 3.14.5).

Two environment settings in `experiments.sh` are workarounds you should know about:

- `VLLM_USE_FLASHINFER_SAMPLER=0`. FlashInfer's top-k/top-p sampler compiles itself with `nvcc` at first
  use, and the pip wheels do not include the CUDA compiler, so engine start-up fails with `Could not find
  nvcc`. The PyTorch sampler is used instead; with greedy decoding it makes no difference to the results.
- `HF_HUB_OFFLINE=1`, so a run never reaches the network and always uses the pinned snapshot.

## 6. Steps

`run.sh` runs all five steps unattended:

```bash
bash run.sh my-run                 # -> results/my-run/ ; about 17-25 min
python3 check.py results/my-run
```

To repeat one step while you explore, start a server by hand and point the load generator at it:

```bash
. lab.env; export VLLM_USE_FLASHINFER_SAMPLER=0 TORCHINDUCTOR_COMPILE_THREADS=4
flock /tmp/handson-gpu.lock $CH15_VENV/bin/vllm serve $CH15_MODEL --revision $CH15_MODEL_REVISION \
  --served-model-name ch15-qwen --port 18015 --max-model-len 4096 \
  --gpu-memory-utilization 0.80 --max-num-seqs 64 --no-enable-prefix-caching
# in another shell
$CH15_VENV/bin/python loadgen.py --concurrency 8 --num-requests 32 --out /tmp/c8.jsonl
curl -s localhost:18015/metrics | grep -E 'vllm:(kv_cache_usage_perc|num_requests_(running|waiting)|num_preemptions_total)'
bash teardown.sh                   # when you are done
```

Answer each step's question in `results/<run-id>/answers.md`.

### Step 1: latency and throughput against concurrency

The base server runs at `--gpu-memory-utilization 0.80`, `--max-num-seqs 64`, `--max-model-len 4096`,
prefix caching off. The load generator runs closed loop at C = 1, 2, 4, 8, 16 and 32 concurrent clients,
three repetitions each, N = max(16, 4C) requests per repetition. **Workload:** prompt length uniform on
256-1,024 tokens (seeded), output exactly 128 tokens (`max_tokens = min_tokens = 128`, `ignore_eos`),
greedy. TTFT is the time to the first streamed chunk; ITL is every gap between chunks; TPOT is
(last chunk − first chunk) ÷ (output tokens − 1) per request. The check confirms the engine streams one
chunk per token, so the chunk gaps really are token gaps.

Look at: output tokens/s rising with C while TPOT rises more slowly; TTFT rising with C; ITL p99 well
above ITL p50 once C > 1. In `raw/server-base.log`, find the engine's `max_num_batched_tokens` (the
prefill token budget per step).

**Question 1.** At C = 1, divide the weight bytes (engine log, "Model loading took") by TPOT. What
bandwidth does that imply, and why is it the right model of a decode step at batch 1 (Section 15.2)? Why
does throughput keep rising to C = 32 while each user's tokens/s falls?

### Step 2: prefix caching off and on

The same shared-prefix workload runs on the base server (prefix caching off) and then on a second server
started with `--enable-prefix-caching`. **Workload:** a 1,536-token prefix shared by every request plus
64 tokens unique to each request, 16 output tokens; C = 1 (24 requests) and C = 8 (48 requests); identical
prompts in both modes. The hit rate comes from the counters `vllm:prefix_cache_hits_total` and
`vllm:prefix_cache_queries_total`, read before and after each load.

Look at: TTFT p50 and p95 off against on, and the hit rate.

**Question 2.** The hit rate is not 1.0 even though 96 % of every prompt is shared. Account for the
missing part with the block size, and say what the speed-up would be for a 200-token shared prefix.

### Step 3: KV pressure and preemption

The same overload, 32 clients sending 64 requests of 1,024 prompt tokens and 512 output tokens (peak
demand 32 × 1,536 = 49,152 tokens of KV), runs at `--gpu-memory-utilization` 0.80 and 0.55. A sampler
reads `/metrics` every 250 ms: `vllm:kv_cache_usage_perc` (older releases: `vllm:gpu_cache_usage_perc`;
`metrics_sampler.py` accepts both), `vllm:num_requests_running`, `vllm:num_requests_waiting` and
`vllm:num_preemptions_total`.

Look at: peak KV usage, the preemption count, and ITL max at each setting (`raw/metrics-pressure-*.jsonl`).

**Question 3.** Compare the result with the preemption-storm signature in Section 15.5. Which parts of
the signature appear, which do not, and what does the ITL maximum tell you about the cost of a recompute
preemption?

### Step 4: KV capacity against `--gpu-memory-utilization`

Fresh servers start at `--gpu-memory-utilization` 0.45, 0.55, 0.65, 0.80 and 0.90. From each start-up
log the analysis takes the weights, the KV memory and tokens, and the engine's own breakdown of the
reserve (non-torch memory, peak activation, CUDA graph pool). It then walks Table 15.3a at 0.80. KV bytes
per token for Qwen2.5-1.5B (28 layers, 2 KV heads of 128, BF16) = 2 × 28 × 2 × 128 × 2 = 28,672 B.

Look at: which setting refuses to start and why (`raw/server-util0.90.log`); how KV tokens grow with the
fraction; the usable/naive ratio against the chapter's 140/186.

**Question 4.** Why does 0.90 refuse to start on this machine, when 0.90 is a normal value on an H100?
Which row of Table 15.3a costs the most here, and why is that different from the TP = 4 FP8 replica in
the chapter?

### Step 5: `--max-num-seqs` under the same load

The same 32-client load (96 requests, prompt 256-1,024, output 128) runs on servers with
`--max-num-seqs` 4, 16 and 64, all at `--gpu-memory-utilization 0.80`.

Look at: the running batch never exceeding the cap, the waiting queue, TTFT, TPOT and throughput.

**Question 5.** Which latency gets better and which gets worse as the cap falls? Relate it to the
chapter's statement that `--max-num-seqs` "protects TPOT" (Section 15.4).

## 7. Check your results

```bash
python3 check.py results/<run-id>
python scripts/handson.py check ch15 <run-id>     # from the repo root, also on Windows
```

The checks test mechanism, not equality with the reference run: throughput at C = 32 at least 4× C = 1;
TPOT and TTFT rising with C; about one streamed chunk per token; prefix caching hitting only when
enabled and cutting TTFT p50 by at least 1.3×; the small KV pool reaching ≥ 90 % usage and preempting
while the large one does not, with the small pool's worst token gap at least 3× the large one's; KV
tokens rising with the memory fraction, below each successive bound of Table 15.3a; the running batch
never above `--max-num-seqs`; the server's peak resident memory under 85 % of host memory and no server
log showing an out-of-memory death. Each FAIL line says what was expected. A bundle with a file missing
fails at the first check, `C0 ... present`, and names the file.

## 8. Reference results

Evidence: [`results/wsl2-rtx4060-laptop/`](results/wsl2-rtx4060-laptop/) (`report.md`, `summary.json`,
`environment.json`, and `raw/` with every server log, load-generator record and `/metrics` scrape).
RTX 4060 Laptop GPU (8 GiB), driver 592.82, WSL2 kernel 6.18.54.1, vLLM 0.30.0, PyTorch 2.13.0+cu130,
Qwen2.5-1.5B-Instruct at revision 989aa79. All values `[MEASURED]`.

**Step 1: concurrency sweep** (median of three repetitions; prompt 256-1,024 tokens, 128 output tokens).

| C | TTFT p50 ms | TTFT p95 ms | TPOT p50 ms | ITL p99 ms | output tok/s |
|---|---|---|---|---|---|
| 1 | 87 | 120 | 13.5 | 20 | 71 |
| 4 | 280 | 499 | 14.4 | 21 | 237 |
| 8 | 386 | 643 | 16.1 | 80 | 417 |
| 16 | 585 | 1,202 | 20.0 | 225 | 642 |
| 32 | 724 | 1,994 | 29.7 | 240 | 905 |

At C = 1 a decode step takes 13.5 ms. The engine log puts the weights at 2.98 GiB (3.20 GB), and 3.20 GB ÷
13.5 ms = 237 GB/s, about 92 % of the GDDR6's 256 GB/s. That is what Section 15.2 predicts for batch 1:
each step reads every weight once and does almost no arithmetic per byte. Going from C = 1 to C = 32 makes
each step only 2.2× slower (13.5 to 29.7 ms), because the weights are still read once per step and now
serve 32 sequences. Output throughput rises 12.8× (71 to 905 tok/s). Each user's speed falls from 71 to
28 tok/s. TTFT rises 8× because a new prompt waits behind other prompts' prefill. The ITL p99 tail
(80-240 ms against a 14-17 ms p50) is decode steps that share their batch with a long prefill.

**Step 2: prefix caching** (1,536 shared + 64 unique prompt tokens, 16 output tokens).

| C | TTFT p50 off ms | TTFT p50 on ms | speed-up | hit rate on |
|---|---|---|---|---|
| 1 | 207 | 32 | 6.5× | 0.92 |
| 8 | 582 | 95 | 6.1× | 0.94 |

With the cache on, only the 64 unique tokens, plus the first request's full prompt, are prefilled. The
remaining 1,536 tokens are 96 whole 16-token blocks, already in the cache. TTFT falls to what a 64-token
prefill and one decode step cost. At C = 8, output throughput rose from 75 to 375 tok/s because the
batch no longer spends its compute on repeated prefill. (A scratch run during development measured
only 1.65× at C = 1, 120 ms with the cache on. The check's 1.3× floor allows for that run-to-run spread.)

**Step 3: KV pressure** (32 clients, 1,024-token prompts, 512 output tokens: 49,152 tokens of peak demand).

| --gpu-memory-utilization | KV pool tokens | peak KV % | preemptions | ITL max ms | output tok/s |
|---|---|---|---|---|---|
| 0.55 | 37,552 | 100 | 20 | 8,285 | 877 |
| 0.80 | 112,416 | 44 | 0 | 256 | 1,163 |

The 0.55 pool is smaller than the demand, so it filled, and vLLM preempted 20 sequences by recompute. A
preempted sequence loses its KV and waits; when it is readmitted, its prompt and the tokens generated so
far are prefilled again. That user sees one 8.3 s gap between tokens, against a 256 ms worst gap with the
larger pool. Throughput fell 25 %, because the recomputed prefill is work done twice. This is Section
15.5's preemption-storm signature in miniature: usage pinned at 100 %, preemptions climbing, a long ITL
tail.

**Step 4: capacity against `--gpu-memory-utilization`.** Engine KV tokens: 7,616 (0.45), 37,552 (0.55),
67,504 (0.65), 112,416 (0.80). 0.90 refuses to start: `Free memory on device cuda:0 (6.93/8.0 GiB) on
startup is less than desired GPU memory utilization (0.9, 7.2 GiB)`. The fraction is of *total* memory,
and Windows keeps about 1 GiB of this card for the display. The Table 15.3a walk at 0.80:

| Step | KV tokens | 4,096-token sequences |
|---|---|---|
| Theoretical: GPU memory − weights | 187,848 | 45 |
| `--gpu-memory-utilization 0.80` | 127,959 | 31 |
| Runtime reserve (non-torch 0.14 + activation 0.27 + CUDA graphs 0.08 GiB) | 112,416 | 27 |
| Block rounding (4,096 = 256 blocks exactly) | 112,416 | 27 |
| Admission headroom (≤ 90 % KV) | 101,174 | 24 |

Usable over theoretical is 24/45 = 0.53, against the chapter's 140/186 = 0.75. The memory fraction is
the largest subtraction here: 20 % of an 8 GiB card is 1.6 GiB, half the size of the weights. The
0.415 GiB runtime reserve is the same at every setting, so a small fraction loses most of its pool to it:
at 0.45 only 7,616 tokens are left, less than two 4,096-token sequences.

**Step 5: `--max-num-seqs`** (32 clients, 96 requests, 128 output tokens).

| --max-num-seqs | max running | TTFT p50 ms | TPOT p50 ms | output tok/s |
|---|---|---|---|---|
| 4 | 4 | 14,531 | 14.6 | 247 |
| 16 | 16 | 3,470 | 21.2 | 658 |
| 64 | 32 | 885 | 29.9 | 880 |

The cap held exactly. A cap of 4 gives the fastest decode step, 14.6 ms, close to the C = 1 figure,
but 28 requests wait in the queue, so TTFT is 14.5 s and throughput is 28 % of the uncapped server's.
The cap protects TPOT by moving delay into the queue, where TTFT pays for it (Sections 15.4 and 15.7).

**Host.** The whole run took 1,017 s with a warm compile cache. The largest server process tree used
4,942 MiB of resident memory, and the lowest MemAvailable in the WSL VM was 364 MiB. That VM is shared:
another lab's job running alongside can push it lower, which is why the check tests the lab's own
footprint and looks for out-of-memory deaths instead.

Other GPUs will give other numbers. A GPU with more memory bandwidth lowers TPOT in proportion; one
with more memory moves every row of the capacity table.

## 9. Clean up

```bash
bash teardown.sh                      # stops any ch15 server; frees port 18015
rm -rf ~/.venvs/ch15-vllm ~/.cache/huggingface/hub/models--Qwen--Qwen2.5-1.5B-Instruct ~/.cache/vllm   # optional, frees ~12 GB
```

## 10. Connect to the chapter

| Step | Section | What it makes concrete |
|---|---|---|
| 1 | 15.1, 15.2, 15.4 | TTFT, TPOT, ITL and goodput definitions; decode as a weight-and-KV read per step; continuous batching trading per-user speed for throughput |
| 2 | 15.5 | Prefix caching skipping prefill for shared blocks |
| 3 | 15.5, 15.14 | Paged KV on demand, recompute preemption and the preemption-storm signature |
| 4 | 15.3 (Table 15.3a) | Theoretical against usable KV capacity; `--gpu-memory-utilization` as a share of total memory |
| 5 | 15.4, 15.7 | `--max-num-seqs` protecting TPOT and moving delay into the queue, where TTFT pays it |
