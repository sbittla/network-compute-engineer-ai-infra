# 3.9 — The price of a narrower pipe

Method: manuscript Section 3.6 ("How fast a link should be") and Section 3.11 Steps 1–6. All results
`[MODELED]` from `[ILLUSTRATIVE]` inputs (45 GB/s healthy rail, 82 % PCIe efficiency, 17.4 s step);
`solve.py` reproduces them.

**(a) Raw per-direction bandwidth.** Gen3 and later use 128b/130b encoding; Gen1/Gen2 use 8b/10b:

```text
Gen5 x16: 32  GT/s × 16 × 128/130 ÷ 8 = 63.0 GB/s
Gen4 x16: 16  GT/s × 16 × 128/130 ÷ 8 = 31.5 GB/s
Gen4 x2 : 16  GT/s ×  2 × 128/130 ÷ 8 =  3.94 GB/s
Gen1 x16: 2.5 GT/s × 16 × 8/10    ÷ 8 =  4.0 GB/s
```

**(b) Rail NIC 4 at Gen4 x16.**

```text
S (BF16 gradients per GPU) = 70e9 ÷ (TP 8 × PP 4) × 2 B = 4.375 GB
ring all-reduce sent       = 2 × 7/8 × 4.375 GB         = 7.656 GB
healthy  : 7.656 ÷ 45 GB/s                              = 0.170 s
degraded : achievable 0.82 × 31.5 = 25.8 GB/s → 7.656 ÷ 25.8 = 0.296 s
extra    : ≤ 0.296 − 0.170                              = 0.126 s per step   [MODELED]
lost fraction = 0.126 ÷ (17.4 + 0.126)                  = 0.0072
GPU-hours lost per day = 256 × 24 × 0.0072              ≈ 44 GPU-h/day       [MODELED]
```

Every rank-4 GPU of every DP replica is in the same ring, so all replicas wait for it, and the optimizer
waits for all rings. The bound is "≤" because the DP all-reduce partly overlaps the backward pass (only
≈ 70 ms with PP), so it is nearly tight.

**(c) Decision (no spare node on ORION-256).**

```text
keep running degraded   : 44 ÷ 24                    ≈ 1.8 GPU-h per hour
shrink to DP = 7        : 32 GPU-h per hour (one idle replica) + 2 × 64 GPU-h restarts
planned stop for repair : 64 GPU-h + 256 × T_repair
wait for next unplanned restart (MTBF 48 h): 48 × 1.8 ≈ 88 GPU-h
```

**Keep running** and repair at the next restart. A planned stop beats waiting only if
64 + 256 × T_repair < 88, that is T_repair < ≈ 6 minutes, which no repair achieves. Watch for escalation:
an AER storm, uncorrected errors or a width drop force a stop.

**Comparison with Gen3 x8 (Section 3.11):** 7.88 GB/s raw, 6.46 GB/s achievable, 1.185 s per DP
all-reduce, ≤ 1.015 s extra per step, ≈ **339 GPU-h/day** (14.1 per hour), about 8× worse. Shrinking
still loses (14.1 < 32), but waiting costs ≈ 677 GPU-h, so a planned stop wins for repairs shorter than
(677 − 64) / 256 ≈ **2.4 h**.

**Common wrong answers:** 8b/10b for Gen4/5; forgetting 2(n − 1)/n; mixing Gb/s and GB/s; assuming a spare
node exists, or that draining moves the job.
