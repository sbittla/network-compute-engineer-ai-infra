# Marking scheme: O1 Investigate an end-to-end workload regression

Type outline-mandated · kind computed · tier L1 · 15 points

**Evidence required:** checker output; a corroboration table (cause × direct evidence × values); interaction coefficients with a one-sentence judgment.

| Criterion | Points |
|---|---|
| (a) lab tasks 1–7 passing in the checker | 3 |
| (b) corroboration table: one direct measurement per cause with numbers (backend tx, data wait/iowait, bounce copy/channel lines, ECC SBE) | 5 |
| (c) tp_x_storage -1.30 ± 0.15 s and tp_x_driver +0.03 ± 0.13 s reported | 4 |
| (c) judgment: keep tp_x_storage, drop tp_x_driver; additive-only model not defensible | 3 |
