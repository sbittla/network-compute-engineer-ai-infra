# W1 — Checkpoint interval and restart overhead: worked solution

**Relies on:** Section 19.1 "What a failure costs" (Young's first-order model); Reference Cluster
reliability canon (node MTBF 1,536 node-h, R = 15 min `[ILLUSTRATIVE]`). Results `[MODELED]`.

```text
overhead ≈ δ/τ + (τ/2 + R)/M        goodput = 1 − overhead
τ_opt    ≈ √(2 · δ · M)
```

δ = blocking checkpoint cost, τ = checkpoint interval, R = restart overhead, M = job MTBF. Use one time
unit throughout (minutes). The model is first-order and valid only while τ ≪ M; both cases here satisfy
that (75.9 ≪ 2,880 and 19 ≪ 180).

## (a) 32-node ORION job, δ = 1 min, R = 15 min

```text
M      = 1,536 h / 32 = 48 h = 2,880 min
τ_opt  = √(2 × 1 × 2,880) = √5,760 = 75.9 min
δ/τ    = 1 / 75.9                 = 0.0132
(τ/2 + R)/M = (37.95 + 15) / 2,880 = 0.0184
overhead = 0.0316  →  goodput = 96.8 %
```

## (b) 512-node ORION-XL job, τ = 19 min

```text
M = 1,536 / 512 = 3 h = 180 min;   δ/τ = 1/19 = 0.0526
R = 15 min: (9.5 + 15)/180 = 0.1361 → overhead 0.1887 → goodput 81.1 %
R =  5 min: (9.5 +  5)/180 = 0.0806 → overhead 0.1332 → goodput 86.7 %
```

τ_opt = √(2 × 1 × 180) = 19.0 min in both cases: in Young's model the optimum interval does not depend
on R, because R is paid once per failure whatever the interval.

## (c) Value of cutting R from 15 to 5 min

```text
Δoverhead = (15 − 5) / 180 = 0.0556
4,096 GPUs × 24 h × 0.0556 = 5,461 GPU-h/day
5,461 GPU-h/day × $3.00/GPU-h ≈ $16,400/day  (≈ $6.0M/year)     [MODELED]
```

## Lesson

At 512 nodes, R alone costs 15/180 = 8.3 % of the job. Reducing restart overhead (hot spares, pre-staged
images, parallel restore, automatic triage) buys about five points of goodput. Checkpoint-interval tuning
near the flat optimum buys about one.

## Common wrong answers

- Mixing hours and minutes (for example M = 3 with δ = 1 min gives τ_opt = 2.4 "min"). This is the key's
  named mistake.
- Using M = node MTBF rather than job MTBF.
- Recomputing τ_opt with R inside the square root.
- In (c), using nodes (512) instead of GPUs (4,096) for GPU-hours.
