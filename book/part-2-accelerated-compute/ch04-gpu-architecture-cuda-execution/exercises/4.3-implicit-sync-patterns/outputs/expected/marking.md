# Marking scheme: 4.3 Implicit host-device synchronization in PyTorch

Type knowledge-check · kind written · tier L1 · 4 points

**Evidence required:** four patterns, each with a one-line mechanism.

| Criterion | Points |
|---|---|
| Pattern 1 named with a correct mechanism (for example .item()/.cpu()/print: value copied D2H, CPU waits) | 1 |
| Pattern 2 named with a correct mechanism (for example Python control flow on a tensor value) | 1 |
| Pattern 3 named with a correct mechanism (for example data-dependent output shape: nonzero, x[mask], unique) | 1 |
| Pattern 4 named with a correct mechanism (for example pageable copy, torch.cuda.synchronize, empty_cache via cudaFree) | 1 |
