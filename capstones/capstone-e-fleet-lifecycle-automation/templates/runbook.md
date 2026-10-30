# Fleet Lifecycle Runbook — ORION

> Template for Capstone E artifact 7. Write for an on-call engineer who did not build the system.
> Every command carries its tier (L1/L2/L3) and whether it is read-only or state-changing.

## 0. Signals and thresholds

| Signal | Source | Threshold | Severity | Procedure |
|---|---|---|---|---|
| Node stuck in `imaged` | controller metric | > `<fill>` h | SEV4 | §2 |
| Acceptance failure rate in a batch | acceptance runner | > `<fill>` % | SEV3 | §2 |
| Canary gate = abort | rollout planner | any | SEV3 | §4 |
| Audit verification failure | Security verifier | any | SEV2 | §5 |
| Node schedulable on non-golden bundle | drift detector | any | SEV3 | §3 |
| `<fill>` | | | | |

## 1. Admit a node

`<fill: numbered steps; expected output at each step; what to do if the admit guard rejects>`

## 2. Investigate an acceptance failure

`<fill: decision tree by failing test name; first command to run; who owns the fix>`

## 3. Drift: node on a blocked or unknown stack

`<fill: drain at a safe boundary → reimage → re-accept; how to confirm jobs were not harmed>`

## 4. Rollout abort and rollback

`<fill: stop further waves; roll back the canary; verify; communicate>`

## 5. Audit verification failure

`<fill: freeze automation writes? preserve evidence; escalate to Security; do NOT "fix" the record>`

## 6. Escalation

| Situation | Escalate to | Within |
|---|---|---|
| `<fill>` | `<fill: Fleet / Platform / Fabric / Security>` | `<fill>` |

## 7. Safety rules

`<fill: what an on-call engineer must never do (e.g. hand-edit inventory, undrain a node on a blocked bundle, flash firmware outside a change ticket)>`
