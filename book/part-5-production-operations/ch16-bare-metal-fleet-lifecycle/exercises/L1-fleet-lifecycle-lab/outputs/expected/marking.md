# Marking scheme: L1 Fleet lifecycle automation lab

Type hands-on-lab · kind lab · tier L1 · 100 points

**Evidence required:** `python lab/check.py` output showing 37/37 PASS; your `acceptance_report.md` listing every non-PASS node with codes, the raw evidence values that triggered them, and the remediation; the list of rejected lifecycle events with reason codes.

| Criterion | Points |
|---|---|
| Task 1 check_compat: all T1 checks pass | 15 |
| Task 2 evaluate_node: all T2 checks pass, policy-driven, no magic numbers | 35 |
| Task 3 state machine: all T3 checks pass, guards in one place, audit complete | 25 |
| Task 4 planner: all T4 checks pass | 15 |
| Task 5 report: correct physical cause and remediation for each non-PASS node; guard explanations | 10 |
