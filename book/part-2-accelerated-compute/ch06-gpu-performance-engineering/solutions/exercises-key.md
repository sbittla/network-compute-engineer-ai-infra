# Chapter 6 — Answer Key (INSTRUCTOR ONLY)

Ceilings from Table 6.1. Every number computed by hand and re-checked with numpy; bootstrap results from
`solutions/lab/analysis.py` (seed 11, 4,000 replicates); permutation tests are exact enumerations.
Deduct for missing units, labels or arithmetic. Point values are given per item (106 points in total
for 6.1–6.9 and 6.11–6.20); the lab (6.10) is graded on its own 100-point rubric.

---

## Knowledge checks

**6.1** *I* = FLOP / DRAM bytes; ridge *I*\* = *P* / *B*. BF16: 989 × 10¹² / 3.35 × 10¹² = **295 FLOP/B**;
FP8: 1,979 / 3.35 = **591 FLOP/B**; FP32 SIMT: 67 / 3.35 = **20 FLOP/B**. *(3 pts: 1 definitions, 2 values.)*

**6.2** Elementwise: a few FLOPs per 2–6 bytes → *I* ≈ 0.3–2 ≪ 295; time is set by bytes, so GB/s vs
3.35 TB/s is the meaningful figure. Large GEMM: *I* in the thousands ≫ 295; time set by FLOPs. *(2 pts.)*

**6.3** (1) Data resident in the 50 MB L2 (or served from shared memory), so traffic did not reach DRAM —
check `dram__bytes_read.sum`/`dram__bytes_write.sum` and `lts__t_bytes` (L2) in Nsight Compute, or rerun
with an input larger than L2. (2) Bytes computed from tensor shapes double-count or assume a layout not
used — compare computed bytes with the DRAM counters. Either way the value exceeds the 3.35 TB/s roof and
cannot be DRAM bandwidth. *(3 pts: 1 per mechanism, 1 for the check.)*

**6.4** MFU = 6*N* × tokens/s / (GPUs × peak); HFU counts executed FLOPs including recomputation
(≈ 8*N* per token with full recomputation). HFU > MFU because recomputed forward passes are work the model
does not require. Report MFU (with convention and the vendor dense peak) for cross-system comparison. *(3 pts.)*

**6.5** Any five, e.g.: warm-up (discard fixed iterations); clocks/thermal/power (lock clocks or record
`clocks_event_reasons` and exclude); other processes (dedicated GPU, check compute apps); software
versions (manifest, pin container digest); time drift (interleave arms); input-size effects (fixed sizes
per comparison); CPU frequency/affinity (governor, pinning); timing method (CUDA events). *(5 pts: 1 per pair.)*

**6.6** Iterations within one process share allocations, clocks, kernel selection, placement and
thermal state; they are positively correlated. A CI from 300 iterations reflects within-run noise only,
ignores run-to-run variation (often the larger component), and is far too narrow → false positives. *(3 pts.)*

**6.7** Active reasons the GPU is running below maximum clocks (power cap, software thermal slowdown,
hardware slowdown, idle, application-clock setting, sync boost, etc.). Older drivers: "Clocks Throttle
Reasons", `clocks_throttle_reasons.*`, DCGM `DCGM_FI_DEV_CLOCK_THROTTLE_REASONS` (now
`DCGM_FI_DEV_CLOCKS_EVENT_REASONS`). Software thermal slowdown engages at the GPU's maximum operating
temperature; hardware slowdown triggers a few °C higher (or on external power-brake signals) and is a
protection mechanism — seeing HW slowdown without SW slowdown at moderate temperatures points to power
delivery or chassis signals, not heat. Throttling should be judged against peers' sustained clock (≈ 1,830 MHz on
ORION), not the 1,980 MHz max boost; `sw_power_cap` events are routine. *(4 pts; deduct 2 if HW slowdown is said to
engage before SW thermal slowdown.)*

## Worked problems

**6.8**
(a) *W* = 2 × 4,096³ = 1.374 × 10¹¹ FLOP; *Q* = 3 × 4,096² × 2 = 1.007 × 10⁸ B; *I* = **1,365 FLOP/B** →
compute-bound; time at roof = 1.374 × 10¹¹ / 989 × 10¹² = **139 µs**.
(b) *W* = 2 × 64 × 4,096² = 2.147 × 10⁹; *Q* = 2 × (64 × 4,096 + 4,096² + 64 × 4,096) = 2 × 17,301,504 =
3.460 × 10⁷ B; *I* = **62.1 FLOP/B** → memory-bound; time at roof = 3.460 × 10⁷ / 3.35 × 10¹² = **10.3 µs**;
attainable = 62.1 × 3.35 = 208 TFLOP/s = 21 % of peak.
(c) *I*(*M*) = 2 × *M* × 4,096² / [2 × 4,096 × (2*M* + 4,096)] = 4,096*M* / (2*M* + 4,096). Set = 295.2:
4,096*M* = 590.4*M* + 1,209,139 → *M* = 1,209,139 / 3,505.6 = **345 tokens** (≈ the "I ≈ M" rule, corrected for
activation traffic). All `[MODELED]`. *(10 pts: 4 / 3 / 3.)*

**6.9** tokens/s = 512 × 4,096 / 5.2 = 2,097,152 / 5.2 = 403,298.
(a) MFU = 6 × 13 × 10⁹ × 403,298 / (64 × 989 × 10¹²) = 3.146 × 10¹⁶ / 6.330 × 10¹⁶ = **0.497**.
(b) HFU = 8/6 × 0.497 = **0.663**.
(c) With 1,979 × 10¹² (FP8 peak) by mistake: **0.248** — the same job looks half as efficient.
(d) 98 % GPU-Util says kernels were running 98 % of the time; it says nothing about efficiency — MFU does.
*(8 pts: 2 each.)*

## Hands-on lab (6.10) — expected results and planted anomalies

Reference output `[SIMULATED]`:

| | Naive | Cleaned change | 95 % bootstrap band | Permutation *p* | Cliff's δ (iter / runs) | Runs used | Decision |
|---|---|---|---|---|---|---|---|
| A/A floor | — | −0.07 % | [−0.66 %, +0.48 %] | 0.57 | — | 6/6 | floor = **0.66 %**; bar = max(0.66 %, 1 %) = 1 % |
| B vs A | +1.04 % | **−3.15 %** | [−3.49 %, −2.11 %] | **2/252 = 0.008** | −0.95 / −1.00 | 5/5 | **improvement** |
| C vs A | −1.83 % | **−0.50 %** | [−0.82 %, +0.18 %] | **0.026** | −0.28 / −0.67 | 5/6 | **below_threshold** |

σ_run (sample SD of the 5 cleaned A run medians / mean) = 0.37 % → MDE at 5 runs per arm = 0.65 % (normal
quantiles) or ≈ 0.74 % (t, 8 df, multiplier ≈ 3.2); at 10 runs = 0.46 % (z; ≈ 0.49 % with t at 18 df). C's significance is marginal: the
median-based permutation statistic gives p = 0.054.

Roofline: compute — GEMM 8192³ (70 %), flash-attn (55 %), FP32 stencil (85 % of FP32 roof), FP8 GEMM
(60 %), GEMM 4096×4096×512 (28.5 %); memory — decode GEMM (85 %), LayerNorm (80 %), embedding gather
(50 %); anomaly — `bias_add_l2_resident` (5.03 TB/s). W-TRAIN MFU 40.0 %, HFU 53.3 %.

### Lab 6 — planted anomalies (do not distribute)

| # | Trap | Where | What a careless analysis does | Correct handling |
|---|---|---|---|---|
| T1 | Warm-up iterations (first 5 per run; iteration 0 ≈ 1.6×) | A, B, AA files | Means inflated ≈ 1.9 % | Drop `iter < 5` |
| T2 | Harness difference: C's file already omits warm-up (iterations start at 5) | `bench_candidate_c.csv` | C appears 1.83 % faster than A | Notice the missing iterations; compare cleaned data only |
| T3 | Version drift: run A3 used PyTorch 2.3.1 (≈ 2.7 % faster kernel selection) | `bench_baseline.csv` | Baseline looks faster, hiding B's gain | Exclude A3 (version) |
| T4 | Thermal throttling: run B4 climbs 70 → 86 °C, then `sw_thermal_slowdown` on 48/60 iterations, median clock 1,443 MHz vs peer median 1,826 MHz (−21 %), +27 % latency | `bench_candidate_b.csv` | B looks slower (naive +1.04 %) | Exclude B4 (clocks); ticket the chassis slot |
| T4b | Routine `sw_power_cap` events on ≈ 3 % of iterations in every arm | all files | Excludes runs for a routine event, or judges clocks against the 1,980 MHz max boost | Keep: below the 5 % event-share rule and clocks match peers |
| T5 | Occasional host hiccups (≈ 2 % of iterations, +0–15 %) | all files | Treated as a signal or trimmed ad hoc | Keep; medians are robust; they are real behaviour |
| T6 | FP32 SIMT kernel judged against the BF16 roof | `kernels.csv` | "5.8 % — terrible" | Use the FP32 ceiling: 85 % |
| T7 | L2-resident kernel with shape-derived bytes (5.03 TB/s) | `kernels.csv` | "Fastest kernel" | Flag as anomaly; measure DRAM bytes |
| T8 | Near-ridge GEMM with small *K* at 28.5 % | `kernels.csv` | Ignored because "compute-bound GEMMs are fine" | Investigate tiles/wave quantization/library |

*Common mistakes:* bootstrapping iterations instead of runs; judging throttling against max boost;
applying an exclusion rule to one arm only; excluding B4 iterations individually but
keeping its clean warm-up-adjacent rows (the protocol excludes the run); treating C's "below_threshold" as
"no effect" (it is a small real effect not worth acting on); using p-values from a t-test on iterations.

**Report marking (30 pts):** protocol complete (8), labelled results tables with manifest (6), decision
table with justified exclusions (6), roofline actions (4), conclusion and limitations (6).

## Outline-mandated exercises

**6.11**

| Kernel | *I* (FLOP/B) | Ridge | Bound | Achieved | Fraction of binding roof |
|---|---|---|---|---|---|
| K1 | 1.0 × 10⁹ / 1.6 × 10⁹ = 0.625 | 295 | memory | 1.6 × 10⁹ / 0.60 ms = 2.67 TB/s | **79.6 %** of HBM |
| K2 | 4.4 × 10¹² / 0.6 × 10⁹ = 7,333 | 295 | compute | 4.4 × 10¹² / 7.4 ms = 595 TFLOP/s | **60.1 %** |
| K3 | 8.6 × 10⁹ / 2.15 × 10⁹ = 4.0 | 295 | memory | 2.15 × 10⁹ / 0.75 ms = 2.87 TB/s | **85.6 %** |
| K4 | 2.0 × 10¹¹ / 0.4 × 10⁹ = 500 | 20 (FP32) | compute | 2.0 × 10¹¹ / 5.0 ms = 40 TFLOP/s | **59.7 %** of FP32 |

*(10 pts: 1.5 per row, 4 for the ranking with levers.)*

Ranking by opportunity: K4 (59.7 % of a roof that is itself 15× below tensor peak — can it use TF32/BF16
tensor cores?), K2 (60 %: tile config/library, FP8 if accuracy allows), K1 (near roof — fuse with neighbours
to avoid the pass), K3 (near roof — only fewer bytes help: KV-cache precision, batching). Accept other
orderings with a defensible "time saved × feasibility" argument; require the right lever per bound.

**6.12** Must include: identical nodes and topology (mapping CSV golden, Chapter 5), dedicated nodes,
`all_reduce_perf` sizes swept (e.g. 8 B–8 GiB, factor 2), `-w` warm-up iterations and `-n` measured
iterations stated, ≥ 6 separate launches per NCCL version interleaved (build both, alternate), fixed NCCL
environment except the version, clocks/limiters and NIC counters recorded, A/A floor (same version
twice), statistic = median busbw per size per launch, bootstrap CI over launches, practical threshold
(e.g. 2 %), manifest (NCCL version, driver, CUDA, NIC firmware, OFED/DOCA, topology, env vars, sizes,
iteration counts). *Marking (10 pts):* 1 pt each for warm-up, repetitions/launches, interleaving, concurrency
control, input sizes, version control and noise floor (7), decision rule (2), manifest (1).

**6.13** Medians: baseline sorted 12.37, 12.39, 12.41, 12.44, 12.47, 12.52 → (12.41 + 12.44)/2 = **12.425**.
Candidate all six: 12.05, 12.10, 12.12, 12.22, 12.31, 12.95 → **12.17** → 12.17/12.425 − 1 = **−2.05 %**;
bootstrap band [−2.97 %, +1.65 %]; exact permutation *p* (6 + 6, C(12, 6) = 924 splits) = **0.36** → *not
significant*. Without run 5: 12.05, 12.10, 12.12, 12.22, 12.31 → **12.12** → **−2.45 %**; band
[−3.16 %, −0.85 %]; *p* (6 + 5, C(11, 5) = 462 splits) = 1/462 = **0.002**; |−2.45 %| ≥ max(0.9 %, 2 %) →
**improvement**. The second decision stands *only if* the exclusion rule (for example "throttling or
power-cap events on > 5 % of iterations, or clock < 95 % of peers") was part of the pre-registered
protocol and is applied to both arms (check the baseline's telemetry too); excluding a run only because it
hurts the candidate is p-hacking. Note also that `sw_power_cap` is often routine; check whether the fifth
run's clock was actually below its peers. Recommend rerunning it, and with an effect this close to the 2 %
threshold, collecting ≥ 10 runs per arm. *(10 pts: medians 2, changes 2, tests 3, decisions and justification 3.)*

## Troubleshooting case (6.14)

Mechanisms: (1) **Amdahl** — 12 % of 4 % = 0.48 % of step time, below the ≈ 1 % noise floor; (2)
**shape mismatch** — batch 1 microbenchmark is launch-/L2-dominated (input 8 KB fits in L2) while production
GELU streams ~hundreds of MB from HBM; the speed-up may vanish at production shapes; (3) **fusion in
production** — `torch.compile` may already fuse GELU into the preceding GEMM epilogue, so the standalone
kernel is never called; (4) **one-process measurement** — 1,000 iterations in one run say nothing about
run-to-run variation; (5) clocks/thermal differences between the microbenchmark host and production.
Expected gain: if the kernel's time drops by 12 %, the step drops by 0.04 × 0.12 = **0.48 %** (if "12 % faster"
means 1.12× throughput, the time drops by 1 − 1/1.12 = 10.7 % and the step by 0.43 %). Experiment: profile production to get the share and the actual shapes; benchmark
at production shapes on an ORION GPU with the full protocol (≥ 5 runs, warm-up, A/A); predict the
end-to-end change with Amdahl and compare against the noise floor before deploying. *(10 pts: mechanisms 4,
Amdahl 3, experiment 3.)*

## Design challenge (6.15) — model answer outline

Budget: 16 GPU-hours = e.g. two dedicated nodes × 8 GPUs × 1 h. Workloads: (i) microbenchmark suite
(GEMM BF16/FP8 at 3 shapes, LayerNorm, attention) on 2 GPUs per node — 20 min; (ii) single-node
`all_reduce_perf` 8 GPUs — 10 min; (iii) end-to-end W-TRAIN-proxy on one node (TP = 8), 6 × 3-minute runs —
30 min. Node selection: rotate through nodes nightly but compare each night against the *same node's*
history (stratify by node), plus a fixed reference node for cross-night drift. Clock policy: production
clocks with telemetry; exclude runs with limiters; separate weekly locked-clock code benchmarks. Samples:
≥ 6 runs per arm, interleaved, each a fresh process; A/A pair each night (budgeted inside (iii)). Decision:
block promotion if the exact permutation test gives p < 0.05 and regression > max(A/A floor, 2 %); warn between floor and 2 %. Keeping floor < 1 %:
dedicated nodes, persistence mode, warm-up ≥ 10 iterations, pinned containers, interleaving. Rejected
alternative: running the gate on whichever production nodes are free — cheaper but confounds node, power
and tenant variation (the Section 6.11 failure). *Marking:* budget arithmetic (2), stratification (2),
decision rule (2), floor control (2), rejected alternative (2).

## Reflection

**6.16** CPU frequency scaling/turbo and thermal state, background processes, BLAS threading variables
(`OMP_NUM_THREADS` etc.), power mode (battery vs AC), and memory pressure. The supplied GPU analysis is
about a different system and uses its own A/A floor; the laptop noise only shows why the protocol matters.
*(3 pts.)*

**6.17** Cliff's δ measures how often one distribution's samples exceed the other's, and its value depends
on the level at which it is computed. For C, on iterations δ = −0.28 ("small": single iterations overlap
heavily); on run medians δ = −20/30 = −0.67 ("large": of the 6 × 5 = 30 run pairs, 25 favour C and 5 favour A) — yet the change is only
0.50 %. Tight run-level distributions make even a tiny shift look "large". Effect sizes describe separation,
not practical value: state the level, and pair δ with the relative change and a practical threshold. *(3 pts.)*

**6.18** Sustained clocks and achievable FLOP/s drop; step times, kernel times, and fractions of the
compute roof change; noise floors may change. MFU still uses the vendor dense peak (989 TFLOP/s), so MFU
falls; if you want to show efficiency against what the capped GPU can achieve, report a separate,
clearly named clock-adjusted efficiency alongside MFU, never instead of it. Re-baseline: new A/A
floor, new reference runs per node under the cap, manifests recording the enforced limit. *(3 pts.)*

**6.19** For serving SLOs: use tail percentiles (p95/p99 TTFT/TPOT) as the statistic, under realistic
concurrency and arrival processes, with longer runs to estimate tails — medians of isolated kernel runs
miss queueing effects (Chapter 15). *(3 pts.)*

**6.20** If A3 is kept (no version rule) and nothing else changes, C vs A becomes −0.44 % with a bootstrap
band of [−0.77 %, +1.19 %] and permutation *p* = 0.99: the "small real effect" disappears because a
2.7 %-fast baseline run sits among A's runs. Which answer is right depends on a rule decided *before* the
data were seen — and applied to every arm. Excluding A3 because it is a different experiment (wrong
container) is legitimate; excluding it because it makes C look worse would not be. Pre-registration plus
symmetric application is what makes the exclusions defensible. *(3 pts.)*
