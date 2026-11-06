# Marking scheme: L1 Lab 19: ORION-XL incident

Type hands-on-lab · kind lab · tier L1 · 100 points

**Evidence required:** 12/12 PASS; incident_packet.md per lab README Section 8

| Criterion | Points |
|---|---|
| Checker Tasks 1–2 pass and a failure timeline 01:12 → 04:31 built from the events | 15 |
| Rank-to-hardware table for every implicated rank (rank, node, GPU UUID, BDF, NUMA, HCA, rail, leaf port) | 10 |
| Task 3 passes and a proven-vs-correlated table citing timing, locality and mechanism; H1 proven pending intervention | 20 |
| Health decision and quarantine per component: smallest defensible fault domain and scheduling unit removed | 15 |
| Safe restart plan: ckpt-0084, restore validation, spares s01/s03, rank remap, pre/post checks, retry policy | 15 |
| Recovery metrics for both attempts (RPO, RTO, lost GPU-h) and the cost of the first auto-restart | 5 |
| Risk register: top-5 risks with corrected scores, owners, mitigations | 10 |
| Isolation model with remediation for all 11 violations | 10 |
