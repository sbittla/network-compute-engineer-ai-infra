# Marking scheme: 14.12 The resume that trained worse

Type troubleshooting · kind computed · tier L1 · 15 points

**Evidence required:** hypothesis table, the recovery decision with arithmetic, and the two changes mapped to Section 14.10

| Criterion | Points |
|---|---|
| Symptom stated and hypothesis table with at least three hypotheses and discriminating evidence | 5 |
| Root cause: latest advanced at snapshot time and restart trusted it; persist of 88327 interrupted; 31 warnings explained | 3 |
| Recovery: stop, validate, restore step_088290; cost 512 + 45.8 + 57.5 ≈ 615 GPU-h with arithmetic | 4 |
| Two prevention changes mapped to Section 14.10 (latest after commit + validation; semantic loss check) | 3 |
