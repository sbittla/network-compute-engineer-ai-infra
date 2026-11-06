# W1 — Headroom budget for a spine (worked solution)

All numbers `[MODELED]`. Relies on manuscript Section 9.4 ("The headroom formula", Table 9.2,
Table 9.3). Conventions: r = 400 Gb/s = 50 GB/s = **50 B/ns**; v ≈ 2 × 10⁸ m/s → **5 ns/m**; port MTU
**9,216 B** (the switch MTU, not the 4,096 RDMA path MTU); t_resp = **1 µs**; PFC frame 64 B.

**H = 2 × MTU + 2 × r × (L / v) + r × t_resp + 64 B**

## (a) Per port per lossless priority, 150 m, 400 Gb/s

| Term | Substitution | Bytes |
|---|---|---|
| L / v | 150 m × 5 ns/m | 750 ns |
| 2 × MTU | 2 × 9,216 B | 18,432 |
| 2 × r × L / v | 2 × 50 B/ns × 750 ns | 75,000 |
| r × t_resp | 50 B/ns × 1,000 ns | 50,000 |
| PFC frame | | 64 |
| **H** | | **143,496 B ≈ 143.5 KB** |

## (b) Whole switch

64 ports × 2 lossless priorities × 143,496 B = **18,367,488 B ≈ 18.4 MB** of buffer reserved as
headroom and taken out of the shared pool that absorbs bursts. On a switch with a few tens of MB of
packet buffer, that is a large fraction. This is why ORION keeps one lossless priority.

## (c) Same cable, MTU and response time at 800 Gb/s

r = 100 B/ns: 18,432 + 2 × 100 × 750 + 100 × 1,000 + 64 = 18,432 + 150,000 + 100,000 + 64 =
**268,496 B ≈ 268.5 KB**, which is 268,496 / 143,496 ≈ **1.87×** the 400 Gb/s value.

**Comment (one sentence):** the wire and response terms scale linearly with link rate and only the MTU
term does not, so headroom nearly doubles with each speed doubling, while switch buffer per port
typically grows more slowly, so every speed upgrade shrinks the buffer left for bursts.

## Common mistakes

Using 4,096 B (RDMA path MTU) instead of the 9,216 B port MTU. Counting propagation once instead of
twice (gives 105,996 B). Forgetting the factor of 2 priorities in (b). Treating 150 m as round-trip.
