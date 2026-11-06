# Marking scheme: 6.14 12 % faster kernel, unchanged step time

Type troubleshooting · kind computed · tier L1 · 10 points

**Evidence required:** mechanisms, Amdahl arithmetic, experiment design.

| Criterion | Points |
|---|---|
| At least three mechanisms (Amdahl, shape mismatch/L2 residency, fusion in production, one-process measurement, clocks) | 4 |
| Amdahl arithmetic: 0.04 × 0.12 = 0.48 % (or 0.43 % for a 1.12× throughput reading), below the noise floor | 3 |
| Experiment design: production profile for share and shapes, production-shape benchmark with full protocol, Amdahl prediction vs noise floor | 3 |
