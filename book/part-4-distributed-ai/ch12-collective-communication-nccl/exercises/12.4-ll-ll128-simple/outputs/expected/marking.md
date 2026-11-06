# Marking scheme: 12.4 LL, LL128 and Simple protocols

Type knowledge-check · kind written · tier L1 · 6 points

**Evidence required:** a three-row comparison with the reason each costs what it costs.

| Criterion | Points |
|---|---|
| LL: ≈ 50 % payload (4 B data + 4 B flag per 8 B store), lowest latency, with mechanism | 2 |
| LL128: ≈ 94 % (120 of 128 B), low latency, needs 128-byte write ordering (NVLink-class) | 2 |
| Simple: ≈ 100 % payload, highest latency from fences and per-chunk synchronization | 2 |
