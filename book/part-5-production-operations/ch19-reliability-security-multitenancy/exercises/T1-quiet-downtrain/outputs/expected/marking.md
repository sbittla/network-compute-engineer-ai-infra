# Marking scheme: T1 The quiet downtrain

Type troubleshooting · kind computed · tier L1 · 12 points

**Evidence required:** hypothesis table; bandwidth arithmetic for x16 vs x8; containment decision; validation criteria

| Criterion | Points |
|---|---|
| Hypothesis table: PCIe downtrain root cause; compute straggler, fabric/optics and congestion rejected with evidence | 3 |
| Bandwidth arithmetic: x16 ≈ 63 GB/s, x8 ≈ 31.5 GB/s (≈ 25–27 achievable) < 50 GB/s NIC line rate | 2 |
| Explains why SM activity is uniform for a network straggler, unlike the Chapter 18 compute straggler | 2 |
| Containment: fault domain = mlx5_2 slot/riser/card, unit = node orion-n10; checkpoint + requeue; no spares on ORION | 3 |
| Fix and validation criteria (LnkSta x16, AER ≈ 0 over 1 h, rail-2 NCCL test, step time within 2 %); acceptance action | 2 |
