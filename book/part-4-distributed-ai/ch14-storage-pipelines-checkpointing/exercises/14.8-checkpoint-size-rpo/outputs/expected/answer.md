# 14.8 — Checkpoint size, write time and recovery-point exposure: worked solution

All values are `[MODELED]` from the prompt's `[ILLUSTRATIVE]` inputs. Formulas follow Sections 14.9 and
14.11.

**(a) Size.** S = params × B/param = 34 × 10⁹ × 14 B = **476 GB**. Per GPU: 476 GB / 128 = **3.72 GB**.

**(b) Write and blocking time (synchronous).**

```text
effective bandwidth = 50 GB/s × 0.80        = 40 GB/s
write time          = 476 GB / 40 GB/s      = 11.9 s
blocking time       = write + commit = 11.9 + 1.0 = 12.9 s
```

**(c) Overhead.** δ/τ = 12.9 s / 900 s = **1.43 %**.

**(d) Exposure.** For a synchronous save, completion latency L = blocking = 12.9 s.

```text
RPO max      = τ + L   = 900 + 12.9 = 912.9 s ≈ 15.2 min
E[lost work] = τ/2 + L = 450 + 12.9 = 462.9 s
```

**(e) Asynchronous, same 15-minute interval.** Blocking falls to the 0.6 s snapshot. The persist
(12.9 s) runs in the background at 3 % interference:

```text
overhead (blocking only)      = 0.6 / 900              = 0.067 %
overhead (with interference)  = (0.6 + 0.03 × 12.9) / 900 = 0.987 / 900 = 0.11 %
L                             = 0.6 + 12.9             = 13.5 s
RPO max                       = 900 + 13.5             = 913.5 s   (unchanged)
```

Asynchrony cut the *premium* about 13×. It did not cut the *exposure*.

**(f) Interval for RPO ≈ 5 min.** τ + L ≤ 300 s → τ = 300 − 13.5 = **286.5 s** (≈ 4.8 min).

```text
δ        = 0.6 + 0.03 × 12.9 = 0.987 s
overhead = 0.987 / 286.5      = 0.34 %
```

This is about a quarter of the original synchronous overhead (1.43 %) with a third of the RPO. Make sure
L (13.5 s) is well below τ, so that only one checkpoint is in flight.

**Common wrong answers.** Using 50 GB/s without the 80 % efficiency (9.5 s). Omitting the commit time.
Claiming that async reduces RPO. Using τ/2 for the worst case.
