# 3.4 — Classifying PCIe status lines

Source: manuscript Section 3.6 ("How fast a link should be", "Capability versus status") and the lab's
severity policy (`PCIE_WIDTH_DEGRADED`, `PCIE_SPEED_DEGRADED`, `PCIE_SPEED_LOW_IDLE`). `solve.py` applies
the rules and computes the bandwidth for (d).

**Rules.** (1) Width below capability is never benign: a fault (critical). (2) Speed below capability
under load is a fault (warning). (3) Speed below capability on an *idle* GPU is power management:
probably benign, verify under load. (4) Status equal to capability is healthy, whatever the absolute
numbers.

| Line | Verdict | Rule and reasoning |
|---|---|---|
| (a) GPU `32GT/s x16` → `32GT/s x8`, 95 % busy | **Fault (critical)** | Rule 1: a lane-training failure halves the link (31.5 GB/s raw instead of 63.0); it does not recover by itself |
| (b) GPU `32GT/s x16` → `2.5GT/s x16`, 0 % busy | **Probably benign — verify** | Rule 3: idle GPUs drop link speed to save power; width is full. Re-read under load |
| (c) BMC VGA `5GT/s x1` = `5GT/s x1` | **Healthy** | Rule 4: an x1 Gen2 link is the device's design |
| (d) Rail NIC `32GT/s x16` → `16GT/s x16` during an all-reduce | **Fault (warning)** | Rule 2: under load, so not power saving |

**Consequence for (d):** Gen4 x16 = 16 × 16 × 128/130 ÷ 8 = **31.5 GB/s** raw per direction, ≈ 0.82 ×
31.5 = **25.8 GB/s** achievable `[MODELED]`. That is below the 50 GB/s line rate of the 400 Gb/s port,
so rail traffic through this NIC is PCIe-capped at about half its design bandwidth, and every collective
on that rail runs at its pace (the Section 3.11 cost method applies).

**Common wrong answers:** flagging (c) because "x1 looks degraded"; flagging (b) as critical; trusting the
`(ok)`/`(downgraded)` annotation instead of comparing numbers (pciutils versions differ).
