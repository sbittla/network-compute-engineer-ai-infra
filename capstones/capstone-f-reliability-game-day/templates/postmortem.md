# Blameless Postmortem — `<fill: title>`

> Template for Capstone F artifact 6 (Chapter 18). Describe systems and decisions, not people.
> Replace every `<fill: …>`.

| Field | Value |
|---|---|
| Severity | `<fill: SEV1–SEV4 and why>` |
| Date / duration | `<fill>` |
| Environment | `<fill: SIMULATED ORION game day / dedicated lab>` |
| Authors / reviewers | `<fill>` |
| Status | `<fill: draft / reviewed / actions tracked>` |

## Summary
`<fill: 3–5 sentences: what happened, impact in GPU-hours and job time, how it ended>`

## Impact
`<fill: lost GPU-hours (by fault), jobs affected, SLOs affected, whether impact is a lower bound (unrecovered at horizon)>`

## Timeline
`<fill: link to incident-timeline.md; reproduce the 8–12 most important rows>`

## Contributing factors
`<fill: systemic factors with the evidence rows that show each — e.g. no absence alert for the scheduler; checkpoint durability not visible; spare pool sized for one failure; repaired nodes not returned automatically>`

## What went well
`<fill>`

## Where we got lucky
`<fill>`

## Action items

| ID | Action | Type (detect / mitigate / prevent / process) | Owner (team) | Priority | Backlog ID | Validation (how we will know it worked) |
|---|---|---|---|---|---|---|
| `<fill>` | `<fill>` | `<fill>` | `<fill>` | `<fill>` | `<fill>` | `<fill>` |

## Lessons for the next game day
`<fill>`
