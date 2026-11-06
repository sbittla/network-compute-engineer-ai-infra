# Marking scheme: M1 SLI/SLO specification for ORION

Type outline-mandated · kind computed · tier L1 · 15 points

**Evidence required:** A table covering all four services; at least one PromQL recording rule per SLI; budget arithmetic; exclusions (e.g. client 4xx, user-code failures) stated.

| Criterion | Points |
|---|---|
| Table covering training completion/recovery, inference latency, cluster availability, fabric health with good/valid events, source, SLO, window, owner | 4 |
| At least one PromQL recording rule per SLI | 3 |
| Budget arithmetic shown (e.g. 99.5 % × 30 d → 216 min) and targets derived from the canon (e^(−24/96) = 0.78; P(≤ 8) = 0.9989) | 4 |
| Burn-rate alert policy and exclusions (client 4xx, user-code failures, announced maintenance) stated; no component-metric SLIs | 4 |
