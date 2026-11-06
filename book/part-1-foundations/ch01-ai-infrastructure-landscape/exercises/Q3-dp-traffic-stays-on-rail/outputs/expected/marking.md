# Marking scheme: Q3 Why DP all-reduces never cross a spine

Type knowledge-check · kind written · tier L1 · 3 points

**Evidence required:** The placement argument linking DP groups to rails.

| Criterion | Points |
|---|---|
| DP groups consist of GPUs with the same TP rank and pipeline stage, which have the same local GPU index | 1 |
| Same local index means the same rail, since NIC i serves GPU i on rail i | 1 |
| Rail leaf r connects NIC r of all 32 nodes, so the traffic stays on one leaf and never reaches a spine | 1 |
