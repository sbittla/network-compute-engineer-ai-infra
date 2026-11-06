# Marking scheme: K7 Sharing a GPU across tenants

Type knowledge-check · kind written · tier L1 · 6 points

**Evidence required:** a 3 × 3 table

| Criterion | Points |
|---|---|
| Whole GPU row: full memory, fault and performance isolation | 1 |
| MIG row: hardware-partitioned memory, instance-level fault isolation with GPU-wide caveat, dedicated SM/bandwidth slices | 2 |
| Time-slicing row: separate address spaces but no capacity limit, no fault isolation, no performance isolation | 2 |
| Concludes time-slicing is never acceptable across tenants | 1 |
