# K4 — PCIe evidence: worked solution

**Relies on:** Section 19.3 "PCIe AER and link retraining"; Reference Cluster PCIe row; docs/VERIFIED_FACTS.md
("PCIe Gen5 achievable bandwidth"). Rates are `[VENDOR-SPEC, 2026-10]` arithmetic; achievable ranges `[ILLUSTRATIVE]`.

## Three AER classes

- **Correctable:** the link layer detects and fixes it (for example a receiver error or bad TLP that is
  replayed). Software only counts it. A low, steady rate is fleet background noise; a rising rate is
  actionable.
- **Uncorrectable, non-fatal:** a transaction is lost, but the link itself still works. The device
  driver must recover (retry or fail the request).
- **Uncorrectable, fatal:** the link is no longer reliable. The device must be reset or the link
  retrained, and the device may need replacement.

## What `LnkSta: 32GT/s, Width x8` under `LnkCap: Width x16` means

The link trained at full speed (Gen5) but half width: it is "downgraded". Bandwidth scales with lanes.

```text
Gen5 x16 = 32 GT/s × 16 lanes × 128/130 / 8 bit/B = 63.0 GB/s per direction (theoretical)
Gen5 x8  = 32 GT/s ×  8 lanes × 128/130 / 8 bit/B = 31.5 GB/s per direction (theoretical)
achievable: x16 ≈ 50–55 GB/s; x8 ≈ 25–27.5 GB/s (≈ 200–220 Gb/s)
```

| | Theoretical | Achievable |
|---|---|---|
| Before (x16) | ≈ 63 GB/s/dir | ≈ 50–55 GB/s/dir |
| After (x8) | ≈ 31.5 GB/s/dir | ≈ 25–27 GB/s/dir |

For a GPU, this halves its host and peer-to-peer bandwidth (host↔GPU copies, data loading, GPU↔NIC traffic
that crosses that link). If the downgraded link is the NIC's, a 400 Gb/s (50 GB/s) NIC is capped near
200–220 Gb/s: the rail runs at about half rate and every collective on that rail waits for it. Nothing
crashes. It is a classic silent straggler (see T1).

## Common wrong answers

- Mixing Gb/s and GB/s (400 Gb/s = 50 GB/s).
- Quoting the 252 Gb/s raw x8 figure as achievable.
- Assuming lower *speed* when only the *width* changed.
- Calling correctable errors "harmless": they are harmless individually, but here thousands of corrected
  Physical Layer errors accompany the downtrain and point to a marginal connector or riser.
