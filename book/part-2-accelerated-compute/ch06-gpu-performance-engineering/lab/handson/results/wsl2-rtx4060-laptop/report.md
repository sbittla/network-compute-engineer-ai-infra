# Ch 6 hands-on: benchmark it properly — `wsl2-rtx4060-laptop`

Every number is `[MEASURED]` on the machine in `environment.json` unless labelled otherwise; the step is named.

## Step 1 — four ways to time one BF16 GEMM (n = 4096)

| Method | Time (ms) | Implied TFLOP/s |
|---|---|---|
| A: host timer, no synchronize | 0.027 | 5170.3 |
| B: one cold call, synchronized | 141.094 | 1.0 |
| C: mean of 20 incl. the first | 12.041 | 11.4 |
| D: CUDA events, warm-up dropped, median of 50 | 4.823 | 28.5 |

All `[MEASURED, step 1]`. Vendor-class BF16 dense peak at the 3105 MHz maximum clock: 38.2 TFLOP/s `[MODELED]`.

## Step 2 — warm-up

First iteration / steady median, median over 32 runs: **7.07×** (max 8.79×) `[MEASURED, step 2]`.

## Steps 3–4 — the protocol: arms, clocks, A/A floor

| Arm | What | Runs (kept) | Mean of run medians (ms) | Median IQR within a run (ms) | SM clock (MHz) | Max temp (°C) | sw_power_cap share |
|---|---|---|---|---|---|---|---|
| base | AdamW foreach (baseline) | 8 (8) | 44.246 | 0.300 | 2456 | 71 | 90 % |
| aa | A/A: identical to baseline | 8 (8) | 44.258 | 0.234 | 2460 | 71 | 89 % |
| fused | AdamW fused | 8 (8) | 39.187 | 0.412 | 2426 | 72 | 91 % |
| zero | zero_grad(set_to_none=False) | 8 (8) | 45.781 | 0.279 | 2464 | 71 | 90 % |

Excluded runs (pre-registered clock rule): 0  `[MEASURED, step 4]`.

A/A (base vs aa): +0.03 %, band [-0.18 %, +0.24 %], p = 0.812: noise floor **0.24 %** `[MEASURED, step 4]`. σ_run = 0.23 %; MDE ≈ 0.32 % at 8 runs per arm, 0.29 % at 10 `[MODELED from MEASURED σ_run]`.

## Step 5 — decisions (one statistic: difference in arm means of run medians, % of baseline)

| Candidate vs base | Change | 95 % bootstrap band | Exact permutation p (floor) | Cliff's δ (runs) | Bar = max(floor, threshold) | Decision |
|---|---|---|---|---|---|---|
| AdamW fused | -11.43 % | [-11.63 %, -11.23 %] | 0.0002 (0.0002) | -1.00 | 1.00 % | **improvement** |
| zero_grad(set_to_none=False) | +3.47 % | [+3.27 %, +3.66 %] | 0.0002 (0.0002) | +1.00 | 1.00 % | **regression** |

With only the first three runs per arm, the fused comparison gives -11.40 % and p = 0.100: the floor for 3 + 3 runs is 0.10, so three runs can never reach p < 0.05 `[MEASURED, step 5]`.

## Step 6 — empirical roofline

- Copy (256 MiB, read + write): **226 GB/s** against a 256 GB/s bus-width × data-rate spec `[MEASURED, step 6]` (spec `[MODELED]`).
- Square BF16 GEMM: n = 4096 27.1, n = 8192 28.3 TFLOP/s against 38.2 at the maximum clock; SM clock right after: 2535 MHz `[MEASURED, step 6]`.
- Sustained n = 8192 GEMM for 4.1 s: **27.9 TFLOP/s** at a median SM clock of **2295 MHz** and 80 W `[MEASURED, step 6]`. The BF16 peak at that clock is 28.2 TFLOP/s `[MODELED]`, so the GEMM is at 99 % of its clock-adjusted peak and 73 % of the maximum-clock figure.
- Measured ridge point: 125 FLOP/B `[MEASURED, step 6]`.

| K | AI (FLOP/B) | Time (ms) | TFLOP/s | GB/s | Bound | % of attainable |
|---|---|---|---|---|---|---|
| 16 | 15.9 | 0.141 | 3.81 | 240 | memory | 106 % |
| 32 | 31.5 | 0.137 | 7.83 | 248 | memory | 110 % |
| 64 | 62.1 | 0.137 | 15.65 | 252 | memory | 111 % |
| 128 | 120.5 | 0.169 | 25.37 | 211 | memory | 93 % |
| 256 | 227.6 | 0.314 | 27.33 | 120 | compute | 97 % |
| 512 | 409.6 | 0.609 | 28.22 | 69 | compute | 100 % |
| 1024 | 682.7 | 1.225 | 28.05 | 41 | compute | 99 % |
| 2048 | 1024.0 | 2.415 | 28.46 | 28 | compute | 101 % |
| 4096 | 1365.3 | 4.844 | 28.38 | 21 | compute | 100 % |

Telemetry: 1240 samples; clock-event reasons seen: {'0x0000000000000001': 287, '0x0000000000000004': 587, '0x0000000000000000': 366} `[MEASURED]`.

