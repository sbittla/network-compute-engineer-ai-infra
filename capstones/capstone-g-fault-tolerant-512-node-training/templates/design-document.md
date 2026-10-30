# Capstone G Design Document — `<fill: title>`

> The nine sections every capstone must contain (outline Section 16). **First line: state that the
> environment is SIMULATED** (or which tier you ran). ≤ 15 pages; every number labelled.

**Author:** `<fill>` · **Date:** `<fill>` · **Tier(s):** `<fill>` · **Repository/commit:** `<fill>`

## 1. Problem statement
`<fill>`

## 2. Architecture
`<fill: telemetry pipeline, correlation service, health DB, quarantine controller, checkpoint service, scheduler integration; captioned diagram>`

## 3. Assumptions register
| ID | Assumption | Label | Impact if wrong | How to validate |
|---|---|---|---|---|
| A1 | Job MTBF 3.2 h (node MTBF 1,536 h / 480) | ILLUSTRATIVE | `<fill>` | `<fill>` |
| A2 | Restart overhead ≈ 900 s | ILLUSTRATIVE | | |
| A3 | `<fill>` | | | |

## 4. Implementation or simulation boundary
`<fill>`

## 5. Test plan
`<fill>`

## 6. Results
`<fill: link results-table.md>`

## 7. Failure analysis
`<fill: including failure modes of the workflow itself — wrong clock offsets, stale inventory, automation retry loops>`

## 8. Security considerations
`<fill: who can quarantine/release devices, audit, protection of the health DB, access to BMC/switch credentials>`

## 9. Final engineering review
`<fill: residual risks with owners; backlog>`
