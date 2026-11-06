# Marking scheme: 17-K1 Capacity 8, allocatable 7

Type knowledge-check · kind written · tier L1 · 5 points

**Evidence required:** The component that sets the number, the mechanism, and the scheduler outcome.

| Criterion | Points |
|---|---|
| Component: NVIDIA device plugin reports healthy devices to the kubelet, which sets allocatable | 2 |
| Mechanism: per-device health from NVML critical events (e.g. uncorrectable ECC Xid 48/95, row-remap failure Xid 64) via ListAndWatch | 2 |
| Outcome: 8-GPU pod never placed there (Insufficient nvidia.com/gpu); follow-up is Chapter 16 repair, not a plugin restart | 1 |
