# Marking scheme: K4 Static, dynamic and continuous batching

Type knowledge-check · kind written · tier L1 · 4 points

**Evidence required:** one sentence per strategy, plus the interference mechanism in terms of iterations

| Criterion | Points |
|---|---|
| Static batching: fixed batch run to completion, early finishers idle | 1 |
| Dynamic batching: batch formed on size or timeout, still run to completion | 1 |
| Continuous batching: admit/retire at every iteration (Orca) | 1 |
| Interference: a new request's prefill occupies an iteration (or part, with chunking), so running sequences get no or slower tokens | 1 |
