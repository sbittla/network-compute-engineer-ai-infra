# Capstone E Design Document — `<fill: title>`

> The nine sections every capstone must contain (outline Section 16). ≤ 15 pages. Every number
> carries an evidence label; state the tier of every result.

**Author:** `<fill>` · **Date:** `<fill>` · **Tier(s):** `<fill: L1 / L2 / L3>` · **Repository/commit:** `<fill>`

## 1. Problem statement
`<fill: the decision/system you deliver, for whom, constraints, success criteria (measurable)>`

## 2. Architecture
`<fill: control-plane diagram (captioned), component responsibilities, data flows, ownership boundaries between provisioner, controller, scheduler and audit store>`

## 3. Assumptions register

| ID | Assumption | Label | Impact if wrong | How to validate |
|---|---|---|---|---|
| A1 | Fleet is ORION-256 + 8-node expansion (stated variation) | ILLUSTRATIVE | `<fill>` | `<fill>` |
| A2 | Capacity floors during maintenance: training ≥ 16 nodes (DP 4), inference ≥ 6 nodes | ILLUSTRATIVE | `<fill>` | `<fill>` |
| A3 | `<fill>` | | | |

## 4. Implementation or simulation boundary
`<fill: what is real code, what is simulated input, what is out of scope; table of claim → tier>`

## 5. Test plan
`<fill: checker tests, your own extra tests (property tests, adversarial event streams), and L2/L3 tests if any>`

## 6. Results
`<fill: link to results-table.md; checker output; acceptance outcomes; wave plan; canary decisions; audit verification>`

## 7. Failure analysis
`<fill: for each planted fault — what it is, how it was caught, what would have happened downstream if it was not; plus at least two failure modes of your own controller (crash mid-transition, split-brain, clock skew) and mitigations>`

## 8. Security considerations
`<fill: BMC/OOB network isolation, credentials, firmware signing/supply chain, automation identity and least privilege, audit integrity, two-person rule for overrides>`

## 9. Final engineering review
`<fill: what you would ship now, what you would not, residual risks (≥ 3) with owners, next-step backlog in priority order>`
