# Marking scheme: W2 Checkpoint interval and goodput

Type worked-problem · kind computed · tier L1 · 10 points

**Evidence required:** arithmetic for each part; the backlog choice justified by numbers

| Criterion | Points |
|---|---|
| Part 1: τ = sqrt(2 × 60 × 86,400) ≈ 3,220 s; δ/τ ≈ τ/(2M) ≈ 1.86 %; R/M ≈ 1.04 %; total ≈ 4.77 % | 3 |
| Part 2: (τ/2 + R) = 2,510 s × 256 / 3,600 ≈ 178.5 GPU-hours per failure | 2 |
| Part 3: goodput 0.902 → 96.00 / 0.902 ≈ 106.4 days | 2 |
| Part 4: reduce δ (async checkpoint) first, justified with recomputed waste (≈ 2.12 %, ≈ 3 days saved); R second | 3 |
