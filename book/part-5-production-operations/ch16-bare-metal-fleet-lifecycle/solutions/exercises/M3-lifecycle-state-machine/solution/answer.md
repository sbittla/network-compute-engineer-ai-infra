# M3 — Lifecycle state machine

**Diagram:** Figure 16.1 (mermaid `stateDiagram-v2`), implemented by `transition_table()` in
`solutions/lab/fleet_lifecycle.py`.

| # | From → To | Event | Guard | Side effects |
|---|---|---|---|---|
| 1 | discovered → imaged | `image` | inventory complete (asset tag, serials) | PXE/iPXE image, record image ID |
| 2 | imaged → validated | `pass_acceptance` | verdict PASS, or WARN with waiver ID | store acceptance run ID, policy version |
| 3 | imaged → repair | `fail_acceptance` | ticket ID present | open/attach ticket |
| 4 | validated → schedulable | `enable` | firmware matches a production bundle | add to scheduler, remove lifecycle taint |
| 5 | validated → imaged | `reimage` | — | new image ID |
| 6 | schedulable → draining | `drain` | reason and category (`fault` / `maintenance`) | Slurm `DRAIN` / cordon |
| 7 | draining → schedulable | `cancel_drain` | category = maintenance | undrain / uncordon |
| 8 | draining → drained | `drain_complete` | running jobs = 0 | — |
| 9 | drained → repair | `send_to_repair` | ticket ID | evidence bundle captured |
| 10 | drained → imaged | `reimage` | — | upgrade / reprovision |
| 11 | drained → retired | `retire` | sanitization certificate ID | remove from CMDB, DNS, scheduler |
| 12 | repair → imaged | `reimage` | ticket closed | reconciler flags new serials |
| 13 | repair → retired | `retire` | sanitization certificate ID | as 11 |

(The lab also audits the self-transition `inventory_update`.) **Audit fields** on every *attempt*,
applied or rejected: `seq`, `ts`, `node`, `event`, `actor`, `from_state`, `to_state`, `result`,
`reason_code`, plus change/ticket/waiver/certificate IDs.

| Forbidden transition | Reason |
|---|---|
| `repair` / `imaged` → `schedulable` | Hardware or image not validated |
| `schedulable` → `repair` | Running jobs; must drain first |
| `draining` → `schedulable` for a *fault* drain | Fault unresolved; must go through repair |
| any edge out of `retired` | Terminal; media sanitized, asset gone |
| `discovered` → `validated` | No image, no acceptance |

**Replay evidence (36 events, 13 rejected) `[SIMULATED]`:** `JOBS_STILL_RUNNING` (n05),
`TICKET_OPEN` (n14), `ILLEGAL_TRANSITION` ×3 (n21 enable from imaged, n12 repair from schedulable,
n14 reimage after retire), `ACCEPTANCE_NOT_PASSED` (n21), `INVENTORY_INCOMPLETE` (n26), `FW_OFF_MATRIX`
(n29), `FAULT_DRAIN_REQUIRES_REPAIR` (n12), `MISSING_TICKET` (n12), `SANITIZATION_MISSING` (n14),
`MISSING_REASON` (n32), `UNKNOWN_NODE` (n40). The T3 checks verify the table shape, that guards
reject *and* audit, that replay does not mutate its input, the rejection list, the final states,
and the invariant that no path reaches `schedulable` except through `validated` or a cancelled
maintenance drain.

Source: Section 16.1, Figure 16.1, Section 16.11; lab Task 3.
