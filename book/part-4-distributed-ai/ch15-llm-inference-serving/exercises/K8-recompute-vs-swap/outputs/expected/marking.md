# Marking scheme: K8 Recompute versus swap

Type knowledge-check · kind computed · tier L1 · 4 points

**Evidence required:** both estimates with stated assumptions (prefill µs/token; PCIe GB/s)

| Criterion | Points |
|---|---|
| Recompute: 10,000 x 88.4 µs ≈ 0.88 s on TP = 2 FP8 at 40 % MFU, stalls co-scheduled sequences | 2 |
| Swap: 3.28 GB total, 1.64 GB per GPU at about 50 GB/s ≈ 33 ms each way, plus host-memory pressure | 2 |
