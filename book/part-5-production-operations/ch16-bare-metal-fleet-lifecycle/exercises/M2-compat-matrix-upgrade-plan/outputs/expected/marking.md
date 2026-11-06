# Marking scheme: M2 Compatibility matrix and staged upgrade plan

Type outline-mandated · kind computed · tier L1 · 25 points

**Evidence required:** The extended matrix; the plan with every number derived; the rollback table; the abort-condition list; the evidence list.

| Criterion | Points |
|---|---|
| Extended matrix: fabric manager, CUDA user-mode, DCGM, container toolkit, NVMe fw, PSU fw with correct coupling rules | 6 |
| Plan numbers derived: canary detection probability, 8 waves, 195 h, 768 GPU-hours, replica-striping condition stated | 8 |
| Pre-declared abort conditions with thresholds | 4 |
| Per-component rollback table incl. at least one non-reversible component | 4 |
| Audit evidence list (change ID, before/after inventory read-back, acceptance run IDs, gate decisions, approvals) | 3 |
