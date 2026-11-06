# Marking scheme: 11.18 Why "fits in 80 GB" is not enough

Type reflection · kind written · tier L1 · 3 points

**Evidence required:** Not stated in exercises.md; marked against the criteria below.

| Criterion | Points |
|---|---|
| Explains peak vs steady allocation and fragmentation | 1 |
| Names other code paths/changes that raise memory (eval, checkpoint, longer sequences, batch changes) | 1 |
| Requires concrete evidence: allocator peak stats over ≥ 200 steps incl. eval and checkpoint, with ≥ 15 % headroom | 1 |
