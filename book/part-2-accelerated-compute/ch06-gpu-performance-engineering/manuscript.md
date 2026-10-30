# Chapter 6 — GPU Performance Engineering

> "It got 3 % faster" is the most expensive sentence in AI infrastructure when it is wrong. Teams ship
> kernel changes, driver upgrades and configuration tweaks on the strength of a single before/after
> number, then spend weeks chasing a regression that was really a hot chassis or a different PyTorch
> build. This chapter is about knowing what a GPU *should* achieve and proving what it *does* achieve.
> The first half gives you the ceilings: compute versus memory limits, arithmetic intensity, the
> roofline model with ORION's numbers, and utilization metrics that mean something (model FLOPs
> utilization) versus ones that mislead (nvidia-smi "GPU utilization"). The second half gives you the
> discipline: benchmark design that controls warm-up, repetitions, clocks, power, concurrency, inputs and
> software versions, and statistics — medians, IQR, bootstrap confidence intervals, effect sizes, noise
> floors — implemented without a statistics library, so you can decide whether an improvement is real
> *and* worth acting on. The lab hands you two benchmark result sets with planted traps and a set of
> kernels to place on the roofline.

## Learning objectives

After this chapter you will be able to:

1. **Calculate** arithmetic intensity for GEMMs, elementwise and memory-movement kernels and **classify**
   them as compute- or memory-bound against the correct ceiling (BF16, FP8 or FP32 SIMT).
2. **Construct** a roofline for an ORION GPU (ridge point ≈ 295 FLOP/B for dense BF16), place measured
   kernels on it, and **detect** measurements that are physically inconsistent with it.
3. **Compute** MFU and HFU for a training job and **explain** why nvidia-smi utilization is not a
   measure of SM efficiency.
4. **Design** a benchmark protocol that controls warm-up, repetitions, clocks and power state,
   concurrency, input size and software versions, and records an environment manifest.
5. **Apply** robust statistics — median, IQR, percentiles, run-level bootstrap confidence intervals,
   Cliff's delta, A/A noise floors — without scipy.
6. **Decide** whether an apparent improvement is statistically and operationally meaningful, and
   **identify** the confounders (warm-up, thermal throttling, version drift, harness differences) that
   fake one.
7. **Operate** a performance-regression gate with explicit thresholds and safe actions.

## Prerequisites and connections

[Chapter 4](../ch04-gpu-architecture-cuda-execution/manuscript.md) (execution model, occupancy, tensor
cores, profiling tools) is required; [Chapter 5](../ch05-gpu-interconnects-host-topology/manuscript.md)
supplies the interconnect ceilings that play the same role for communication that HBM plays here.
Roofline reasoning returns for LLM decode in [Chapter 15](../../part-4-distributed-ai/ch15-llm-inference-serving/manuscript.md)
and for scaling efficiency in [Chapter 11](../../part-4-distributed-ai/ch11-distributed-training-architecture/manuscript.md);
the benchmark protocol is reused for NCCL in [Chapter 12](../../part-4-distributed-ai/ch12-collective-communication-nccl/manuscript.md),
for node acceptance in [Chapter 16](../../part-5-production-operations/ch16-bare-metal-fleet-lifecycle/manuscript.md),
for safe change in [Chapter 20](../../part-5-production-operations/ch20-automation-safe-change/manuscript.md),
and end to end in [Chapter 22](../../part-5-production-operations/ch22-cross-layer-performance-engineering/manuscript.md).
The lab completes **Progressive Lab 4 (GPU baseline)** started in Chapter 4 and is the measurement
backbone of [Capstone C](../../../capstones/) (distributed training performance optimization).

## 6.1 Performance engineering as a discipline

Performance engineering is the diagnostic loop with numbers attached: *observe a symptom → collect
evidence → trace the bottleneck → identify root cause → make a safe change → validate with repeatable
measurements*. Two of those steps are where teams most often fail.

- **Tracing the bottleneck** requires a model of what the hardware can do. Without one, "this kernel
  takes 150 µs" is just a fact; with one, it is "80 % of the HBM roof — leave it alone" or "28 % of the
  compute roof — investigate". Sections 6.2–6.4 provide that model.
- **Validating with repeatable measurements** requires a protocol and statistics. Without them, a 3 %
  change is indistinguishable from the ≈ 1 % `[ILLUSTRATIVE]` run-to-run noise of a real GPU, and a thermally throttled run
  can turn an improvement into an apparent regression. Sections 6.5–6.8 provide that discipline.

> **Key idea:** A performance claim has three parts: a number, a ceiling it is compared against, and an
> uncertainty. A claim missing any of the three is an anecdote.

## 6.2 Compute limits, memory limits and arithmetic intensity

Every kernel does some amount of arithmetic, *W* (FLOP), and moves some number of bytes between the
SMs and device memory, *Q* (B). Its **arithmetic intensity** is

> *I* = *W* / *Q*   (FLOP per byte of DRAM traffic)

On a GPU with peak compute *P* (FLOP/s) and memory bandwidth *B* (B/s), the kernel cannot run faster than
either limit:

> *t* ≥ max(*W*/*P*, *Q*/*B*)   ⇔   achieved FLOP/s ≤ min(*P*, *I* × *B*)

ORION's GPUs have *P* ≈ 989 × 10¹² FLOP/s dense BF16 and *B* ≈ 3.35 × 10¹² B/s `[VENDOR-SPEC, 2026-10]`.
Four kernel families cover most of what an AI cluster runs:

**Square GEMM** (*M* = *N* = *K* = 8,192, BF16). *W* = 2*MNK* = 2 × 8,192³ = 1.0995 × 10¹² FLOP. Minimum
traffic reads *A* and *B* and writes *C* once: *Q* = 3 × 8,192² × 2 B = 402.7 × 10⁶ B. *I* = 1.0995 × 10¹² /
4.027 × 10⁸ = **2,731 FLOP/B** — compute-bound by a wide margin.

**Skinny GEMM** (decode: *M* = 16 tokens, *N* = *K* = 8,192). *W* = 2 × 16 × 8,192² = 2.147 × 10⁹ FLOP.
Traffic is dominated by the weight matrix: 8,192² × 2 B = 134.2 × 10⁶ B (activations add 0.5 × 10⁶ B).
*I* ≈ 2.147 × 10⁹ / 1.347 × 10⁸ = **15.9 FLOP/B** — memory-bound. In general for a linear layer with *m*
tokens and weights much larger than activations, *I* ≈ *m* FLOP/B in BF16: the batch size *is* the
arithmetic intensity. This one relation explains why LLM decode is memory-bound and why batching
requests raises throughput (Chapter 15).

**Elementwise and normalization** kernels (LayerNorm, GELU, residual adds): a few FLOPs per element,
2–6 bytes of traffic per element `[ILLUSTRATIVE]`. *I* ≈ 0.3–2 FLOP/B `[MODELED]` — always memory-bound; their target is a fraction of
HBM bandwidth, never of FLOP/s.

**Pure movement** (embedding gather, copies, all-to-all packing): *W* ≈ 0, *I* ≈ 0. Judge them only by
bytes per second.

Two cautions. First, *Q* is **DRAM** traffic, not bytes requested by the program: caches can make *Q*
smaller than the data touched (good kernels reuse tiles through shared memory and L2), and poor access
patterns can make it larger (uncoalesced loads fetch whole sectors; Chapter 4). Measure *Q* with
counters (`dram__bytes_read.sum` and `dram__bytes_write.sum` in Nsight Compute) when it matters, rather
than computing it from tensor shapes. Second, *P* depends on the instruction mix: tensor-core BF16 and FP8,
TF32, and plain FP32 on the CUDA cores have different peaks.

## 6.3 The roofline model on ORION

Williams, Waterman and Patterson's roofline model (2009) plots attainable performance against
arithmetic intensity on log–log axes: a sloped line *I* × *B* (the memory roof) meets a horizontal line
*P* (the compute roof) at the **ridge point**

> *I*\* = *P* / *B* = 989 × 10¹² / 3.35 × 10¹² = **295 FLOP/B** (dense BF16 on ORION) `[MODELED from VENDOR-SPEC]`.

Kernels left of the ridge are memory-bound; right of it, compute-bound. Each precision has its own roof
and therefore its own ridge:

*Table 6.1 — ORION GPU ceilings and ridge points (`[VENDOR-SPEC, 2026-10]` peaks, dense; ridges `[MODELED]`).*

| Ceiling | Peak *P* | Ridge *I*\* = *P* / 3.35 TB/s | Typical kernels |
|---|---|---|---|
| BF16/FP16 tensor (dense) | 989 TFLOP/s | 295 FLOP/B | Training GEMMs, attention |
| FP8 tensor (dense) | 1,979 TFLOP/s | 591 FLOP/B | FP8 training/inference GEMMs |
| FP32 non-tensor (CUDA cores) | ≈ 67 TFLOP/s | 20 FLOP/B | Custom FP32 kernels, some reductions, stencils |
| HBM3 bandwidth | 3.35 TB/s | — | Every memory-bound kernel |

```text
 attainable
 TFLOP/s (log)
   1979 ┤                                   ┌──────────────── FP8 roof
        │                                ╱
    989 ┤                        ┌───────────────────────────── BF16 roof   ● GEMM 8192³ (2731, 692)
        │                     ╱  ●4096×4096×512 (372, 282)                 ● flash-attn (2048, 544)
        │                  ╱
    100 ┤               ╱
     67 ┤            ╱──────────────────────────────────────── FP32 SIMT roof  ● stencil (500, 57)
        │         ╱
     10 ┤      ╱ ● decode GEMV (15.9, 45)
        │   ╱
      1 ┤╱  ● LayerNorm (1.33, 3.6)
        └┬────────┬────────┬────────┬────────┬────────┬──────► arithmetic intensity (FLOP/B, log)
        0.1       1       10       100    295 1000    10000
                                           ridge (BF16)
```

*Figure 6.1 — Roofline for an ORION GPU with the lab's kernels (schematic; points are (intensity,
achieved TFLOP/s), `[SIMULATED]` measurements from `lab/data/kernels.csv`).*

### Reading kernels off the roofline

The lab's kernel table makes the method concrete. For each kernel: compute *I*, pick the ceiling for its
precision, classify, and express performance as a fraction of the *binding* roof (bandwidth for
memory-bound, FLOP/s for compute-bound).

*Table 6.2 — Roofline classification of the lab kernels (`[SIMULATED]` counters and times; classification `[MODELED]`).*

| Kernel | Precision | *I* (FLOP/B) | Ridge | Bound | Fraction of binding roof | Verdict |
|---|---|---|---|---|---|---|
| `gemm_bf16_8192x8192x8192` | BF16 | 2,731 | 295 | compute | 70 % | Good |
| `gemm_bf16_decode_m16` | BF16 | 15.9 | 295 | memory | 85 % of HBM | Good — batch more requests to go faster |
| `layernorm_fwd_bf16` | BF16 | 1.33 | 295 | memory | 80 % of HBM | Good |
| `flash_attn_fwd_bf16` | BF16 | 2,048 | 295 | compute | 55 % | Typical; tuning possible |
| `fp32_simt_stencil` | FP32 SIMT | 500 | 20 | compute | 85 % of FP32 | Good *against the right roof* |
| `bias_add_l2_resident` | BF16 | 0.33 | 295 | **anomaly** | 5.03 TB/s > 3.35 TB/s | Counters inconsistent with DRAM roof |
| `gemm_fp8_8192x8192x8192` | FP8 | 5,461 | 591 | compute | 60 % | Typical |
| `embedding_gather_bf16` | BF16 | 0 | 295 | memory | 50 % of HBM | Investigate access pattern |
| `gemm_bf16_4096x4096x512` | BF16 | 372 | 295 | compute | 28.5 % | Investigate: small *K*, near the ridge |

Three rows carry the chapter's warnings:

- **The FP32 stencil** achieves 5 × 10¹¹ FLOP / 8.78 ms = 57 TFLOP/s. Against the BF16 roof that is 5.8 % —
  "terrible". Against the FP32 roof it is 85 % — excellent. Using the wrong ceiling produces wrong
  priorities; the right question is whether the kernel *should* use tensor cores at all.
- **The L2-resident bias add** claims 100.7 MB moved in 20 µs = 5.03 TB/s, above the 3.35 TB/s HBM roof.
  That cannot be DRAM traffic. Either the data was resident in the 50 MB L2 from a previous kernel (so the
  "DRAM bytes" were computed from tensor sizes, not counters) or the bytes are double-counted. A point
  above the roof is not a fast kernel; it is a **measurement or model error**, and it must not enter an
  efficiency report.
- **The 4096 × 4096 × 512 GEMM** is nominally compute-bound (*I* = 372 > 295) but achieves only 28.5 %.
  Near the ridge, both limits matter at once; with a short *K* the kernel cannot amortize its prologue and
  epilogue, and tile counts may quantize badly across 132 SMs (Chapter 4's wave quantization). This is
  where a library upgrade or a different tile configuration pays.

### What the roofline does not tell you

The basic roofline assumes the kernel is long enough to reach steady state and limited by throughput.
It says nothing useful about kernels dominated by launch latency (a 3 µs kernel is launch-bound, not
memory-bound), synchronization, tail effects, or instruction-issue limits; nor about communication,
which has its own roofs (NVLink, PCIe, NIC — Chapter 5). Hierarchical rooflines add L2 and shared-memory
bandwidth ceilings; Nsight Compute draws one for a profiled kernel:

```bash
# L2 — roofline chart and speed-of-light summary for one kernel (section names are version-sensitive)
ncu --section SpeedOfLight --section SpeedOfLight_RooflineChart -k regex:gemm -c 3 -o gemm_roof python bench.py
ncu --metrics dram__bytes_read.sum,dram__bytes_write.sum,gpu__time_duration.sum -k regex:layernorm -c 5 python bench.py
```

### From classification to action

Classification is useful only because it narrows the levers. Table 6.3 is the map senior engineers carry
in their heads; the left column is decided by the roofline, the right columns by profiling.

*Table 6.3 — Optimization levers by bound (gains `[ILLUSTRATIVE]`; measure before and after).*

| Bound (and evidence) | Levers that work | Levers that do *not* work | Typical first check |
|---|---|---|---|
| Memory-bound, far below HBM roof (< 50 %) | Fix access pattern (coalescing, vectorized loads, layout); raise bytes in flight (occupancy or ILP, Chapter 4); avoid redundant passes | More FLOP/s (tensor cores, FP8 math) | Nsight Compute memory workload analysis: sectors per request, achieved occupancy |
| Memory-bound, near HBM roof (> 75 %) | Move fewer bytes: fuse adjacent kernels, lower precision of stored tensors, keep data in L2/shared memory, recompute instead of storing | Further tuning of this kernel in isolation | Is the producer/consumer kernel pair fusable? |
| Compute-bound, far below roof | Use tensor cores (precision, alignment to multiples of 8/16/64), fix tile quantization, upgrade the library, larger problem per kernel | Memory-layout tuning | Tensor-pipe utilization; wave count vs SM count |
| Compute-bound, near roof | Do less arithmetic: FP8 where accuracy allows, algorithmic changes (e.g. FlashAttention avoids materializing the attention matrix), sparsity only with real support | Kernel tuning | Is the FLOP count itself necessary? |
| Not on the roofline at all (short kernels, gaps) | Launch-overhead and synchronization fixes from Chapter 4 | Anything in this table | Timeline: kernel duration vs launch interval |

Two consequences matter for capacity planning. First, **fusion is the universal memory-bound lever**:
two kernels that each stream a 400 MB tensor through HBM at 80 % of the roof take 2 × 400 × 10⁶ /
(0.8 × 3.35 × 10¹²) = 0.30 ms; fused, the intermediate never leaves the SM and the pair costs about half.
That is why compilers (`torch.compile`, XLA) and hand-fused kernels dominate the elementwise budget of
modern training. Second, **precision changes move kernels across the ridge**: halving bytes per element
doubles intensity, so an FP8 GEMM that was borderline memory-bound in BF16 can become compute-bound, while
FP8 *math* does nothing for a kernel that remains memory-bound.

A useful habit is to compute the **time at roof** for every hot kernel — *W*/*P* or *Q*/*B*, whichever is
larger — and sum it over a training step. The ratio of that sum to the measured step time is an upper
bound on what kernel-level work can buy; the remainder is idle time, launch overhead and communication,
which the timeline methods of Chapter 4 and the collective analysis of Chapter 12 address. For the
Chapter 4 worked example, the kernels' FLOPs at the BF16 roof would take 3.257 × 10¹³ / 989 × 10¹² =
33 ms of an 85 ms step — so even perfect kernels leave most of that step's time to non-kernel causes until
the host-side problems are fixed.

## 6.4 Utilization metrics: MFU, HFU and the ones that mislead

### Model FLOPs utilization

For training, the end-to-end efficiency metric is **model FLOPs utilization (MFU)** — the FLOPs the model
mathematically requires per second, divided by the hardware's peak:

> MFU = (FLOPs per token × tokens per second) / (number of GPUs × peak FLOP/s per GPU)

For a dense transformer, forward plus backward costs ≈ 6*N* FLOPs per token for *N* parameters (2*N*
forward, 4*N* backward; attention adds a sequence-length-dependent term that is often reported
separately). ORION's reference job W-TRAIN (70 × 10⁹ parameters, 4,096 × 1,024 = 4,194,304 tokens per
step, 256 GPUs) at its modeled 17.4 s step:

> tokens/s = 4,194,304 / 17.4 s = 241,052 tokens/s
> MFU = 6 × 70 × 10⁹ × 241,052 / (256 × 989 × 10¹²) = 1.0124 × 10¹⁷ / 2.5318 × 10¹⁷ = **0.400** `[MODELED]`

**Hardware FLOPs utilization (HFU)** counts the FLOPs actually executed, including recomputation. With
full activation recomputation the forward pass runs twice, ≈ 8*N* FLOPs per token, so the same job has
HFU = 8/6 × 0.400 = **0.533**. HFU is higher but less useful for comparing systems, because recomputation
is work the model did not need. Report MFU, state the FLOP-count convention, and state the peak used.

> **Pitfall:** MFU computed against the *sparse* tensor peak (twice the dense figure on this GPU class)
> halves the result. MFU always uses the vendor **dense** peak, even when the fleet runs power-capped or at
> a sustained clock below max boost, so that numbers stay comparable across sites. If you want to show how
> much of the *achievable* peak a capped fleet reaches, report a separate, clearly named clock-adjusted
> efficiency (dense peak × sustained clock ÷ max-boost clock in the denominator) next to MFU, never instead of it.

### Device-level metrics and what they mean

*Table 6.4 — Utilization metrics compared (`[VENDOR-SPEC, 2026-10]` definitions; verify DCGM field names for your version).*

| Metric | Definition | Answers | Misleads when |
|---|---|---|---|
| nvidia-smi `utilization.gpu` ("GPU-Util") | % of the sample period during which one or more kernels was executing | "Is the GPU idle?" | Always read as efficiency — a 4-block kernel on 132 SMs reads 100 % |
| `DCGM_FI_PROF_SM_ACTIVE` | Fraction of time an SM has at least one warp resident, averaged over SMs | "Are all SMs being used?" | A resident but stalled warp counts as active |
| `DCGM_FI_PROF_SM_OCCUPANCY` | Resident warps / maximum, averaged | Latency-hiding headroom | Low values are normal for tensor-core GEMMs (Chapter 4) |
| `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE` | Fraction of cycles the tensor pipe is busy | "Are tensor cores doing the work?" | Mixed precision misconfigured → near zero |
| `DCGM_FI_PROF_DRAM_ACTIVE` | Fraction of cycles the memory interface is busy | Memory-bound phases | High for good memory-bound kernels too |
| MFU | Model FLOPs / (GPUs × peak) | "How much of the hardware does the model use?" | Wrong FLOP convention or peak |
| Step time / tokens per second | Workload throughput | The business metric | Compared across different configs or versions |

The progression senior engineers use: throughput and MFU tell you *whether* there is a problem;
SM-active, tensor-active and DRAM-active tell you *where to look*; timelines and Nsight Compute tell you
*why* (Chapter 4).

## 6.5 Clocks, power and thermal state: the hidden variables

A GPU's speed is not a constant. Under load it raises its SM clock up to its maximum boost and lowers it
when it hits a limit: the power limit (software power cap), the thermal limit (software thermal
slowdown), or a hardware protection event (hardware slowdown, which triggers a few degrees *above* the
software thermal limit, or on external signals such as a power-brake from the chassis). Current drivers
report the active limiters as **clock event reasons** (`clocks_event_reasons.*` in `nvidia-smi
--query-gpu`; the section "Clocks Event Reasons" in `nvidia-smi -q`; `DCGM_FI_DEV_CLOCKS_EVENT_REASONS`
in DCGM). Older drivers called them *clocks throttle reasons* (`clocks_throttle_reasons.*`,
`DCGM_FI_DEV_CLOCK_THROTTLE_REASONS`) `[VENDOR-SPEC, 2026-10]`.

```bash
# L2 — sample clocks, temperature, power and limiters every 100 ms during a benchmark
nvidia-smi --query-gpu=timestamp,index,clocks.sm,clocks.mem,temperature.gpu,power.draw,power.limit,clocks_event_reasons.active \
           --format=csv -lms 100 -i 0 > gpu0_telemetry.csv &
nvidia-smi -q -d PERFORMANCE,CLOCK,POWER -i 0        # current limiters, clocks, enforced power limit
```

Judge throttling against what the GPU *sustains*, not the max boost clock: under dense GEMM load ORION's
GPUs settle at ≈ 1,830 MHz `[ILLUSTRATIVE]` rather than the 1,980 MHz maximum, and brief `sw_power_cap`
events are routine. A run is suspect when its clock falls clearly below its peers' or when thermal or
hardware events affect a meaningful share of its iterations. In the lab's candidate-B data, run B4 starts
at ≈ 1,820 MHz and 70 °C, climbs to 86 °C by iteration 11 (a chassis slot with poor airflow), and from
iteration 12 reports `sw_thermal_slowdown` with a median SM clock of 1,443 MHz, 21 % below the peer median of
1,826 MHz, and latency up by ≈ 1,826/1,443 = 1.27×. Its median (4.93 ms) is 27 % above the other B runs
(≈ 3.89 ms). Nothing about the kernel changed.

Two operational choices follow:

- **Lock or record clocks.** For microbenchmarks comparing *code* variants, lock the GPU clock so that
  both arms run at the same frequency (`nvidia-smi -lgc <min>,<max>`, reset with `nvidia-smi -rgc`;
  requires root). Lock **at or below the sustained clock** (for example 1,755–1,830 MHz on ORION
  `[ILLUSTRATIVE]`), not at max boost — a lock the GPU cannot hold under load just moves the throttling —
  and verify from telemetry that `clocks_event_reasons` stays at none for the whole run. For benchmarks that
  predict *production* behaviour, run at the production power and clock policy, record clocks and limiters
  per iteration, and exclude or stratify runs by a pre-registered rule (Section 6.7).
- **Control the thermal environment.** Run comparisons on the same GPU and node, interleave arms (A, B, A,
  B …) rather than all-A-then-all-B so that drift affects both equally, and give the GPU time to reach a
  steady temperature during warm-up.

> **Safety:** Clock locking, power-limit changes (`nvidia-smi -pl`) and persistence-mode changes are root
> operations that affect every tenant of the GPU. Use them only on benchmark nodes you own, and restore
> the fleet baseline afterwards; never change them on shared production nodes.

## 6.6 Designing a benchmark protocol

A benchmark is an experiment. The protocol states what is measured, under which conditions, how often,
and how the decision will be made — *before* the data is seen.

*Table 6.5 — Benchmark protocol checklist (the course outline's required controls, with ORION defaults `[ILLUSTRATIVE]`).*

| Control | Why it matters | Protocol rule |
|---|---|---|
| Warm-up | First iterations pay JIT compilation, cuDNN/cuBLAS autotuning, allocator growth, clock ramp-up and cold caches (the lab's first iteration is 1.6× slower) | Discard a fixed number of warm-up iterations decided in advance (≥ 5, more for autotuned frameworks), and verify that the discarded region covers the transient |
| Repetitions | Iterations within one process share its state (allocations, clocks, placement) and are correlated | ≥ 50 iterations per run **and** ≥ 5 independent runs (separate processes) per arm; the run is the unit of replication |
| Ordering | Thermal and background drift over time | Interleave arms (ABAB…) or randomize run order |
| Clocks and power | Frequency changes speed directly | Lock clocks at or below sustained for code comparisons, or record clocks and `clocks_event_reasons` per iteration and exclude runs whose median clock is < 95 % of the session-wide peer median (all runs of all arms) or with thermal/hardware events on > 5 % of iterations (`sw_power_cap` is routine) |
| Concurrency | Other processes, MIG/MPS neighbours, NCCL traffic, CPU frequency scaling and noisy data loaders distort timing | Dedicated GPU; check `nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv`; pin CPU threads (Chapter 5); record CPU governor |
| Input size | Performance is shape-dependent (wave quantization, cache residency, alignment) | Sweep realistic sizes; report each separately; never average across sizes |
| Software versions | Driver, CUDA, cuDNN/cuBLAS, NCCL, framework and container change kernel selection | Record all in a manifest; compare only runs with identical versions except the variable under test |
| Timing method | Host timers without synchronization measure launch time, not execution | CUDA events or synchronize before reading the host clock (Chapter 4); report what was timed |
| Noise floor | Real hardware varies by ≈ 1 % run to run `[ILLUSTRATIVE]` | Run an A/A comparison (same code twice) in the same session; changes smaller than its spread are not detectable |
| Decision rule | Post-hoc choices bias conclusions | Fix the statistic, confidence level and practical threshold before running |

```yaml
# Environment manifest for an L2 GPU benchmark (record per run) — fields, not values, are the point
benchmark: fused_attn_block_latency
workload: {batch: 8, seq_len: 4096, heads: 32, head_dim: 128, dtype: bf16}
host: {node: orion-n13, rack: rack-04, gpu_index: 0, gpu_uuid: GPU-..., bios: ..., cpu_governor: performance}
software: {driver: 570.124.06, cuda: "12.8", cudnn: ..., torch: 2.4.0, container_digest: sha256:...}
gpu_state: {persistence_mode: Enabled, power_limit_w: 700, clocks_locked: false,
            clocks_event_reasons_seen: [none], temp_range_c: [62, 71]}
protocol: {warmup_iters: 5, iters_per_run: 60, runs_per_arm: 6, order: interleaved, timer: cuda_events}
concurrency: {other_gpu_processes: 0, mig: disabled, mps: disabled}
```

## 6.7 Statistics without hand-waving

GPU latency distributions are skewed (a floor set by the hardware, a tail of interrupts, allocator
events and occasional host hiccups), and samples within a run are not independent. The statistics in this
section are chosen for those facts, and every one is implementable in a few lines of numpy.

**Location and spread.** Use the **median** rather than the mean. One 6 ms warm-up iteration among 59
steady 4 ms iterations moves the mean to (59 × 4 + 6) / 60 = 4.033 ms, +0.83 %, and the lab's five warm-up
iterations per run move it by ≈ 1.9 %; the median moves by nothing. Use the **interquartile range** (IQR = p75 − p25) for
spread and report **p95/p99** when tails matter (serving latency, collective stragglers). State the
quantile method; the lab uses linear interpolation between order statistics (numpy's default).

**The unit of replication.** Iterations within one process share its state, so 60 iterations from one run
are not 60 independent observations — treating them as such makes confidence intervals far too narrow.
Summarize each run by its median, and treat runs as the samples.

**Bootstrap confidence intervals.** The percentile bootstrap estimates the uncertainty of a statistic
without distributional assumptions: resample the data with replacement many times, recompute the
statistic each time, and take the 2.5th and 97.5th percentiles of the results as a 95 % interval. For a
comparison, resample runs independently within each arm:

```python
# L1 — percentile bootstrap of the relative change in median latency, resampling runs (numpy only)
import numpy as np
def bootstrap_ratio_ci(base_runs, cand_runs, n_boot=4000, seed=11, level=0.95):
    rng = np.random.default_rng(seed)
    reps = np.empty(n_boot)
    for i in range(n_boot):
        b = base_runs[rng.integers(0, len(base_runs), len(base_runs))]
        c = cand_runs[rng.integers(0, len(cand_runs), len(cand_runs))]
        reps[i] = np.median(c) / np.median(b) - 1.0
    a = (1 - level) / 2
    return np.median(cand_runs) / np.median(base_runs) - 1.0, np.quantile(reps, a), np.quantile(reps, 1 - a)
```

With five or six runs per arm the percentile bootstrap is **not** reliable: resampling five values can
produce only a handful of distinct medians, and at small *n* percentile intervals tend to under-cover
(a nominal 95 % interval contains the truth less often than 95 % of the time). Use it as a magnitude band,
not as the significance test. More runs make it trustworthy; more iterations per run mostly do not.

**Exact permutation test.** For the significance call at small *n*, use an exact permutation test on the
run medians. Under the null hypothesis that the change did nothing, the labels "baseline" and "candidate"
are exchangeable, so enumerate every way of splitting the pooled run medians into two groups of the
original sizes and count how often the difference in group means is at least as large as the observed one.
With 5 + 5 runs there are C(10, 5) = 252 splits; if every candidate run beats every baseline run, only the
observed split and its mirror image are as extreme, so *p* = 2/252 ≈ 0.008 — the smallest value five runs
per arm can ever produce. With 3 + 3 runs the floor is 2/20 = 0.1, so three runs per arm can never reach
*p* < 0.05 however large the effect.

```python
# L1 — exact two-sided permutation test on run medians (numpy + itertools only)
import itertools, numpy as np
def permutation_test(base_runs, cand_runs):
    pooled = np.concatenate([base_runs, cand_runs]); k = len(cand_runs)
    obs = abs(np.mean(cand_runs) - np.mean(base_runs)); hits = total = 0
    for idx in itertools.combinations(range(len(pooled)), k):
        m = np.zeros(len(pooled), bool); m[list(idx)] = True
        hits += abs(pooled[m].mean() - pooled[~m].mean()) >= obs - 1e-12; total += 1
    return hits / total
```

**How many runs? Minimum detectable effect.** Before collecting data, estimate the run-to-run standard
deviation σ_run of run medians (as a fraction of the mean) from earlier data: the A/A runs, or the cleaned
baseline runs of a previous comparison (the lab uses the sample standard deviation of the five cleaned A
run medians divided by their mean). For two arms of *n* runs,
a two-sided test at α = 0.05 with 80 % power detects changes of roughly

> MDE ≈ (1.96 + 0.84) × σ_run × √(2/*n*) = 2.8 × σ_run × √(2/*n*)

With the lab's σ_run = 0.37 %: *n* = 5 gives 2.8 × 0.37 % × √0.4 = 0.65 %; *n* = 10 gives 0.46 %; *n* = 20 gives
0.32 %. The 2.8 multiplier uses normal quantiles and is optimistic at *n* ≤ 10, where σ_run is itself
estimated from few runs: with Student-*t* quantiles for 2*n* − 2 = 8 degrees of freedom the multiplier is
≈ 2.31 + 0.89 ≈ 3.2, giving MDE ≈ 3.2 × 0.37 % × √0.4 ≈ 0.74 % at five runs per arm. If the effect you care about is close to the MDE, or close to your practical threshold, plan **at
least 10 runs per arm**; five runs are enough only for effects several times larger than σ_run.

**Effect size.** A confidence interval says whether a difference is distinguishable from zero; an
effect size says how separated the distributions are. **Cliff's delta** — *P*(*X* > *Y*) − *P*(*X* < *Y*)
over all pairs — is rank-based and robust to skew; following Romano et al. (2006), |δ| < 0.147 is
negligible, < 0.33 small, < 0.474 medium, larger is large. State the level at which you compute it:
on iterations it describes single-iteration overlap; on run medians it describes how consistently runs
differ, and the two can differ a lot. Report it alongside the relative change in medians, which is the
effect size engineers actually act on.

**Noise floor.** Run the *same* configuration as two groups (an A/A test) under the same protocol. The
largest change the A/A comparison produces (its point estimate and CI bounds) is the smallest change you
can claim to detect in that environment.

**Practical significance.** Statistical significance is not a reason to ship. Set a practical threshold
in advance — the smallest change worth the risk and effort of a change (1 % for the lab's kernel; for a
fleet-wide driver upgrade the threshold may be "no regression beyond the noise floor").

**Exclusions are part of the protocol.** Decide the exclusion rules in advance and apply them
identically to every arm, including the baseline. Clock rules compare each run with the **session-wide**
peer median (all runs of all arms in the comparison), so an arm that ran hot throughout cannot hide behind
its own low median. An exclusion rule invented after seeing which run hurts
the candidate is p-hacking, even when it sounds reasonable.

**The decision rule** used in the lab, fixed before looking at results:

| Condition | Decision |
|---|---|
| Permutation *p* < 0.05, change < 0 and \|change\| ≥ max(noise floor, threshold) | **Improvement** |
| Permutation *p* < 0.05, change > 0 and \|change\| ≥ max(noise floor, threshold) | **Regression** |
| Permutation *p* < 0.05 but \|change\| < max(noise floor, threshold) | **Real but below threshold**: do not act on it |
| Permutation *p* ≥ 0.05 | **Not significant**: not demonstrated |

> **Pitfall:** Running the comparison repeatedly until it "passes", or trying several statistics and
> reporting the best one, inflates false positives. Fix the protocol first; if you test many variants,
> say so and widen your skepticism accordingly.

## 6.8 Reproducibility: harnesses and manifests

A benchmark you cannot rerun is a rumour. The lab's harness shows the minimum structure:

1. Inputs created once from a seeded generator, so every run computes on identical data.
2. Warm-up calls timed but reported separately — so you can verify the transient was covered.
3. Each measured call timed individually, raw samples kept (summary statistics can always be recomputed;
   raw data cannot be recovered from a mean).
4. An environment manifest captured automatically at run time: host, OS, CPU architecture and count,
   interpreter and library versions, BLAS build, threading environment variables, harness version, seed
   and process id.
5. Results written as structured data (JSON) with the configuration that produced them.
6. Multiple independent runs as the unit of replication, each in a **fresh process** (the harness
   re-executes itself per run and records each run's pid), so that allocator state, JIT caches and thread
   placement are not shared between runs.

On a GPU the same harness wraps a CUDA-synchronized callable or uses CUDA events, and the manifest adds
GPU UUID, driver/CUDA/library versions, clocks, power limit, limiter history and the container digest
(Section 6.6). On a laptop the harness produces `[MEASURED]` numbers *for that laptop* — useful for
learning the discipline (expect ≈ 10–20 % `[ILLUSTRATIVE]` run-to-run variation on a laptop CPU), never as evidence
about ORION.

## 6.9 Worked example: is candidate B really faster?

**Situation.** Halcyon's Training Infra team has a new fused attention-block kernel (`fused_attn_v2`, "B")
and a tuning-flag variant of the current kernel (`fused_attn_v1_tuned`, "C"). Both claim improvements over
the baseline (`fused_attn_v1`, "A") on an ORION GPU. Engineers collected six runs per variant, 60
iterations each, and an A/A pair of six runs each (`lab/data/`, `[SIMULATED]`). The decision protocol
(Section 6.7) was fixed beforehand: warm-up 5 iterations; runs as the unit; symmetric exclusion rules
(version mismatch; throttling events on > 5 % of iterations or a median clock < 95 % of the session-wide
peer median, i.e. over all runs of both arms being compared);
exact permutation test at α = 0.05; 95 % bootstrap band for magnitude; 1 % practical threshold; reference
software driver 570.124.06 / CUDA 12.8 / PyTorch 2.4.0.

**Step 1 — The naive answer.** Mean of all rows: A = 4.0711 ms, B = 4.1133 ms, C = 3.9966 ms. B looks
**1.04 % slower**, C **1.83 % faster**. A team reading these numbers would reject B and ship C. Both
decisions would be wrong.

**Step 2 — Evidence: look at the data, not the summary.**

- *Warm-up.* Iterations 0–4 of every A and B run average 4.912 ms in A (1.2× steady state; iteration 0 is
  ≈ 1.6×). C's file has no iterations below 5: C was collected with a different harness version that
  already discarded warm-up. The naive comparison penalizes A and B for warm-up that C never reports.
- *Software versions.* Run A3 reports PyTorch 2.3.1 (an old container image); every other run reports
  2.4.0. A3's median, 3.907 ms, is ≈ 2.7 % faster than the other A runs: a different kernel selection,
  not the same experiment.
- *Clocks.* Every arm shows occasional `sw_power_cap` events (≈ 3 % of iterations): routine under heavy
  GEMMs and not a reason to exclude anything. Run B4 is different: from iteration 12 it reports
  `sw_thermal_slowdown` on 48 of 60 iterations, temperature has climbed from 70 °C to 86–89 °C, and its
  median SM clock is 1,443 MHz against a peer median of 1,826 MHz (21 % below; the peers sit at the
  ≈ 1,830 MHz sustained clock, not the 1,980 MHz max boost). Its median latency is 4.929 ms versus
  ≈ 3.89 ms for the other B runs.

**Step 3 — Clean by the protocol.** Drop iterations < 5 everywhere; exclude A3 (version) and B4
(clocks); the same rules applied to C exclude nothing. Remaining: 5 A runs, 5 B runs, 6 C runs, 55
iterations each. Per-run medians (ms):

| Arm | Run medians | Median of run medians |
|---|---|---|
| A | 4.0157, 4.0247, 4.0109, 4.0234, 3.9884 | **4.0157** |
| B | 3.8894, 3.8810, 3.9309, 3.8844, 3.8984 | **3.8894** |
| C | 3.9906, 3.9965, 3.9866, 4.0009, 3.9973, 3.9944 | **3.9955** |

**Step 4 — Noise floor and sensitivity.** The A/A comparison (same kernel, two groups of six runs) gives
−0.07 % with a 95 % bootstrap band of [−0.66 %, +0.48 %] (permutation p = 0.57). The noise floor is the
largest absolute value, **0.66 %**; the decision bar is max(0.66 %, 1 %) = 1 %. The run-to-run standard
deviation of A's run medians is 0.37 %, so with five runs per arm the MDE is
2.8 × 0.37 % × √(2/5) = **0.65 %**: changes of 1 % or more are detectable, smaller ones only marginally.

**Step 5 — Compare.**

*Table 6.6 — Decisions for candidates B and C (`[SIMULATED]` data; statistics computed by the lab solution).*

| | Naive (all rows, means) | Cleaned change in median | 95 % bootstrap band | Permutation *p* (run medians) | Cliff's δ (iterations / runs) | Decision |
|---|---|---|---|---|---|---|
| B vs A | +1.04 % (slower) | 3.8894 / 4.0157 − 1 = **−3.15 %** | [−3.49 %, −2.11 %] | 2/252 = **0.008** | −0.95 / −1.00 | **Improvement** |
| C vs A | −1.83 % (faster) | 3.9955 / 4.0157 − 1 = **−0.50 %** | [−0.82 %, +0.18 %] | **0.026** | −0.28 / −0.67 | **Real but below threshold** |

Every B run is faster than every A run, which is why the exact test reaches its smallest possible value
for 5 + 5 runs (the observed split and its mirror image out of C(10, 5) = 252). The 3.15 % change exceeds
the 1 % bar: a real, operationally meaningful improvement. The naive analysis had it backwards because one
hot run inflated B and one old-container run flattered A. C is significant by the exact test (*p* = 0.026),
though its bootstrap band still touches zero: at six runs the two methods disagree at the margin, which is
exactly why the protocol names the permutation test as the significance call. Note that the test statistic
is the difference in *means* of run medians while the reported effect is the change in *medians*; a
median-based permutation statistic is too coarse at five runs (many splits tie), and for C it gives
*p* = 0.054. C's significance is therefore marginal — one more reason not to act on it. Either way its 0.50 % change
is below the threshold, and most of the naive 1.83 % came from comparing a warm-up-free file against files
with warm-up. Report δ at both levels and say which: on iterations it describes how often single
iterations differ (−0.28, "small"); on run medians it describes how consistently runs differ (−0.67).
Neither is the business metric; the relative change is.

**Step 6 — Safe change and validation.** Ship B behind a feature flag to one training job and compare its
step time with the 7-day baseline using the same protocol (runs = independent job segments, ≥ 10 per arm
because the expected effect is near the threshold for an end-to-end metric). Keep C out. Open two follow-up
tickets: the node slot that ran B4 hot (Facilities/Fleet: inlet temperature and fan curve; see Chapter 21),
and the stale container that produced A3 (Platform: pin image digests).

**Roofline cross-check.** Is a 3 % gain plausible? The attention block is compute-bound (like
`flash_attn_fwd_bf16`, *I* ≈ 2,048 FLOP/B, 55 % of the BF16 roof). A 3.15 % reduction in time means
55 % → 55 / 0.9685 = 56.8 % of the roof, well within what a better tile schedule can deliver. A claim of
"40 % faster" for the same kernel would imply 92 % of peak and should trigger suspicion before celebration.

## 6.10 Hands-on lab overview

The lab ([lab/README.md](lab/README.md)) is **Level 1** and has three parts. **(1) Harness:** complete
`harness.py`, a reproducible microbenchmark harness that times numpy matmul (GFLOP/s) and memory-copy (GB/s)
kernels on your CPU with explicit warm-up, per-call timing, multiple runs and an automatically captured
environment manifest; run it and analyse your own laptop's run-to-run noise. **(2) Statistics and
decisions:** implement quantiles, summaries, Cliff's delta, run cleaning, the run-level bootstrap, the A/A
noise floor and the decision rule, and apply them to the supplied result sets with their planted traps.
**(3) Roofline:** classify nine supplied kernels against precision-specific ceilings, catching the
physically impossible one, and compute W-TRAIN's MFU and HFU. The deliverable is the course outline's
*reproducible benchmark harness, results table and performance conclusion*. The L2 extension runs the same
protocol on a real GPU with CUDA-event timing and full telemetry capture.

## 6.11 Troubleshooting scenario: "The driver upgrade made us 7 % slower"

**Symptom.** Fleet rolled driver 575.57.08 `[ILLUSTRATIVE version]` to a canary set of eight ORION nodes
(`orion-n25`–`n32`, the inference racks 07–08), replacing the fleet baseline 570.124.06. The nightly performance
gate reports W-TRAIN-proxy step time up 7.1 % on the canaries versus the rest of the fleet. The driver
team is asked to roll back.

**Evidence (collect before deciding).** The gate's own records show the comparison is canaries (new
driver) against non-canaries (old driver) on the same night — two variables at once: driver *and* node set.
Telemetry from the canaries during the gate:

```text
$ nvidia-smi --query-gpu=index,clocks.sm,power.draw,power.limit,clocks_event_reasons.active --format=csv -i 0   # [ILLUSTRATIVE]
index, clocks.sm [MHz], power.draw [W], power.limit [W], clocks_event_reasons.active
0, 1665 MHz, 499.12 W, 500.00 W, 0x0000000000000004
$ nvidia-smi -q -d POWER -i 0 | grep -E 'Current Power Limit|Requested Power Limit|Default Power Limit'
        Current Power Limit               : 500.00 W
        Requested Power Limit             : 500.00 W
        Default Power Limit               : 700.00 W
```

The active reason bitmask `0x…04` is the software power cap `[VENDOR-SPEC, 2026-10 — decode bitmasks with
your driver's nvidia-smi documentation]`, and `nvidia-smi -q -d PERFORMANCE` confirms "SW Power Cap :
Active". Racks 07–08 had been placed under a 500 W per-GPU cap by Facilities during a cooling
maintenance window (Chapter 21).

**Hypotheses, ranked.**

| # | Hypothesis | Discriminating test | Result |
|---|---|---|---|
| H1 | Driver regression in kernel performance | Same nodes, same power limit, old vs new driver (A/B on one node, interleaved runs) | Pending |
| H2 | Node set differs (power cap, thermals, topology) | Compare limiters, clocks, power limits between groups | **Canaries capped at 500 W** |
| H3 | Software stack drift besides the driver | Manifest diff between groups | Identical except driver |

**Discriminating experiment.** The cap is a facility safety control during maintenance; do not ask to
lift it to run a benchmark. Instead isolate the driver variable without touching the cap: on two drained,
uncapped training-partition nodes outside racks 07–08, run the gate's microbenchmark with each driver
(old driver in a second boot environment), or run both arms on one capped canary node at 500 W so that
only the driver differs. Use the full protocol: ≥ 6 interleaved runs per driver, 5 warm-up iterations
discarded, A/A floor from the same session. Result `[ILLUSTRATIVE]`: new vs old driver −0.3 %, bootstrap
band [−0.9 %, +0.4 %], permutation *p* = 0.48: not significant; noise floor 0.8 %.

**Root cause.** The regression was the power cap, not the driver. Capped GPUs ran at ≈ 1,665 MHz against
the ≈ 1,830 MHz the uncapped fleet sustains under load, a clock-bound ceiling of 1,830 / 1,665 − 1 ≈ 9.9 %
for fully compute-bound work; the observed 7.1 % fits a workload that is mostly but not entirely
clock-bound. The gate compared two node groups that differed in power policy.

**Fix and validation.** Do not roll back the driver. Change the gate so that (1) every comparison is
within the same node set or stratified by enforced power limit; (2) runs whose clock is clearly below
their peers' or that show thermal/hardware events on > 5 % of iterations are excluded or flagged; (3) the manifest records the enforced power limit. Re-run the canary gate
after the maintenance window: step-time change within the noise floor; proceed with the staged driver
rollout per Chapter 20.

> **Pitfall:** A fleet comparison is not an A/B test unless the groups differ in exactly one variable.
> "New driver nodes vs old driver nodes" is usually also "new racks vs old racks".

## Trade-offs and design decisions

*Table 6.7 — Measurement design choices.*

| Decision | Option A | Option B | Choose A when | Choose B when |
|---|---|---|---|---|
| Clock policy | Lock clocks (`-lgc`) | Production clocks, record limiters | Comparing code variants; you need low noise | Predicting production throughput; validating power/thermal policy |
| Summary statistic | Median (+ IQR, p95/p99) | Mean (+ standard deviation) | Latency, skewed data, outliers present | Throughput totals where every sample's cost adds up (e.g. tokens per hour), after outlier review |
| Replication unit | Runs (process restarts) | Iterations | Always for inference about the configuration | Only for describing within-run behaviour (tails, warm-up) |
| Significance test | Exact permutation test on run medians | Bootstrap CI or t-interval on run medians | Few runs (≤ 10 per arm), skewed data | Many runs (≥ 20 per arm); report a CI for magnitude either way |
| Benchmark scope | Microbenchmark (one kernel) | End-to-end (step time, tokens/s) | Attributing a change to a kernel; fast iteration | Deciding to ship; capturing interactions (comms, data loading) |
| Ordering | Interleaved/randomized runs | Blocked (all A, then all B) | Shared node, drift possible | Never, unless switching cost is prohibitive (then add A/A) |

## Production operations notes / runbook excerpt

**Runbook: performance-regression gate (Training Infra / Platform; runs nightly and on every candidate
driver, container or kernel change).**

*Signals and thresholds* `[ILLUSTRATIVE — calibrate with your own A/A data]`:

| Signal | Threshold | Action |
|---|---|---|
| Median step-time change vs baseline | Permutation *p* < 0.05 and change > max(A/A floor, 2 %) | Block promotion; open a regression ticket with both manifests |
| A/A noise floor | > 2 % | Gate is unreliable: investigate the environment before trusting any result |
| Runs excluded for clock event reasons | > 1 of 6 in either arm | Rerun on other nodes; ticket to Fleet/Facilities |
| Version mismatch within an arm | Any | Invalidate the comparison |
| MFU on the reference job | < 90 % of the 30-day median | Investigate (Chapter 22 cross-layer method) |

*Procedure:* (1) Confirm both arms' manifests differ only in the variable under test. (2) Check telemetry
for limiters, temperature range and other GPU processes. (3) Recompute the decision with the fixed rule;
never change the threshold after seeing the data. (4) If a regression is confirmed, bisect (one variable
at a time) on a dedicated node. (5) Record the decision, data and manifests in the change ticket.

*Safe actions:* reruns on dedicated benchmark nodes; clock locking only there; no power-limit or clock
changes on shared nodes; promotions and rollbacks through the staged change process (Chapter 20).
*Escalation:* kernel/library regressions to the framework team with Nsight Compute reports; power and
thermal anomalies to Fleet and Facilities.

## Realism boundaries

> **Realism boundary:** The lab's benchmark datasets and kernel counters are `[SIMULATED]`: generated from a
> run-level plus iteration-level noise model with planted warm-up, version, thermal and harness traps. Real
> GPU measurements add effects the generator does not: time-correlated drift, bimodal kernel selection,
> allocator events, interference from other processes, and clock behaviour that depends on workload mix. The
> CPU harness produces `[MEASURED]` numbers about *your laptop only*; laptop CPUs have turbo, thermal and
> background-process behaviour that make them noisier than a dedicated GPU node, which is useful for
> learning the statistics and useless as evidence about ORION. Roofline ceilings are vendor peaks; achievable
> ceilings are lower (typically 70–90 % of HBM bandwidth and 60–80 % of tensor peak for the best kernels
> `[ILLUSTRATIVE]`) and should be measured on your hardware before setting targets.

## Summary

- Arithmetic intensity (FLOP per DRAM byte) decides whether a kernel is compute- or memory-bound; for a
  linear layer it is roughly the number of tokens in the batch.
- ORION's dense-BF16 ridge point is 989 / 3.35 ≈ 295 FLOP/B; FP8's is ≈ 591 and FP32 SIMT's ≈ 20. Judge each
  kernel against the roof for its precision, as a fraction of its *binding* roof.
- A point above a roof is a measurement error (L2 residency, miscounted bytes), not a fast kernel.
- MFU = 6*N* × tokens/s ÷ (GPUs × dense peak); W-TRAIN at 17.4 s/step is 40 % MFU, 53 % HFU with full
  recomputation. State the convention and the peak.
- nvidia-smi GPU-Util is a duty cycle; SM-active, tensor-active and DRAM-active point to where time goes.
- Clocks move with power and thermal limits; record `clocks_event_reasons` and exclude or stratify affected runs.
- Protocols fix warm-up, repetitions, ordering, clocks, concurrency, sizes, versions, timing method and
  the decision rule before data is collected.
- Runs, not iterations, are the unit of replication; use medians, IQR and a run-level bootstrap.
- An A/A comparison sets the noise floor; a practical threshold separates "real" from "worth acting on".
- At five or six runs per arm, make the significance call with an exact permutation test, use the
  bootstrap only as a magnitude band, and size experiments with MDE ≈ 2.8 σ_run √(2/n).
- In the worked example the naive analysis reversed one decision (B) and invented another (C); cleaning by
  a pre-registered, symmetric protocol found a 3.15 % improvement (p = 0.008) and a 0.50 % non-actionable change.

## Review questions

Full exercise set: [exercises.md](exercises.md). Quick self-check:

1. A kernel reads 64 MB, writes 64 MB and performs 2 × 10⁹ FLOP in BF16 in 50 µs on an ORION GPU. Is it
   compute- or memory-bound, and what fraction of its binding roof does it reach?
2. Why is a 95 % CI computed from 300 iterations of a single run misleading?
3. Two variants differ by 0.6 % with a CI of [−0.9 %, −0.3 %]; the A/A floor is 1.0 %. What do you decide?

*(Answers: 1 — I = 2 × 10⁹ / 1.28 × 10⁸ = 15.6 FLOP/B < 295 → memory-bound; 1.28 × 10⁸ B / 50 µs = 2.56 TB/s =
76 % of HBM. 2 — iterations within a run are correlated and share one process's state, so the CI ignores
run-to-run variation and is far too narrow. 3 — real but below the noise floor/threshold: do not act on it.)*

## Further reading

- S. Williams, A. Waterman and D. Patterson, "Roofline: An Insightful Visual Performance Model for Multicore
  Architectures," *Communications of the ACM* 52(4), 2009 — the original model and how to read it.
- NVIDIA, *Nsight Compute Kernel Profiling Guide* — speed-of-light metrics, roofline charts and the DRAM
  byte counters used to measure arithmetic intensity correctly.
- A. Chowdhery et al., "PaLM: Scaling Language Modeling with Pathways," 2022 (appendix on MFU) — the
  widely used definition of model FLOPs utilization.
- V. Korthikanti et al., "Reducing Activation Recomputation in Large Transformer Models," 2022 — FLOP
  accounting with recomputation, the basis of HFU.
- B. Efron and R. Tibshirani, *An Introduction to the Bootstrap* (Chapman & Hall, 1993) — the bootstrap
  methods used in Section 6.7.
- A. Georges, D. Buytaert and L. Eeckhout, "Statistically Rigorous Java Performance Evaluation," OOPSLA
  2007 — why single-run comparisons mislead and how to replicate properly.
- T. Kalibera and R. Jones, "Rigorous Benchmarking in Reasonable Time," ISMM 2013 — choosing how many runs
  and iterations, with multi-level variation.
- T. Mytkowicz et al., "Producing Wrong Data Without Doing Anything Obviously Wrong!", ASPLOS 2009 —
  measurement bias from environment details, the reason manifests exist.
- T. Hoefler and R. Belli, "Scientific Benchmarking of Parallel Computing Systems," SC 2015 — twelve rules
  for reporting HPC performance, directly applicable to GPU clusters.
- J. Romano, J. Kromrey, J. Coraggio and J. Skowronek, "Appropriate Statistics for Ordinal Level Data:
  Should We Really Be Using t-test and Cohen's d for Evaluating Group Differences on the NSSE and Other
  Surveys?", Florida Association of Institutional Research annual meeting, 2006 — the source of the
  Cliff's delta thresholds used in Section 6.7.
- P. Good, *Permutation, Parametric, and Bootstrap Tests of Hypotheses*, 3rd ed. (Springer, 2005) — exact
  permutation tests and when bootstrap intervals are unreliable at small sample sizes.
