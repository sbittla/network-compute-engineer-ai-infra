# Marking scheme: 12.11 Analyze an NCCL result set across message sizes

Type outline-mandated · kind computed · tier L1 · 12 points

**Evidence required:** a summary table (six rows), region boundaries, a log-log plot of time vs size for c2 and c5 (matplotlib), and a 150-word scaling verdict.

| Criterion | Points |
|---|---|
| Summary table: α, B, n½ and plateau for all six configurations | 4 |
| Region boundaries per configuration with thresholds stated | 2 |
| Log-log plot of c2 and c5 with labelled units | 2 |
| Scaling verdict: plateau flat 352 → 345 GB/s (86–88 % of egress), α +≈ 10 µs per doubling, n½ grows; c3/c6 anomalous | 4 |
