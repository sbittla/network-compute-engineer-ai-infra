# Marking scheme: 2.3 Simplified capacity model

Type outline-mandated · kind computed · tier L1 · 20 points

**Evidence required:** The model file or table with formulas visible; every output labelled [MODELED]; a three-sentence interpretation.

| Criterion | Points |
|---|---|
| Item 1, 128 GPUs, 10,240 GB total and 9,216 GB usable HBM, 26.0 GB training state per GPU that fits in 72 GB | 3 |
| Item 2, 80 GB/s read and 40 GB/s write, 0.625 GB/s read per GPU, 182 GB checkpoint written in at least 4.55 s | 3 |
| Items 3 and 4, 25.6 Tb/s bisection; 181.9 kW IT maximum and 236.5 kW facility power | 6 |
| Item 5, 897,024 allocated GPU-hours per year and 0.28 durable fraction of peak | 3 |
| Item 6 and interpretation, GPU memory binds first if the model doubles (52 GB of 72 GB), argued with numbers | 5 |
