# W1 — Checkpoint interval and restart overhead `[MODELED]`

overhead ≈ δ/τ + (τ/2 + R)/M; τ_opt ≈ √(2δM)

(a) M = 1,536/32 h = 2,880 min; τ_opt = √(2 × 1 × 2,880) = 75.9 min; overhead = 0.0132 + 0.0184 = 0.0316 → goodput 96.8 %
(b) M = 180 min, τ = 19: R = 15 → 0.1887 → 81.1 %; R = 5 → 0.1332 → 86.7 % (τ_opt = 19.0 min either way)
(c) 0.0556 × 4,096 GPUs × 24 h = 5,461 GPU-h/day × $3 = $16,384/day
