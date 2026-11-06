# Marking scheme: 11.10 Choose a parallelism for three constraints

Type outline-mandated · kind computed · tier L1 · 15 points

**Evidence required:** for each case, the chosen (TP, PP, DP, CP, ZeRO stage), a memory estimate showing it fits, the dominant traffic with bytes per GPU per step, and which ORION links carry it.

| Criterion | Points |
|---|---|
| (a) DP = 64 (DDP/ZeRO-1): memory ≈ 38 GB shown; 2.6 GB gradient all-reduce over NVLink + all 8 rails | 5 |
| (b) TP 8/PP 4/DP 2 + ZeRO-1 (or an equivalent): 37.3 GB shown; TP 1.2 TB on NVLink, DP 4.4 GB and PP 2.15 GB on the rail | 5 |
| (c) TP 8/PP 4/DP 1 with full recompute (or TP + CP): selective 182 GB impossible, full ≈ 50 GB; TP ≈ 4.8–7.2 TB on NVLink, PP 8.6 GB on the rail | 5 |
