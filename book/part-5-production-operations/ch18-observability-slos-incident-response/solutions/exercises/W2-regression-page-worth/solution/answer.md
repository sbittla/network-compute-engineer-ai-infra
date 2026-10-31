# W2 — Is a 9 % regression worth a page?

4,096-GPU ORION-XL job; step 17.4 s → 19.0 s; $3 per GPU-hour `[ILLUSTRATIVE price]`. `[MODELED]`

**(a)** Throughput ratio = 17.4 / 19.0 = **0.916**; fraction of GPU time lost = 1 − 0.916 = **0.084**
(8.4 %).

**(b)** Lost GPU-hours = duration × GPUs × lost fraction.
- Case A: (6 h + 0.5 h) × 4,096 × 0.0842 = **2,242 GPU-h → ≈ $6,730**.
- Case B: (12 + 30) min = 0.7 h; 0.7 × 4,096 × 0.0842 = **241 GPU-h → ≈ $724**.
Detection saves ≈ 2,000 GPU-h ≈ $6,000 per incident.

**(c)** 19.0 / 17.4 = **1.092 < 1.10** → `TrainingThroughputFastBurn` does **not** fire: the ratio
never drops below 0.909, so no minute counts as bad.
*Proposed threshold for jobs ≥ 1,024 GPUs: 1.05 × baseline* (ratio < 0.952).
*Noise argument:* Lab 18 step-time noise is ≈ 1.2 % (sd) `[SIMULATED]`. A 10-minute rolling median
covers ≈ 600 / 17.4 ≈ 34 steps; the median's sd ≈ 1.25 × σ / √n = 1.25 × 1.2 % / √34 ≈ **0.26 %**, so a
5 % shift is ≈ 19 sd away from normal variation: false positives from noise are negligible; real
risk comes from legitimate slow phases.
*Evidence before adopting it:* ≥ 2 weeks of rolling-median ratios per large job, including
checkpoint, evaluation, and data-shard boundaries, showing a false-positive rate within the page
budget (two incidents per 12 h shift, D1); a check that legitimate configuration changes (batch size,
parallelism) reset the baseline. The economic case: at 4,096 GPUs, every hour of an undetected 5 %
regression costs ≈ 205 GPU-h.

Accept 1.03–1.07 with a sound noise argument. Source: Section 18.8 ("A burn-rate alert for training
throughput"). `solve.py` reproduces (a)–(c).
