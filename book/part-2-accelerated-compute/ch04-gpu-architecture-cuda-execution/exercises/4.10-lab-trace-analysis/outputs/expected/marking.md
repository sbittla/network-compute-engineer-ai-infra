# Marking scheme: 4.10 Lab 4: trace analysis of a training step

Type hands-on-lab · kind lab · tier L1 · 100 points

**Evidence required:** checker output (all PASS), `report.md`, `analysis.md` per the lab rubric.

| Criterion | Points |
|---|---|
| Task 1: utilization and overlap checks pass; busy(any) vs busy(kernel) vs efficiency explained | 15 |
| Task 2: gap-attribution checks pass; each host_sync gap tied to its source construct (.item(), pageable copy) | 20 |
| Tasks 3-4: copy-table and occupancy checks pass; PCIe degradation ruled out with the pinned 48 GB/s evidence; one occupancy configuration worked by hand | 20 |
| Task 5: kernel-summary check passes; GEMM and flash-attention low occupancy judged by design | 10 |
| Task 6: findings check passes; five findings with savings in ms per step; report.md generated | 15 |
| Task 7: analysis.md with annotated timeline, ranked fixes, projected step time 63-65 ms with basis, validation plan with repeated runs, limitations | 20 |
