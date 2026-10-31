# W2 — Retry budgets and spares: worked solution

**Relies on:** Section 19.4 (RC retry mechanism, `NCCL_IB_TIMEOUT` defaults `[VENDOR-SPEC, 2026-10]`,
also docs/VERIFIED_FACTS.md); Section 19.7 "Rank remapping and spares" (Poisson pool sizing, the
Chapter 16 method); FMEA F03 (Table 19.2). Results `[MODELED]`.

## (a) Retry budget at `NCCL_IB_TIMEOUT=20`, `NCCL_IB_RETRY_CNT=7`

The local ACK timeout is 4.096 µs × 2^timeout per attempt, and the QP tries the original send plus
`retry_cnt` retransmissions before failing with status 12:

```text
per attempt = 4.096 µs × 2^20 = 4.096e-6 × 1,048,576 = 4.295 s
budget      ≈ (7 + 1) × 4.295 s = 34.4 s      (was (7 + 1) × 1.07 s ≈ 8.6 s at the old default 18)
```

The lab's flaps were 14 s, 6 s, 5 s and 14 s. All four are under 34.4 s, so **all four would now be
survived**: the job hiccups but does not hang. At the old default, only the 6 s and 5 s flaps were
survived; both 14 s flaps killed an attempt.

## (b) What a longer timeout costs

A *dead* peer (crashed node, real partition) is now reported only when the whole budget expires:

```text
extra detection delay = 34.4 − 8.6 = 25.8 s
cost per dead-peer event = 25.8 s × 4,096 GPUs / 3,600 = 29.3 GPU-h
compare: one 10-min watchdog = 600 s × 4,096 / 3,600 = 683 GPU-h
```

The direct cost is small. The real costs are:

- every flap now stalls the whole 4,096-GPU job for up to 14 s (≈ 16 GPU-h per flap), and
- **the flaky link stays in service**. Surviving hides a component that is degrading (orionxl-n212's
  optic was at the receiver-sensitivity edge) and will eventually fail hard, at a worse moment.

**Recommendation:** accept the longer timeout as a ride-through, **combined with** flap-rate quarantine
(FMEA F03: alert on every link-down; quarantine after 2 flaps in 24 h; DOM alerting at ≈ −4 dBm warn).
Trade-off: slower detection of genuine dead peers (+26 s) and short stalls, in exchange for not losing
the ≈ 5,500 GPU-h a hang-plus-restart costs. Other positions are acceptable if they are argued from the
same numbers (for example keeping 18 with early-abort hang detection).

## (c) Declared ORION-XL spare pool (variation: the reference cluster has none)

```text
failures/day = 512 nodes × 24 h / 1,536 h = 8 per day
nodes in repair ~ Poisson(λ = 8 × MTTR)
```

| MTTR | Mean in repair | Smallest k with P(X ≤ k) ≥ 0.99 | P(X ≤ k) | Pool / 512 |
|---|---|---|---|---|
| 3 days | 24 | **36** (P(≤ 35) = 0.987) | 0.992 | 7.0 % |
| 5 days (canonical) | 40 | **55** (P(≤ 54) = 0.986) | 0.990 | 10.7 % |

The pool sits *outside* the partition, so it is extra capex (55 HX8 nodes at 5 days). Cutting repair
turnaround from 5 to 3 days saves 19 nodes (3.7 % of the partition): a strong argument for faster RMA
logistics or on-site parts. A pool sized at the *mean* (24 or 40) would run short roughly half the time,
which forces fixed-size restarts to wait.

## Common wrong answers

- Budget = 7 × per attempt (forgetting the first try): 30.1 s.
- Using 2^18 with the new default, or the wrong version boundary.
- Adding a flat margin ("mean + 20 %") instead of the Poisson quantile (the key's named mistake).
- Counting the pool inside the 512 nodes.
