# Marking scheme: 20-M3 Review a deliberately unsafe change plan

Type outline-mandated · kind lab · tier L1 · 20 points

**Evidence required:** findings.yaml passing the three Part 3 checks; a rewritten plan (<= 2 pages) addressing every finding with wave plan, abort conditions and rollback.

| Criterion | Points |
|---|---|
| Checker: p3.review_coverage PASS (>= 13 of 17 real gaps) | 4 |
| Checker: p3.review_false_positives PASS (<= 1; owner, approval, comms are not gaps) | 3 |
| Checker: p3.review_evidence_quality PASS (valid line citations, concrete fixes) | 3 |
| Rewrite splits the work into three ordered changes (firmware, leaf QoS, RDMA MTU) | 4 |
| Each change has prechecks, drain, waves, abort conditions, rehearsed rollback, OOB access, kill switch, staffed window | 6 |
