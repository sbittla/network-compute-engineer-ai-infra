# Marking scheme: 8.3 Where the QP parameters live

Type knowledge-check · kind written · tier L1 · 4 points

**Evidence required:** transitions named correctly; one-sentence troubleshooting implication.

| Criterion | Points |
|---|---|
| (a) Path MTU and destination GID / source GID index set at INIT→RTR | 2 |
| (b) timeout and retry_cnt set at RTR→RTS | 1 |
| Implication: a QP can reach RTS and pass small tests with a wrong MTU or marginal timeout; check the printed values, not 'it connected' | 1 |
