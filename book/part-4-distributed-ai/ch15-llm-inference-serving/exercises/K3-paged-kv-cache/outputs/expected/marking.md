# Marking scheme: K3 Paged KV cache

Type knowledge-check · kind written · tier L1 · 4 points

**Evidence required:** the fragmentation/over-reservation mechanism, and preemption (recompute or swap) with its cost

| Criterion | Points |
|---|---|
| Mechanism: contiguous max-length reservation wastes memory (over-reservation, fragmentation; ≈ 20-40 % used in prior systems) | 2 |
| New failure mode: pool runs out while sequences decode, so the scheduler must preempt | 1 |
| Recompute vs swap cost (re-prefill on GPU vs PCIe copy to host); repeated preemption is a storm | 1 |
