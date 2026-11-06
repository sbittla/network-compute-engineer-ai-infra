# Marking scheme: 10.M4 Physical-layer runbook and port/cabling schedule

Type deliverable · kind lab · tier L1 · 100 points

**Evidence required:** the CSV (row count = 256, unique IDs) and the runbook; the runbook must cite which thresholds are `[ILLUSTRATIVE]` policy and which come from a specification.

| Criterion | Points |
|---|---|
| Schedule: 256 rows, unique cable IDs and endpoints, 8 links per leaf–spine pair, labels name both ends, lengths from a stated layout | 40 |
| Runbook: signal → threshold → first safe action → escalation table (BER warn 10⁻⁵, critical 10⁻⁴) | 20 |
| Runbook: drain-before-touch for host links (scheduler node drain) and uplinks (routing-policy drain, then admin-down) | 20 |
| Runbook: commissioning gates and cleaning/inspection procedure (IEC 61300-3-35) | 10 |
| Runbook: sparing numbers (16 optics, 6 cables, 1 switch) with thresholds labelled policy vs specification | 10 |
