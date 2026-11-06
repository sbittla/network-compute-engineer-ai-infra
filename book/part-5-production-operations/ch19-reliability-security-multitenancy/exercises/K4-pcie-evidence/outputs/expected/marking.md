# Marking scheme: K4 PCIe evidence

Type knowledge-check · kind computed · tier L1 · 6 points

**Evidence required:** three definitions; bandwidth before/after in GB/s per direction

| Criterion | Points |
|---|---|
| Correctable AER: handled by the link layer (replay), counted only | 1 |
| Uncorrectable non-fatal: a transaction lost, link still usable, driver must recover | 1 |
| Uncorrectable fatal: link unreliable, device reset or retrain needed | 1 |
| Gen5 x16 ≈ 63 GB/s per direction theoretical (≈ 50–55 achievable) with the 128b/130b arithmetic | 1 |
| x8 ≈ 31.5 GB/s theoretical (≈ 25–27 achievable), below a 400 Gb/s (50 GB/s) NIC's line rate | 2 |
