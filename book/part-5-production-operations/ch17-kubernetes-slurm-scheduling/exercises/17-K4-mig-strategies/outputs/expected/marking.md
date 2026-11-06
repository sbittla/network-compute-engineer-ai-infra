# Marking scheme: 17-K4 MIG mixed versus single strategy

Type knowledge-check · kind written · tier L1 · 5 points

**Evidence required:** Resource names and counts; the outcome under both strategies.

| Criterion | Points |
|---|---|
| mixed: advertises nvidia.com/mig-1g.10gb: 56 and nvidia.com/gpu: 0 | 2 |
| mixed outcome: nvidia.com/gpu: 1 pod stays Pending (Insufficient nvidia.com/gpu), lab case P07 | 1 |
| single: slices advertised as nvidia.com/gpu: 56; pod gets one 1g.10gb slice (≈ 10 GB), likely OOM if it expected 80 GB | 2 |
