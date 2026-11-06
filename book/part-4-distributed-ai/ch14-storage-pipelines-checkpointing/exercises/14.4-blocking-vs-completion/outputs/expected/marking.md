# Marking scheme: 14.4 Blocking time versus completion latency

Type knowledge-check · kind written · tier L1 · 5 points

**Evidence required:** the expression τ/2 + L and a one-paragraph derivation

| Criterion | Points |
|---|---|
| Defines blocking time (training stalled: snapshot + coordination) | 1 |
| Defines completion latency L (snapshot start to commit durable) | 1 |
| Derivation: failure at uniform u; u ≥ L loses u, u < L (prob L/τ) loses u + τ; E = τ/2 + L | 2 |
| Explains blocking is a per-checkpoint overhead, not lost work on failure | 1 |
