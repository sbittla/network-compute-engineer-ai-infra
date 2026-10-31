# 6.10 — Lab 6: benchmark harness and statistics (reference results)

Graded with the Lab 6 rubric (lab README Section 7, 100 points); the checks listed in `meta.yaml` must PASS in
`solutions/lab/outputs/check_solution.txt`. Reference implementation: `solutions/lab/harness.py` and
`solutions/lab/analysis.py`. Relies on manuscript Sections 6.3–6.9.

## Decisions `[SIMULATED]` data, reference analysis

| | Naive | Cleaned change | 95 % bootstrap band | Permutation *p* | Cliff's δ (iter / runs) | Runs used | Decision |
|---|---|---|---|---|---|---|---|
| A/A floor | — | −0.07 % | [−0.66 %, +0.48 %] | 0.57 | — | 6/6 | floor = **0.66 %**; bar = max(0.66 %, 1 %) = 1 % |
| B vs A | +1.04 % | **−3.15 %** | [−3.49 %, −2.11 %] | **2/252 = 0.008** | −0.95 / −1.00 | 5/5 | **improvement** |
| C vs A | −1.83 % | **−0.50 %** | [−0.82 %, +0.18 %] | **0.026** | −0.28 / −0.67 | 5/6 | **below_threshold** |

Exclusions (rules applied identically to every arm): **A3** (version: PyTorch 2.3.1 vs 2.4.0); **B4** (clocks:
`sw_thermal_slowdown` on 48 of 60 iterations, median 1,443 MHz vs 1,826 MHz session peer median, −21 %, 70 → 86 °C).
Routine `sw_power_cap` events (≈ 3 % of iterations in every arm) are kept. C's file omits warm-up (iterations
start at 5), which is why its naive comparison looks 1.83 % faster.

σ_run (5 cleaned A run medians) = 0.37 % → MDE at 5 runs per arm ≈ 0.65 % (normal quantiles) or ≈ 0.74 % (t, 8 df);
at 10 runs ≈ 0.46 %. C's significance is marginal (median-based permutation statistic gives p = 0.054).

## Roofline and MFU `[MODELED]`

Compute-bound: GEMM 8192³ (70 %), flash-attention (55 %), FP32 stencil (85 % of the FP32 roof, not 5.8 % of BF16),
FP8 GEMM (60 %), GEMM 4096×4096×512 (28.5 %: investigate tiles, wave quantization, library). Memory-bound:
decode GEMM (85 %), LayerNorm (80 %), embedding gather (50 %). Anomaly: `bias_add_l2_resident` at 5.03 TB/s
(> 3.35 TB/s roof: L2-resident, measure DRAM bytes). W-TRAIN MFU **40.0 %**, HFU with full recomputation **53.3 %**.

## Report marking (Task 6, 30 points)

Protocol complete with all ten Table 6.5 controls (8); labelled results tables with manifest (6); decision
table with justified exclusions quoting rows (6); roofline actions (4); conclusion a manager can act on (ship B;
do not ship C for performance alone) and limitations, including what would make it `[MEASURED]` on ORION (6).

**Common mistakes.** Bootstrapping iterations instead of runs; judging throttling against max boost;
applying an exclusion rule to one arm only; excluding B4's throttled iterations but keeping the run; reading
C's "below_threshold" as "no effect" (small real effect, not worth acting on); t-tests on iterations.
