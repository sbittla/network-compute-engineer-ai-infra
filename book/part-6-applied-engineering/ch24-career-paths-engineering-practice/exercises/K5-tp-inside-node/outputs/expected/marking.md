# Marking scheme: K5 TP inside the node

Type knowledge-check · kind computed · tier L1 · 5 points

**Evidence required:** formula, substituted values, both times with units and labels.

| Criterion | Points |
|---|---|
| TP volume per GPU per step derived with arithmetic (67.1 MB → 117 MB → 1.20 TB) | 2 |
| Time over NVLink ≈ 3.3 s at 360 GB/s, labelled | 1 |
| Time over a NIC ≈ 30 s at 40 GB/s, labelled | 1 |
| Conclusion: NIC time exceeds the 17.4 s step, so TP stays in the NVLink domain | 1 |
