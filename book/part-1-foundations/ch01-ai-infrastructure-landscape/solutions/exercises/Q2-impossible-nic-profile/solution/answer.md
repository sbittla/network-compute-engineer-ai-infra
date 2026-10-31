# Q2 — 40 GB through a 400 Gb/s NIC in 0.5 s

Source: manuscript Section 1.6 (ceiling fraction above 1.0) and lab row W12. `solve.py` checks the
arithmetic.

```text
implied rate   = 40 GB / 0.5 s          = 80 GB/s
line rate      = 400 Gb/s / 8           = 50 GB/s
lower bound    = 40 GB / 50 GB/s        = 0.8 s  >  0.5 s observed
ceiling fraction = 0.8 / 0.5            = 1.6  → physically impossible
```

**Conclusion:** the profile is wrong, not the NIC. Likely causes: the host counter summed TX and RX
(80 GB/s ≈ 2 × 40 GB/s of a bidirectional exchange), counters from two NICs were aggregated, a
bits/bytes confusion elsewhere in the pipeline, or the time window is wrong (the bytes were sent over more
than 0.5 s). Ask the owner which counter and window they used before using the row; do not "fix" it by
halving the number.
