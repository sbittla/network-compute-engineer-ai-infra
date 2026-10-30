# Chapter 4 — Answer Key (INSTRUCTOR ONLY)

All device values from manuscript Table 4.1 (H100-SXM-class, `[VENDOR-SPEC, 2026-10]`). Computed values
are `[MODELED]` unless stated. Every number below was computed twice (by hand and with a Python
one-liner); the lab numbers are reproduced by `solutions/lab/trace_analysis.py`.

Marking scale per exercise: full marks require the stated evidence; deduct for missing units, missing
evidence labels, or a correct number with no arithmetic shown.

---

## Knowledge checks

**4.1** SM: a streaming multiprocessor, the GPU's replicated compute unit with its own schedulers,
register file, shared memory/L1 and tensor cores. Warp: 32 threads executing one instruction at a time
(SIMT). Thread block (CTA): up to 1,024 threads that run on one SM and can share shared memory and
barriers. Grid: all blocks of one kernel launch. (a) Placement unit: the **block** (assigned to one SM
for its lifetime). (b) Issue unit: the **warp**.
*Common mistake:* saying the thread is the unit of issue.

**4.2** A sector is 32 B.
- (a) 32 × 4 B = 128 B contiguous → 128 / 32 = **4 sectors**, useful 128 / 128 = **100 %**.
- (b) Stride 2 → addresses span 32 × 8 B = 256 B → **8 sectors**, useful 128 / 256 = **50 %**.
- (c) Stride 32 elements = 128 B apart → each thread in its own sector → **32 sectors** = 1,024 B,
  useful 128 / 1,024 = **12.5 %**.

**4.3** Any four, each with mechanism: `.item()`/`float()`/`.tolist()`/`.cpu()`/`print(t)` (value copied
D2H and the CPU waits); Python control flow on a tensor (`if t.any():`); data-dependent output shapes
(`x[mask]`, `nonzero`, `unique`, `masked_select`) — the CPU must learn the size to allocate; copies to/from
pageable memory (staging, host-blocking); `torch.cuda.synchronize()`/`empty_cache()` (via `cudaFree`).
*Marking:* 1 point per pattern with a correct mechanism.

**4.4** (1) Bandwidth: the driver stages through a pinned bounce buffer with a CPU memcpy, typically
10–25 GB/s vs ≈ 50 GB/s pinned on Gen5 x16 `[ILLUSTRATIVE]`. (2) Host blocking: the call does not return
until the data has been staged (or, D2H, until the copy completes), so the CPU cannot run ahead and queue
kernels. (3) No overlap: it serializes with the stream and cannot run concurrently with kernels the way a
pinned async copy on a side stream can.

**4.5** Percent of time over the sample period during which one or more kernels was executing. Example:
600 back-to-back four-block kernels use ≤ 4 of 132 SMs (3 %) at a fraction of per-SM throughput → GPU-Util
100 %, delivered FLOP/s < 1 % of peak. Revealing fields: `DCGM_FI_PROF_SM_ACTIVE` (low, ≈ 0.03 here),
`DCGM_FI_PROF_PIPE_TENSOR_ACTIVE` (≈ 0), `DCGM_FI_PROF_SM_OCCUPANCY`, `DCGM_FI_PROF_DRAM_ACTIVE`.

**4.6** NVTX ranges are recorded on the CPU thread. The CPU enqueues the 85 forward kernels
asynchronously in 2.3 ms and moves on; the GPU executes them over 19.6 ms. Each GPU activity carries the
correlation ID of the API call that launched it; joining activities whose launch call falls inside the
NVTX range gives the GPU-side extent of the range (Nsight Systems' "projected" NVTX ranges do this).
*Common mistake:* concluding that `log_loss` takes 17.6 ms (it is the CPU waiting for the forward pass).

**4.7** The GEMM issues asynchronous warp-group MMA instructions on tiles brought into shared memory by
TMA; a few warps keep many bytes and FLOPs in flight (high instruction-level and memory-level parallelism
per warp), and large tiles maximize reuse, so the tensor pipes stay fed. The layernorm backward is
memory-bound; with 8 warps per SM, each holding about three 128-B requests outstanding, it has
8 × 3.25 × 128 B ≈ 3.3 KB in flight versus ≈ 15.2 KB needed (Little's law, Section 4.3): 3.3 / 15.2 ≈ 22 % of
HBM bandwidth, which is what it achieves. (One request per warp would give only 1 KB ≈ 7 %; the kernel's
vectorized 16-B loads are what lift it to ≈ 3 KB.)

## Worked problems

**4.8**
(a) *w* = 128 / 32 = 4 warps per block.
- Warp limit: ⌊64 / 4⌋ = 16 blocks.
- Registers: 80 × 32 = 2,560 per warp (= 10 × 256, no rounding); ⌊65,536 / 2,560⌋ = 25 warps → 24 after the warp-allocation granularity of 4; ⌊24 / 4⌋ = 6 blocks.
- Shared memory: ⌊233,472 / (49,152 + 1,024)⌋ = ⌊233,472 / 50,176⌋ = ⌊4.65⌋ = 4 blocks.
- Block limit: 32.
- Resident = 4 blocks = 16 warps → 16 / 64 = **25 %**, limiter **shared memory**.

(b) Needed per SM = 3.35 × 10¹² B/s × 600 × 10⁻⁹ s / 132 = 2.01 × 10⁶ / 132 = **15,227 B ≈ 15.2 KB**.
In flight = 16 warps × 2 loads × 128 B = 4,096 B. Fraction ≈ 4,096 / 15,227 = **26.9 %** →
≈ 0.269 × 3.35 TB/s ≈ **0.90 TB/s** upper bound `[MODELED]`.

(c) Shared memory: ⌊233,472 / (32,768 + 1,024)⌋ = ⌊233,472 / 33,792⌋ = ⌊6.91⌋ = 6. Registers still 6.
Resident = 6 blocks = 24 warps → **37.5 %**; limiter **registers** (ties with shared memory; the Section 4.7
rule reports the first in order warps → registers → shared memory → blocks). In flight = 24 × 256 B =
6,144 B → 6,144 / 15,227 = **40.3 %** → ≈ **1.35 TB/s**.
*Marking:* 4 pts (a), 3 pts (b), 3 pts (c). Accept "shared memory and registers tie" for (c).
*Common mistake:* forgetting the 1 KB per-block reservation. It does not change these answers (without it:
233,472 / 49,152 = 4.75 → 4 and 233,472 / 32,768 = 7.1 → 7, still above the register limit of 6), but it does
at other sizes: with 45 KB (46,080 B) per block, 233,472 / 46,080 = 5.07 → 5 blocks without it, but
233,472 / 47,104 = 4.96 → **4** with it.

**4.9**
(a) CPU-limited: 400 × 10 µs = **4.0 ms** per iteration (plus the last kernel's 6 µs tail, negligible).
Kernel-busy = 400 × 6 µs / 4,000 µs = 2.4 / 4.0 = **60 %**.
(b) GPU-limited: 400 × 6 µs + 399 × 1 µs + ≈ 15 µs replay launch = 2,400 + 399 + 15 = **2,814 µs ≈ 2.81 ms**;
speed-up 4.0 / 2.81 = **1.42×**; kernel-busy 2.4 / 2.81 = 85 %.
(c) 256 MiB = 268,435,456 B. Pageable: 268,435,456 / 12 × 10⁹ = **22.4 ms**, serial and host-blocking →
iteration ≈ 22.4 + 4.0 = 26.4 ms (eager). Pinned: 268,435,456 / 50 × 10⁹ = **5.37 ms**. Prefetching hides
it only if compute per iteration ≥ copy time; with graphs compute is 2.81 ms < 5.37 ms, so the
steady-state iteration is max(2.81, 5.37) = **5.37 ms — copy-bound**. The honest answer is that PCIe, not
the GPU, sets throughput; reduce bytes per iteration (keep data resident, send token IDs rather than
dense tensors, compress). Deeper prefetching does not help: the link is bandwidth-bound, not latency-bound.
*Marking:* full marks require noticing the copy-bound steady state in (c).

## Hands-on lab (4.10) and Lab 4 — expected results

Reference results `[SIMULATED]` (solution module, default parameters):

| Metric | `train_step_41` | `train_step_42` |
|---|---|---|
| Step window | 85.57 ms | 85.89 ms |
| Busy (any) / busy (kernel) | 88.8 % / 78.6 % | 89.0 % / 78.5 % |
| Copy time / overlapped | 10.12 ms / 13.4 % | 10.44 ms / 13.1 % |
| `host_sync` gaps | 15 (4.91 ms) | 15 (4.77 ms) |
| `launch_bound` gaps | 600 (4.02 ms) | 600 (4.03 ms) |
| `dependency` gaps | 1 (0.31 ms) | 1 (0.31 ms) |

Findings and estimated savings per step (tool output; mean of 2 steps, idle/copy time only): PAGEABLE_H2D
8.85 ms; EXCESS_SYNC 4.84 ms; LAUNCH_BOUND 4.03 ms; STREAM_DEPENDENCY 0.31 ms; LOW_OCCUPANCY
(`layernorm_bwd_fused_kernel`) 2.44 ms; total 20.47 ms. The worked example (manuscript Table 4.5) uses step 41
and adds removed kernel time (hook reductions, tiny optimizer kernels): 8.77 / 5.30 / 5.55 / 0.31 / 2.43 =
22.36 ms, projecting 63.2 ms; the tool's basis projects ≈ 65.1 ms. Accept 63–65 ms with the basis stated. "Low occupancy by design":
the four GEMM families and both flash-attention kernels.

### Lab 4 — planted anomalies (do not distribute)

| # | Planted problem | Where in the data | Signature the learner should find | Magnitude per step |
|---|---|---|---|---|
| P1 | Pageable host-to-device copies of the input batch (96 MiB image tensor + 4 MiB labels) on the compute stream | `gpu_trace.csv` rows with `src_mem=pageable`, `bytes` ≥ 1 MiB; matching `cudaMemcpyAsync` calls last as long as the copy | 9.3–12.2 GB/s vs 48 GB/s pinned; host blocked; no kernel overlap; 2 small `host_sync` gaps after them | 8.70 ms copy-only + 0.07 ms gaps |
| P2 | Debug hook calling `grad.norm().item()` after every backward layer (12 per step) | NVTX `debug_grad_norm_hook`; 4-byte pageable D2H + `cudaStreamSynchronize` | 12 `host_sync` gaps of 0.27–0.55 ms before backward GEMMs/optimizer | 4.67 ms idle + 0.63 ms of reduce kernels |
| P3 | Launch-overhead-bound unfused optimizer: 120 small tensors × 5 elementwise ops | NVTX `optimizer_step`; 600 kernels of 2.6 µs median, grid 4 | 600 `launch_bound` gaps of ≈ 6.7 µs; phase busy 31.9 % | 4.02 ms gaps + 1.56 ms tiny-kernel time |
| P4 | Register-limited, memory-bound `layernorm_bwd_fused_kernel` (256 threads, 168 regs) | `regs_per_thread=168`, `dram_bytes=201,326,592` | 12.5 % occupancy (registers), 21.6 % of HBM roof, 5 % of kernel time | 2.43 ms vs an 80 %-of-roof kernel |
| P5 | Cross-stream dependency: before forward layer 6 a monitoring library records an event on stream 7, makes stream 13 wait on it, runs a 310 µs host callback (`cudaLaunchHostFunc`) on stream 13, and makes stream 7 wait on a second event | `cuda_api_trace.csv`: `cudaEventRecord` / `cudaStreamWaitEvent` / `cudaLaunchHostFunc` sequence; the next kernel (`layer_norm_fwd_kernel`) was submitted ≫ 10 µs before the gap | 1 `dependency` gap per step, ≈ 0.31 ms, GPU fully idle with work queued | 0.31 ms |

Distractors (should **not** be flagged as problems):

- D1 — GEMMs (18.75 % occupancy) and flash-attention kernels (6.25 % and 12.5 %) are low-occupancy *by
  design*; they run at 45–62 % of the BF16 roof. A learner who flags them has applied "occupancy is bad"
  without checking the roof.
- D2 — The pinned 64 MiB side-stream prefetch at backward start is good practice (48 GB/s, overlapped).
- D3 — The NVTX `log_loss` range lasts ≈ 17.6 ms: the CPU waiting in `loss.item()` for the forward
  pass, not slow logging. The actual GPU idle due to the loss sync is only ≈ 0.17 ms.
- D4 — The per-step `cudaDeviceSynchronize` (timing) appears only as trailing idle (≈ 0.07 ms) and is
  excluded from gaps by design; mentioning it as minor is a bonus, ranking it high is a mistake.

*Common mistakes:* double-counting overlapping intervals across streams (busy > 100 % or copy overlap
miscounted); classifying gaps by the *previous* activity instead of the next activity's submit time;
computing pageable bandwidth from the API duration instead of the GPU duration; reporting occupancy
without the limiter.

**Task 7 (`analysis.md`) marking guide (20 pts):** timeline annotated with the five phases and the sync
gaps (5); findings ranked by saving with units and labels (5); projected step time 63–65 ms with the basis stated (Table 4.5),
arithmetic, noting savings are upper bounds that interact (4); validation plan with repeated runs,
warm-up, median/IQR (3); limitations (simulated data, theoretical occupancy, single GPU) (3).

## Outline-mandated exercises

**4.11** A = B = 8,192² × 2 B = 134,217,728 B each; C the same.
- H2D: 2 × 134,217,728 = 268,435,456 B / 52 × 10⁹ B/s = **5.16 ms** (the GPU waits; the CPU does not if pinned/async).
- Kernel: 2N³ = 2 × 8,192³ = 1.0995 × 10¹² FLOP / (0.70 × 989 × 10¹²) = 1.0995 × 10¹² / 6.923 × 10¹⁴ = **1.59 ms**.
- D2H: 134,217,728 / 52 × 10⁹ = **2.58 ms**; then `cudaStreamSynchronize` returns (the CPU waits here).
- Total ≈ 9.33 ms, of which the kernel is 17 %.
(c) Training keeps weights, gradients, optimizer state and activations resident in HBM; only the input
batch (small: token IDs) crosses PCIe, prefetched from pinned memory on a side stream; results stay on
the GPU (only scalars are read, and rarely). Over PCIe, the "ridge point" would be 989 × 10¹² / 52 × 10⁹ ≈
19,000 FLOP/B, versus this GEMM's 1.0995 × 10¹² / (3 × 134.2 × 10⁶) ≈ 2,730 FLOP/B — moving its operands per
use makes it PCIe-bound.
*Diagram must show:* CPU wait only at the final sync; GPU SMs waiting on H2D; D2H waiting on the kernel.

**4.12** From the lab capture (accept equivalent evidence from a real CUDA sample):
launch overhead — optimizer kernels ids in step 41's `optimizer_step` range, 2.6 µs median vs ≈ 9.3 µs
launch interval; memory-transfer cost — the 100,663,296-B pageable copy, 8.26 ms at 12.19 GB/s;
occupancy constraint — `layernorm_bwd_fused_kernel`, 168 registers → 12 warps → 1 block → 12.5 %;
memory-bandwidth bottleneck — the same kernel at 725 GB/s = 21.6 % of 3.35 TB/s (or GELU kernels at ≈ 83–84 %
of HBM roof as an example of a *healthy* memory-bound kernel). Award full marks only with quoted values.

**4.13**
(a) 8,192 × 2,048: tiles = (8,192 / 128) × (2,048 / 256) = 64 × 8 = 512; waves = 512 / 132 = 3.88 → 4;
efficiency = 3.88 / 4 = **97 %**. 1,024 × 2,048: tiles = 8 × 8 = 64; waves = 0.48 → 1; only 64 of 132 SMs
busy, efficiency **48 %**.
(b) Row-major [8,192, 4,096] BF16: consecutive elements of a *row* are adjacent; walking dimension 0 means
adjacent threads are 4,096 × 2 B = 8,192 B apart → one 32-B sector per thread for 2 useful bytes → 64
useful bytes per 1,024 fetched = **6.25 %** efficiency. Fixes: map adjacent threads to adjacent columns;
materialize the transposed layout once (`.t().contiguous()`) if read many times; or load coalesced tiles
into shared memory and transpose there.
(c) For a linear layer with *m* tokens, weight *k* × *n*: FLOPs = 2*mkn*; bytes ≈ 2(*mk* + *kn* + *mn*) in
BF16. When *m* ≪ *k*, *n*, the weight term dominates and intensity ≈ 2*mkn* / 2*kn* = *m* FLOP/B, so halving
the batch halves intensity and pushes the GEMM toward the memory roof (Chapter 6). nvidia-smi reports a
duty cycle, which stays near 100 % whether the GEMM runs at 60 % or 15 % of peak.

## Troubleshooting case (4.14)

Ranked hypotheses:
1. **Allocator churn from the new "free memory between requests" code (`torch.cuda.empty_cache()`)** —
   evidence: 2,100 `cudaFree` calls in 10 s (one per request at ≈ 210 req/s), 420 `cudaMalloc` calls averaging
   2.7 ms, and GPU idle gaps beginning when `cudaFree` starts. `cudaFree` implicitly synchronizes the
   device, and re-growing the cache costs `cudaMalloc` calls on the next request.
2. **Genuine fragmentation causing allocation retries** — evidence would be `num_alloc_retries` > 0 in
   `torch.cuda.memory_stats()` and OOM-retry warnings before the release; discriminates from (1) by
   whether gaps persist when `empty_cache` is removed.
3. **CPU-side pauses (GC, logging, contention)** — would produce gaps not aligned with CUDA API calls;
   check with py-spy/perf on the server process and `pidstat`. Ruled out by the alignment with `cudaFree`.

Root cause: per-request `empty_cache()` → synchronizing `cudaFree` plus re-allocation on the next
request; tail latency grows because requests queued behind the freed memory wait for the device to drain
and the allocator to regrow.
Fix: remove the call; if fragmentation was the original concern, measure it (`memory_stats`) and use the
caching allocator's configuration (for example `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` — verify
availability for the deployed PyTorch version) and bucketed shapes. Roll out via canary (5 % of traffic
for one hour), compare p50/p99/p99.9 latency against the pre-release baseline at matched load; roll back
on regression.
Validation: `cudaFree` call count ≈ 0 in steady state; p99 back within 10 % of baseline across ≥ 3
one-hour windows; `num_alloc_retries` = 0.
*Marking:* 4 hypotheses/evidence, 3 root cause with mechanism (implicit sync of `cudaFree`), 3 fix and validation.

## Design challenge (4.15) — model answer outline

- **PCIe budget:** 100 MiB = 104,857,600 B per 60 ms = 1.75 GB/s per GPU ≈ 3.5 % of ≈ 50 GB/s achievable.
  On HX8 two GPUs share each PCIe switch uplink (Figure R.1): 3.5 GB/s per switch — negligible. PCIe is
  not the constraint *if* copies are pinned and overlapped.
- **Pinned memory:** reused staging pool, 3 buffers per rank (one being filled, one in flight, one in use)
  = 3 × 100 MiB = 300 MiB per rank, 2.4 GiB per node of 2 TiB. Reject "pin every tensor" (unbounded growth).
- **NUMA:** ranks 0–3 and their loader workers on socket 0 (NUMA 0), 4–7 on socket 1, with staging buffers
  allocated on the local node (`numactl --cpunodebind=N --membind=N` or framework affinity settings) so
  DMA reads do not cross the inter-socket link. Check with `nvidia-smi topo -m` CPU/NUMA affinity
  columns (Chapter 5).
- **Overlap:** side-stream `non_blocking` copy one step ahead, `wait_stream` + `record_stream`.
- **Optimizer overhead:** 1,400 tensors unfused ≈ 1,400 × several launches → thousands of launches;
  choose `fused=True` (or `foreach=True`) AdamW — low effort, full flexibility. Rejected alternative:
  whole-step CUDA Graph — larger gain potential but static-address constraints, harder debugging, and
  collectives inside graphs need care; revisit if launch gaps remain > 2 % of step.
- **Proof:** nsys capture shows copies overlapped and ≤ a handful of optimizer kernels; step-time median
  over 5 runs × 300 steps within the noise floor of the 60 ms target; DCGM SM active ≥ baseline.
*Marking:* budget arithmetic (3), pinned/NUMA (3), overhead strategy with rejected alternative (2), validation (2).

## Reflection

**4.16** `[SIMULATED]`: all trace-derived values (85.57 ms, busy fractions, gap totals, copy bandwidths,
62 %/22 % roof fractions). `[MODELED]`: occupancy, the 80 %-of-roof layernorm target, savings and the
63.2 ms projection. To make it `[MEASURED]`: apply the changes on real hardware, record a manifest
(GPU, driver, CUDA, PyTorch, clocks), capture with nsys, and measure step time over ≥ 5 runs with warm-up
discarded, reporting median and IQR.

**4.17** A 10 µs allowance mislabels genuine short dependency waits as launch-bound (and vice versa on
hosts with slower launch paths); a 2 µs threshold may drop real launch gaps on fast hosts or include
normal inter-kernel spacing on slow ones. Calibrate on a known-good trace: histogram inter-kernel gaps in a
GPU-bound region (sets the threshold above its p99) and measure submit-to-start latency on an idle stream
(sets the allowance).

**4.18** Collective communication time and its overlap with compute (Chapters 11–12), stragglers and
rank skew, network congestion (Chapter 9), and topology effects such as GPU–NIC locality (Chapters 5, 13).

**4.19** Interest correlates with novelty, not cost. In the worked example the low-occupancy kernel
(2.43 ms) is the most technically interesting; the pageable copy (8.77 ms) is 3.6× larger and a
one-line fix. Rank by modeled saving × confidence ÷ effort.
