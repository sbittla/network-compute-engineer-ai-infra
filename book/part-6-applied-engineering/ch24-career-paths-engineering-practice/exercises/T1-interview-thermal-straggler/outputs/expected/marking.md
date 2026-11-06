# Marking scheme: T1 The interview troubleshooting round, version 2

Type troubleshooting · kind computed · tier L1 · 15 points

**Evidence required:** hypothesis table; discriminating test with expected outcomes; root-cause statement separated into proven and inferred; magnitude check with arithmetic; safe action; validation with repetitions; ECN hypothesis with its test.

| Criterion | Points |
|---|---|
| Hypothesis table (≥ 3) ranked by information value, cost and risk, with rationale | 4 |
| Discriminating tests with both expected outcomes | 3 |
| Root cause split into proven (SW thermal slowdown) and inferred (fan-tray trigger), plus magnitude check 13.5 × 1,830/1,585 ≈ +2.1 s | 3 |
| Safe change: drain and checkpoint restart with the job owner, Facilities inspects; no clock/power/QoS overrides | 2 |
| Validation with repetitions and the ECN-as-consequence hypothesis with its test | 3 |
