# Chapter 21 hands-on: performance per watt and cost per useful GPU-hour

Power, energy, throughput and busy fraction are `[MEASURED]` (board power from nvidia-smi at ~100 ms; energy = ∫P dt). FLOP counts and costs are `[MODELED]`; your cost inputs are `[ASSUMPTION]` (cost_inputs.json); ORION figures are the chapter's `[MODELED]` values.

## Step 1: what you can vary here

- Power limit change permitted: **False**; clock lock: **not attempted** `[MEASURED]` (controls.txt). Power-cap sweep run: False.
- Idle board power 16.0 W `[MEASURED]`.

## Steps 2-3: the same job (fixed tokens) at different intensity and busy fraction

| Job | Batch | Busy fraction | Wall (s) | Avg power (W) | Energy (kJ) | J/token | Tokens/J | TFLOP/J | Tokens/s (wall) | SM clock (MHz) | Power cap |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| intensity_b1 | 1 | 1.00 | 28.5 | 69.2 | 1.97 | 3.75 m | 266 | 0.101 | 18,424 | 2535 | 0 % |
| intensity_b4 | 4 | 1.00 | 14.3 | 78.6 | 1.12 | 2.14 m | 468 | 0.177 | 36,770 | 2445 | 100 % |
| intensity_b16 | 16 | 1.00 | 12.2 | 79.3 | 0.97 | 1.85 m | 541 | 0.205 | 42,923 | 2370 | 100 % |
| duty_075 | 16 | 0.75 | 16.3 | 68.4 | 1.12 | 2.13 m | 469 | 0.177 | 32,080 | 2415 | 76 % |
| duty_050 | 16 | 0.50 | 24.3 | 52.7 | 1.28 | 2.44 m | 409 | 0.155 | 21,560 | 2520 | 49 % |
| duty_025 | 16 | 0.25 | 48.4 | 37.0 | 1.79 | 3.42 m | 293 | 0.111 | 10,839 | 2535 | 19 % |

- Batch 16 does the job with 2.03× the tokens per joule of batch 1 (higher power, much shorter time) `[MEASURED]`.
- duty_075: busy 0.75, energy +15 % for the same tokens (idle-but-allocated watts) `[MEASURED]`.
- duty_050: busy 0.50, energy +32 % for the same tokens (idle-but-allocated watts) `[MEASURED]`.
- duty_025: busy 0.25, energy +85 % for the same tokens (idle-but-allocated watts) `[MEASURED]`.

## Step 4: cost per useful GPU-hour, yours beside ORION's

Your inputs `[ASSUMPTION]`: $1,500 over 3 years, $0.08/kWh, PUE 1.0, host power 0 W, allocated 0.25 of owned hours.

| Case | Nominal $/GPU-h | Goodput | $/useful GPU-h | $/M tokens | $/PFLOP | Electricity share |
|---|---:|---:|---:|---:|---:|---:|
| ORION (book, Section 21.4) `[MODELED]` | 3.00 | 0.88 | 4.72 | 1.39 (70B) | 0.0033 | 4 % |
| Yours, intensity_b16 | 0.0596 | 1.00 | 0.239 | 0.002 (63M) | 0.0041 | 4 % |
| Yours, duty_075 | 0.0594 | 0.75 | 0.317 | 0.002 (63M) | 0.0054 | 4 % |
| Yours, duty_050 | 0.0591 | 0.50 | 0.473 | 0.003 (63M) | 0.0081 | 3 % |
| Yours, duty_025 | 0.0588 | 0.25 | 0.942 | 0.006 (63M) | 0.0159 | 3 % |

ORION's $3.00 rate with your measured goodput in place of 0.88 `[MODELED]`: intensity_b16 → $4.15, duty_075 → $5.55, duty_050 → $8.31, duty_025 → $16.64.

## Energy per unit of work against ORION

- ORION W-TRAIN: 0.33 TFLOP/J at the IT load (whole node, 40 % MFU) and 0.44 facility kWh per million tokens of a 70B model `[MODELED]`.
- This GPU at batch 16: 0.205 TFLOP/J (board only) and 0.0005 kWh per million tokens of a 63M model `[MEASURED]`; at batch 1: 0.101 TFLOP/J.
- Compare per FLOP, not per token: a token of a 70B model is ≈ 1,100× the work of a token of this model.
