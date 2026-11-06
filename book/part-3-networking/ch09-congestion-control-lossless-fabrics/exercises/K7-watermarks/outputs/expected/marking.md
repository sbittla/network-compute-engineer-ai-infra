# Marking scheme: K7 Instantaneous samples versus watermarks

Type knowledge-check · kind written · tier L1 · 3 points

**Evidence required:** explanation and the replacement metric.

| Criterion | Points |
|---|---|
| Explanation: 10 s instantaneous samples almost never catch microsecond bursts | 1 |
| ECN counters are cumulative and miss nothing, so there is no contradiction | 1 |
| Replacement metric: queue watermark (peak since last read) and ECN-mark rate | 1 |
