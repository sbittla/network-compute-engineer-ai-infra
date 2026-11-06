# Marking scheme: 8.13 RDMA readiness validator and perftest analyzer

Type hands-on-lab · kind lab · tier L1 · 100 points

**Evidence required:** `python check.py` output showing all checks PASS; the report; a diagnosis for each flagged perftest pair with mechanism, evidence, and next discriminating test, stating that the data are `[SIMULATED]`.

| Criterion | Points |
|---|---|
| Task 1 parsers: all parser checks pass | 20 |
| Tasks 2–3 readiness logic: all planted faults, no false positives, correct verdicts | 25 |
| Task 4 report: readable, evidence per finding, sorted, actionable | 10 |
| Tasks 5–7 perftest analysis and PCIe correlation | 20 |
| Task 8 diagnosis: mechanism per flagged pair, evidence cited, next discriminating test, [SIMULATED] stated | 20 |
| Code quality: type hints, docstrings with units, no hard-coded answers | 5 |
