# Lab 10 L2: NIC/optic probe and a physical-layer soak of the GPU's PCIe link

`[MEASURED]` on **NVIDIA GeForce RTX 4060 Laptop GPU**, 2026-10-31T23:42:25Z.

| Environment | Value |
|---|---|
| device | cuda |
| cpu_model | 13th Gen Intel(R) Core(TM) i7-13700HX |
| cpu_count | 24 |
| mem_total_gib | 7.8 |
| os | Linux-6.18.54.1-microsoft-standard-WSL2-x86_64-with-glibc2.35 |
| torch | 2.5.1+cu124 |
| cuda_runtime | 12.4 |
| driver_version | 592.82 |
| pcie.link.gen.max | 4 |
| pcie.link.width.max | 8 |
| clocks.max.sm | 3105 |
| power.limit | [N/A] |

**Status:** ran
**Invariants:** all passed

## PCIe link soak `[MEASURED]`

| Quantity | T0 | T1 | Delta |
|---|---|---|---|
| Replays since reset | 0 | 0 | 0 |
| Replay number rollovers | 0 | 0 | 0 |

| Quantity | Value |
|---|---|
| Capability | Gen4 x8 (16.0 GT/s per lane, 128b/130b) |
| Negotiated under load | Gen4 x8 (110 samples) |
| Soak | 60.01 s, 777.4 GB moved (6.22e+12 bits) |
| Per direction (median window) | 6.48 GB/s of 15.75 GB/s coded ceiling (41 %) |
| H2D alone (median of 10) | 12.31 GB/s |
| 95 % upper bound on replay events per bit | 4.82e-13 |
| Certifies the PCIe 1e-12 target? | yes |
| Soak needed to certify 1e-12 at this rate | 29.0 s |

What to conclude:

- The link held its full capability under load (Gen4 x8 of Gen4 x8) and moved 6.2e+12 bits with 0 replays. Zero errors is not a BER of zero: it only bounds the rate below 4.8e-13 per bit at 95 % confidence.
- To certify 1e-12 this soak would need about 29 s at the achieved rate, and 1e-15 a thousand times longer. The same arithmetic is why the chapter's optics check differences counters 600 s apart under load and why pre-FEC BER (millions of corrected codewords) is the useful early signal on a 400G port, not post-FEC errors.
- With both directions busy each got 6.48 GB/s against 12.31 GB/s for H2D alone: the full-duplex link is not the only shared resource (DMA engines, host memory and the root complex are too). Measure the load you will actually run.
- Read capability *and* negotiated state, under load: a link that trains down (x8 to x4, Gen4 to Gen3) passes every ping and halves throughput, exactly like a 400G optic linked at 200G.
- This is a laptop GPU's PCIe link, not a 400G optical port: there is no DOM, no FEC histogram and no lane power to read. Those rows of the analyzer need the L2 NIC host.

## Soak length needed to certify a BER (zero errors, 95 %) `[MODELED]`

| Link | BER target | Bits needed | Seconds at line rate |
|---|---|---|---|
| 400GbE port (one direction) | 1e-12 | 3.0e+12 | 7.5 |
| 400GbE port (one direction) | 1e-15 | 3.0e+15 | 7500.0 |
| PCIe Gen4 x8 (one direction) | 1e-12 | 3.0e+12 | 23.8 |
| PCIe Gen4 x8 (one direction) | 1e-15 | 3.0e+15 | 23803.7 |
| PCIe Gen5 x16 (one direction) | 1e-12 | 3.0e+12 | 6.0 |
| PCIe Gen5 x16 (one direction) | 1e-15 | 3.0e+15 | 5950.9 |

## L1 analyzer on the lab snapshots (reference)

64 ports classified by `solutions/lab/linkhealth.py`: CONGESTION 1, CRC_ERRORS 1, HEALTHY 55, LINK_FLAP 1, MISCABLED 2, OPTIC_MISMATCH 1, OVERSIZE_FRAMES 1, PRE_FEC_BER_HIGH 1, RX_POWER_LOW 1.

## Not runnable on this host

- **NIC port soak: ethtool -m (DOM per lane), --show-fec / -I --show-fec, ethtool -S, ip -s -s link, 600 s apart**: needs a 100G+ NIC port with a pluggable optic or DAC, ethtool >= 5.13 (mlxlink for NVIDIA NICs), root for ethtool -m, a peer or loopback to carry load. Probe: physical ports none, interfaces ['lo'].

- Load: 256 MiB pinned H2D and D2H copies on two streams, 8 of each per timing window, for 60.0 s.
- Replays are counted by the GPU's data-link layer; one replay means at least one TLP failed its LCRC check, so a bound on replays per bit is a bound on detected errors, not a full BER measurement.
- Link state was sampled every 0.5 s during the load with nvidia-smi.
