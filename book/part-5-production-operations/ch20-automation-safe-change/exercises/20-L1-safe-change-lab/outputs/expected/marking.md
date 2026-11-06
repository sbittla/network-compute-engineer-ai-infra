# Marking scheme: 20-L1 Lab 20: safe-change automation

Type hands-on-lab · kind lab · tier L1 · 100 points

**Evidence required:** check.py output with all checks PASS; the run_rollout decision log; written answers a-c (<= 1 page); L2/L3 manifest fields.

| Criterion | Points |
|---|---|
| Part 1: validation finds every planted defect, with a one-line RoCE-failure explanation of each (answer a) | 15 |
| Part 1: plan, dry-run, capped apply, audit trail and idempotency demonstrated (checker lines, second plan of size 0) | 20 |
| Part 2: correct decision log and explanation of the two traps a naive controller falls into (answer b) | 20 |
| Part 2: rollback set and justification of all_changed vs failing wave only (answer c) | 5 |
| Part 3: findings coverage and precision (checker) | 15 |
| Part 3: quality of fixes, specific numbers and ORION context (instructor-graded) | 10 |
| Safe-change runbook built from the lab outputs (shared with Exercise 20-DEL) | 15 |
