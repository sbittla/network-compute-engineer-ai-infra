# Marking scheme: 20-T1 The plan that wanted to remove PFC

Type troubleshooting · kind written · tier L1 · 15 points

**Evidence required:** Ranked hypotheses with discriminating tests; root cause tied to specific log lines; fix, validation and guard.

| Criterion | Points |
|---|---|
| (a) three ranked hypotheses, each with a discriminating test; inventory truncation first | 5 |
| (b) root cause: inventory client ignores pagination (items=16 with next= page link) | 3 |
| (c) consequence on orion-n17-n32 and the Table 20.11 controls that stop it (sanity bound, plan size, cap, dry-run review) | 4 |
| (d) fix (follow pagination, fail closed), validation (0-action rerun, paginated test), new guard | 3 |
