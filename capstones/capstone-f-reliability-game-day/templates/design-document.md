# Capstone F Design Document — `<fill: title>`

> The nine sections every capstone must contain (outline Section 16). ≤ 15 pages. Every number
> carries an evidence label; state the tier of every result.

**Author:** `<fill>` · **Date:** `<fill>` · **Tier(s):** `<fill: L1 / L2 / L3>` · **Repository/commit:** `<fill>`

## 1. Problem statement
`<fill: what the game day must prove or disprove, for whom, constraints (safety scope), measurable success criteria>`

## 2. Architecture
`<fill: system-under-test diagram (captioned): signals, alerting, health controller, scheduler, checkpoint path; who owns each recovery step>`

## 3. Assumptions register

| ID | Assumption | Label | Impact if wrong | How to validate |
|---|---|---|---|---|
| A1 | Simulator parameters (collective timeout 600 s, drain after 60 s, launch + warm-up 280 s, storage 80/160 GB/s) | ILLUSTRATIVE | `<fill>` | `<fill>` |
| A2 | Protected inference partition is out of scope | ILLUSTRATIVE | `<fill>` | `<fill>` |
| A3 | `<fill>` | | | |

## 4. Implementation or simulation boundary
`<fill: what the simulator represents and what it does not (quote its docstring); which conclusions therefore transfer to a real cluster and which do not>`

## 5. Test plan
`<fill: checker tests, your scenarios and why, what-if re-runs, and any L2/L3 drills with abort and rollback>`

## 6. Results
`<fill: link to results-table.md; detection, recovery and lost GPU-hours; hypothesis verdicts; what-if results>`

## 7. Failure analysis
`<fill: for each refuted hypothesis — mechanism, evidence, consequence at production scale; plus failure modes of the game day itself (injection fails to roll back, monitoring blind spot) and mitigations>`

## 8. Security considerations
`<fill: who may run fault injection; credentials for BMC power control; audit of every injection; isolation of the lab from production; handling of logs and recordings>`

## 9. Final engineering review
`<fill: what you would change now, residual risks (≥ 3) with owners, the next game day's plan>`
