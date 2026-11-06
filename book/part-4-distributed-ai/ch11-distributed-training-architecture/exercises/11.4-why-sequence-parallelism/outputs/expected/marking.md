# Marking scheme: 11.4 Why sequence parallelism?

Type knowledge-check · kind computed · tier L1 · 3 points

**Evidence required:** two sentences naming the quantity and the factor.

| Criterion | Points |
|---|---|
| Names activation memory (the replicated LayerNorm/dropout activations) as the quantity reduced | 1 |
| Factor for TP = 8: (10 + 24/8)/(34/8) = 13/4.25 ≈ 3.1× | 1 |
| States why wire bytes are unchanged (all-reduce = reduce-scatter + all-gather) | 1 |
