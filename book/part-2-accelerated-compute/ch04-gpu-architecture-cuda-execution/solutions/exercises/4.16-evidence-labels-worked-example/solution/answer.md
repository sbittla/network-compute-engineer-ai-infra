# 4.16 — Evidence labels in the worked example (model answer)

Relies on manuscript Section 4.12 (worked example, Table 4.11) and the book's evidence-label rules.

**`[SIMULATED]`:** everything read from the seeded Lab 4 capture: the 85.57 ms step window, busy fractions
(88.8 % any, 78.6 % kernel), gap counts and totals (15 `host_sync` = 4.91 ms, 600 `launch_bound` = 4.02 ms,
1 `dependency` = 0.31 ms), copy bandwidths (12.19 GB/s pageable, ≈ 48 GB/s pinned) and the achieved roof
fractions (GEMMs ≈ 62 %, layernorm backward ≈ 22 %).

**`[MODELED]`:** values computed from a model rather than observed: theoretical occupancy (12.5 %, 18.75 %),
the 80 %-of-roof target for the fixed layernorm, every per-finding saving (8.77, 5.30, 5.55, 2.43, 0.31 ms)
and the 63.2 ms projection (1.35×).

**To make 63 ms `[MEASURED]`:** apply the changes one at a time on real ORION hardware; record a manifest
(GPU, driver, CUDA, PyTorch, clocks, node); capture with nsys to confirm each mechanism; measure step time
over ≥ 5 independent runs with warm-up discarded and report median and IQR, against a baseline measured the
same way.

(≈ 130 words.)
