# 11.9 — Communication budget for the W-TRAIN baseline (TP 8, PP 4, DP 8)

Assumptions: Table 11.4 (NVLink busbw 300 GB/s, rail busbw 45 GB/s, NVLink latency 10 µs,
inter-node latency 30 µs, TP overlap 25 %, PP overlap 50 %, DP hides behind the last micro-batch's
backward). M = s·b·h·2 B = 4,096 × 8,192 × 2 = 67.1 MB. All values `[MODELED]`.

```text
TP: collectives = 4 × (80/4 layers) × 128 micro-batches = 10,240
    bytes = 10,240 × 2(7/8) × 67.1e6                     = 1.203e12 B  (1.2 TB)
    time  = 10,240 × (2(7/8) × 67.1e6 / 300e9 + 10 µs)   = 10,240 × (391.5 + 10) µs = 4.11 s
    exposed = 4.11 × (1 − 0.25)                          = 3.08 s
DP: P_local = 70e9/32 = 2.1875e9 → BF16 gradients 2P = 4.375e9 B
    bytes = 2(7/8) × 4.375e9                             = 7.656e9 B (7.66 GB)
    time  = 2(7/8) × 4.375e9 / 45e9 + 2 × 30 µs          = 0.170 s
    window = 13.916 s / 128 × 0.667                      = 0.0725 s → exposed 0.098 s
PP: bytes = 2 × 128 × 67.1e6 / 8                         = 2.147e9 B (2.15 GB)
    time  = 2.147e9 / 45e9 + 256 × 30 µs                 = 0.055 s → exposed (50 %) 0.028 s
```

**Priority.** Attack **TP first**: its 3.08 s exposed is ≈ 18 % of the 17.45 s step and more than 95 %
of all exposed communication (3.08 of 3.21 s). DP (0.098 s) and PP (0.028 s) together are under 1 % of
the step. Levers: better TP/compute overlap, or TP = 4 with more pipeline stages (lab candidate D).

**TP = 2 and the (t − 1) identity.**

```text
V_TP = 4 × 2(t−1)/t × M × (L/p) × m,   with (L/p) × m = L × B / (p × d × b) = L × B × t / (W × b)
     = 8 × (t − 1) × M × L × B / (W × b)
t = 2: 8 × 1 × 67.1e6 × 80 × 1,024 / 256 = 171.8 GB   (= 1.2026e12 / 7)
```

Because W = t·p·d is fixed, a GPU with smaller t processes proportionally more layer-micro-batches,
which cancels the 1/t of the per-collective factor 2(t − 1)/t: per-GPU TP bytes scale as (t − 1),
so TP = 8 → TP = 2 cuts them by 7×, not by 4×.

**Common wrong answers.** Using 2(t − 1)/t alone and concluding TP = 2 saves only 43 %; forgetting the
latency term (10,240 × 10 µs = 0.1 s); computing DP on the full 70e9 parameters.
