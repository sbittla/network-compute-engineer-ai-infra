# W2 — Incast and DCQCN feedback timing (worked solution)

All numbers `[MODELED]`. Relies on manuscript Section 9.7 (incast arithmetic: fill time = buffer /
((N − 1) × r)), Section 9.6 (DCQCN rate rules, worked halving consequence) and Section 9.3 (choosing
Kmin). r = 400 Gb/s = 50 GB/s = **50 KB/µs** (decimal units).

## (a) Excess arrival rate

Arrival = 16 × 50 KB/µs = 800 KB/µs; drain = 50 KB/µs.
Excess = (16 − 1) × 50 KB/µs = **750 KB/µs**.

## (b) Time to reach the 1.5 MB threshold

t = 1,500 KB / 750 KB/µs = **2.0 µs**.

## (c) Can ECN feedback arrive first?

**No.** A CNP can affect a sender no earlier than **one RTT (6 µs)** after the first CE mark, plus CNP
generation time at the NP. The threshold is crossed at 2 µs, a third of that. PFC must absorb the
first burst. Without PFC the 6 MB share would fill in 6,000 / 750 = **8 µs**, and drops would follow
before the first rate cut takes effect.

## (d) Minimum possible completion time

Total = 16 × 2 MB = 32 MB through a single 400 Gb/s egress:
32 × 10⁶ B / 50 × 10⁹ B/s = **640 µs**. No congestion control can beat it.

## (e) Repeated DCQCN halving

The aggregate rate must fall from 16 × r to 1 × r, a 16× cut. With α ≈ 1 each CNP halves a flow's rate
(Rc ← Rc × (1 − α/2)), so **log₂ 16 = 4 halvings** are needed. The first cut lands ≈ 1 RTT after
marking starts (≈ 6 µs). Later cuts come at most once per CNP interval N = 50 µs per flow:
t ≈ 6 + 3 × 50 = **≈ 156 µs**, which is 156 / 640 ≈ **24 %** of the minimum completion time. During that
time PFC carries the excess. (Counting 4 × 50 = 200 µs ≈ 31 % is accepted with stated reasoning; the
range 150–210 µs is accepted.) In reality α grows toward 1 with repeated CNPs and recovery starts
between cuts, so this is a rough lower-order estimate.

## (f) BDP and an upper bound for Kmin

BDP = 50 GB/s × 6 µs = **300 KB**. Kmin should be **≤ 1 BDP** and comfortably below the 1.5 MB PFC
threshold (a defensible choice is 100–300 KB). Marking must start early enough that a full RTT of
feedback delay (≈ 1 BDP of extra arrival) still lands before Xoff. Otherwise PFC engages before DCQCN
has a chance to act, and the fabric "runs on pause". This is exactly the lab's leaf-r3 fault: Kmin
1,500 KB = 7.5 × BDP.

## Common mistakes

Using 16 × 50 instead of 15 × 50 for the excess. Expecting ECN to prevent the first burst. Treating DCQCN
as cutting every RTT (it is limited by N). Choosing Kmin above the PFC threshold.
