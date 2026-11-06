# Marking scheme: LAB Workload-characterization lab

Type hands-on-lab · kind lab · tier L1 · 100 points

**Evidence required:** check.py output showing 9/9 PASS; the generated comparison Markdown; the data-quality note (one line per rejected or flagged row with the root-cause hypothesis for the flaw).

| Criterion | Points |
|---|---|
| Task 1, validation and unit normalization (checks validation_issues and unit_normalization) | 20 |
| Task 2, resource lower bounds (checks resource_times_core, resource_times_io, w01_worked_example) | 20 |
| Task 3, classification and flags (checks classification and flags) | 20 |
| Task 4, one-page W01 vs W02 comparison, correct, at most 600 words, meaningful evidence section | 15 |
| Task 5, data-quality note covering all nine flawed rows with a plausible cause and an owner | 20 |
| Code quality, type hints, docstrings with units, no hard-coded workload IDs in logic | 5 |
