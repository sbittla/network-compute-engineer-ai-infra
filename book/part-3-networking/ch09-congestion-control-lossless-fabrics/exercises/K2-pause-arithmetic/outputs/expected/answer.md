# K2 — Pause quantum arithmetic (worked solution)

All numbers `[MODELED]`. Relies on manuscript Section 9.4 ("What a PFC frame is", Figure 9.3).

**Formula:** one pause quantum = **512 bit-times** = 512 bit / link rate. The 16-bit timer field allows
at most 65,535 quanta per frame.

| Rate | Quantum | Maximum single-frame pause |
|---|---|---|
| 100 Gb/s | 512 bit / (100 × 10⁹ bit/s) = **5.12 ns** | 65,535 × 5.12 ns = 335,539 ns ≈ **335.5 µs** |
| 400 Gb/s | 512 bit / (400 × 10⁹ bit/s) = **1.28 ns** | 65,535 × 1.28 ns = 83,885 ns ≈ **83.9 µs** |

The quantum is defined in bit-times, so a faster link pauses for a *shorter* wall-clock time per
quantum. At 400 Gb/s a single frame can stop a priority for at most ≈ 84 µs.

## Why a sustained pause appears as a *rate* (one sentence)

A pause longer than one frame's maximum (≈ 84 µs at 400 Gb/s) requires the pausing device to keep
**refreshing** it with new pause frames before the timer expires (and to end it early with a quanta-0
XON), so a port held in pause shows a steady stream of frames in `pfc_tx_p3`/`pfc_rx_p3`. With
refresh at half the lifetime, that is 1 / 41.9 µs ≈ **23,800 frames/s** at 400 Gb/s (≈ 6,000/s at
100 Gb/s). That is exactly the ≈ 23,750/s pause rx rate in the lab's PFC-storm episode.

Refresh policy is implementation-specific. The rate tells you a pause is *sustained*, not exactly how
long it lasted: use pause-duration counters for that.

**Common mistake:** using bytes instead of bits (512 B / 50 GB/s = 10.24 ns, an 8× error), or
reporting the maximum pause as 65,535 ns.
