# Marking scheme: 14.1 Little's law on NVMe

Type knowledge-check · kind computed · tier L1 · 5 points

**Evidence required:** the formula, substituted values, and results with units

| Criterion | Points |
|---|---|
| (a) IOPS = 1 / 95 µs = 10,526 IOPS and 43.1 MB/s (accept 41.1 MiB/s if labelled) | 2 |
| (b) QD = 330,000 /s x 0.097 ms = 32.0, formula shown | 2 |
| (c) %util counts time with at least one request outstanding; NVMe is parallel; saturation shows as latency rising at constant throughput | 1 |
