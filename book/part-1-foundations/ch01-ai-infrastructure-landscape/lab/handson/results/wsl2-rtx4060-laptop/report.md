# Chapter 1 hands-on: NVIDIA GeForce RTX 4060 Laptop GPU against its ceilings

Every number below is `[MEASURED]` on this machine by `ch01_ceilings.py` unless labelled `[VENDOR-SPEC, 2026-10]` (peak constants) or `[MODELED]` (derived through the ceiling model).

## Step 1: inventory

- 24 SMs, 512 BF16 FLOP/clock/SM `[VENDOR-SPEC, 2026-10]`, 128-bit memory bus `[VENDOR-SPEC, 2026-10]`; maximum SM clock 3105 MHz `[MEASURED]` (nvidia-smi).
- Peak at maximum clock 38.2 TFLOP/s; theoretical bandwidth 256 GB/s; machine balance 149 FLOP/B `[MODELED]` (ORION HX8: 295 FLOP/B).
- Idle: 18.4 W, SM clock 2250 MHz `[MEASURED]`.

## Step 2: empirical ceilings

- BF16 GEMM 8192³: 27.8 TFLOP/s `[MEASURED]` at a mean SM clock of 2307 MHz and 80.2 W (power cap active in 100 % of samples) `[MEASURED]`.
- Clock-adjusted peak 28.3 TFLOP/s `[MODELED]`: the GEMM reaches 0.98 of it, but only 0.73 of the max-clock peak.
- Device copy: 228 GB/s `[MEASURED]` = 0.89 of 256 GB/s theoretical at SM clock 2535 MHz, 53.0 W.
- Machine balance at the GEMM's clock 111 FLOP/B `[MODELED]`; empirical (GEMM ÷ copy) 122 FLOP/B `[MEASURED]`.

## Step 3: from decode-like to GEMM-like (Y = X·W, W = 8192 × 8192 BF16)

| Batch B | Intensity (FLOP/B) | Observed (µs) | T_compute (µs) | T_memory (µs) | Dominant | Ceiling fraction | Achieved |
|---:|---:|---:|---:|---:|---|---:|---|
| 1 | 1.0 | 543.7 | 5.0 | 524.4 | memory | 0.96 | 247 GB/s |
| 4 | 4.0 | 556.4 | 18.1 | 524.8 | memory | 0.94 | 241 GB/s |
| 16 | 15.9 | 555.7 | 69.7 | 526.3 | memory | 0.95 | 242 GB/s |
| 64 | 63.0 | 649.8 | 310.0 | 532.5 | memory | 0.82 | 210 GB/s |
| 256 | 240.9 | 1349.8 | 1278.8 | 557.1 | compute | 0.95 | 25.5 TFLOP/s |
| 1024 | 819.2 | 5173.3 | 4956.3 | 655.4 | compute | 0.96 | 26.6 TFLOP/s |
| 4096 | 2048.0 | 20232.6 | 19651.2 | 1048.6 | compute | 0.97 | 27.2 TFLOP/s |

Observed times and achieved rates `[MEASURED]`; lower bounds `[MODELED]` from the clock-adjusted peak.

## Step 4: a training step (8-layer, d = 768 decoder, sequence 512, BF16 autocast, fused AdamW)

| Batch | Tokens/step | Median step (ms) | Tokens/s | Achieved (6N) | SM clock (MHz) | MFU (clock-adjusted) | MFU (max clock) | T_compute (ms) | T_memory (ms) | Dominant | Ceiling fraction | Band |
|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---|---:|---|
| 1 | 512 | 28.0 | 18,288 | 6.9 TFLOP/s | 2520 | 0.22 | 0.18 | 6.2 | 10.9 | memory | 0.39 | meaningful |
| 4 | 2048 | 56.4 | 36,284 | 13.7 TFLOP/s | 2387 | 0.47 | 0.36 | 26.4 | 14.0 | compute | 0.47 | meaningful |
| 16 | 8192 | 196.6 | 41,660 | 15.7 TFLOP/s | 2314 | 0.55 | 0.41 | 108.9 | 26.5 | compute | 0.55 | meaningful |

Step time, tokens/s, clocks `[MEASURED]`; FLOP counts, MFU, lower bounds `[MODELED]` (6N FLOPs per token; minimum bytes = 36 B per parameter plus twice the measured bytes saved for backward).

## Verdict

- Batch 16: **compute-bound**, ceiling fraction 0.55 `[MODELED]`.
- Confirming evidence (Table 1.7): tokens ×4 → step time ×3.48; time per token ratio 0.87 `[MEASURED]` (scales with FLOPs).
- Smallest batch: meaningful (0.25-0.9): gap is ordinary inefficiency.
- ORION W-TRAIN runs at MFU 0.40 against a 295 FLOP/B machine; this GPU's best step reached 0.55 against 111 FLOP/B. Ratios and mechanisms carry over; absolute values do not.
