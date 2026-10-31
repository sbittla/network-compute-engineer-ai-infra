# Lab 10 L2: NIC/optic probe and a physical-layer soak of the GPU's PCIe link

`[MEASURED]` on **CPU fallback: 13th Gen Intel(R) Core(TM) i7-13700HX**, 2026-10-31T23:43:37Z.

| Environment | Value |
|---|---|
| device | cpu |
| cpu_model | 13th Gen Intel(R) Core(TM) i7-13700HX |
| cpu_count | 24 |
| mem_total_gib | 7.8 |
| os | Linux-6.18.54.1-microsoft-standard-WSL2-x86_64-with-glibc2.35 |
| torch | 2.5.1+cu124 |
| cuda_runtime | 12.4 |

**Status:** ran
**Invariants:** all passed

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

_CPU fallback: no GPU, so no PCIe link was soaked; the link-state, replay and throughput invariants were skipped._

## Not runnable on this host

- **NIC port soak: ethtool -m (DOM per lane), --show-fec / -I --show-fec, ethtool -S, ip -s -s link, 600 s apart**: needs a 100G+ NIC port with a pluggable optic or DAC, ethtool >= 5.13 (mlxlink for NVIDIA NICs), root for ethtool -m, a peer or loopback to carry load. Probe: physical ports none, interfaces ['lo'].

- CPU fallback: no PCIe link status is visible in this container; the soak table is [MODELED].
