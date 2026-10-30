# Fault-Injection Plan — `<fill: game-day name>`

> Template for Capstone F artifact 1. Approve this plan **before** the game day. Replace every
> `<fill: …>`.

| Field | Value |
|---|---|
| Environment | `<fill: SIMULATED ORION (cluster_sim.py) — or dedicated lab name>`; **never production or shared** |
| Date / window | `<fill>` |
| Game-day lead / safety officer | `<fill>` / `<fill>` |
| Protected scope (must not be touched) | `<fill: e.g. rack-08 inference partition>` |
| Communication channel | `<fill>` |
| Go / no-go criteria | `<fill: e.g. no real incident open; rollback rehearsed; monitoring healthy>` |

## Scenarios

| ID | Title | Fault(s): kind, target, start, duration | Overlap? | Blast radius | Abort conditions | Rollback (and how verified) |
|---|---|---|---|---|---|---|
| S1 | `<fill>` | `<fill>` | no | `<fill>` | `<fill>` | `<fill>` |
| S2 | `<fill>` | `<fill>` | `<fill>` | `<fill>` | `<fill>` | `<fill>` |
| … | | | | | | |

Coverage check: link_down `<fill: scenario IDs>` · node_loss `<fill>` · storage_slow `<fill>` ·
scheduler_outage `<fill>` · overlapping pair `<fill>`.

## Why these scenarios

`<fill: which failure interactions each scenario is designed to expose, ranked by expected learning value and risk>`

## Safety sign-off

`<fill: who approved, when; what would stop the game day immediately>`
