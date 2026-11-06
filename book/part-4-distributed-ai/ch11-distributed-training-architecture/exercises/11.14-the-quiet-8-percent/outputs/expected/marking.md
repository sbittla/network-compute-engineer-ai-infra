# Marking scheme: 11.14 The quiet 8 %

Type troubleshooting · kind computed · tier L1 · 10 points

**Evidence required:** ranked hypotheses (≥ 3), tests with expected outcomes, root cause, fix, validation criteria, and an estimate of GPU-hours lost per day.

| Criterion | Points |
|---|---|
| At least three ranked hypotheses, with ranks 96–103 mapped to orion-n13 (one TP group) | 2 |
| Discriminating tests with expected outcomes (clock-event reasons, power limit, peer comparison, token counts) | 3 |
| Root cause: power cap left by maintenance on orion-n13 | 1 |
| Safe fix (checkpoint, drain, Fleet restores policy under change control) and validation criteria | 2 |
| Loss estimate ≈ 435 GPU-h per day with arithmetic | 2 |
