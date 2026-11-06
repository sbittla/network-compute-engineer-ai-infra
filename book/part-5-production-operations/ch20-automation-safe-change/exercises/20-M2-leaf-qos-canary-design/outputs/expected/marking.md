# Marking scheme: 20-M2 Canary rollout design for the leaf QoS profile

Type outline-mandated · kind written · tier L1 · 20 points

**Evidence required:** A 1-2 page design under the six headings; every threshold labelled [ILLUSTRATIVE] or derived from a stated baseline; explicit reasoning about rail independence.

| Criterion | Points |
|---|---|
| Prechecks: per-leaf and fabric-wide, exact signals, baselines and staged rollback config | 3 |
| Wave plan: one leaf canary, growth, bake >= 60 min under real load justified from Table 20.8 | 3 |
| Success criteria per rail vs own baseline median, with expected direction of ECN marks | 3 |
| At least four abort conditions with statistic, threshold and floor; hold for telemetry gaps | 3 |
| Rollback: mechanism, scope, rehearsal evidence, time bound | 3 |
| Audit evidence per leaf and per wave and where it is stored | 3 |
| Rail-independence reasoning (one leaf = one rail of every node; never two in the canary) | 2 |
