# Marking scheme: 12.14 Latency doubled, bandwidth fine

Type troubleshooting · kind written · tier L1 · 15 points

**Evidence required:** ≥ 3 ranked hypotheses, tests with expected outcomes, root cause, fix, and validation criteria.

| Criterion | Points |
|---|---|
| At least three ranked hypotheses, with algorithm/protocol restriction first and why it fits (latency up, plateau unchanged) | 4 |
| Discriminating tests with commands and expected log lines (INFO ENV/TUNING, env diff, unset rerun, affinity) | 4 |
| Root cause and safe fix under change control, with a guard against recurrence | 4 |
| Validation criteria (repeat launches, 8 B ≈ 47 ± 3 µs, plateau unchanged) | 3 |
