# Recovery Runbook — Collective Hang on ORION-XL

> Template for Capstone G artifact 7. Every command carries its tier and whether it changes state.
> Lab or authorised production procedure only.

## 0. Signals that start this runbook
`<fill: watchdog timeouts, progress stall, critical Xid alert>`

## 1. First five minutes
`<fill: numbered steps — freeze automation retries? capture evidence; find lowest collective seq; map rank → device>`

## 2. Classify
`<fill: decision table: critical GPU evidence on the stalled rank → proven cause; other ≥ threshold → independent>`

## 3. Contain
`<fill: quarantine + drain commands (e.g. scontrol update NodeName=<node> State=DRAIN Reason="<ticket>"); Fabric ticket>`

## 4. Recover
`<fill: select checkpoint; build restart plan from eligible spares; submit; watch first steps>`

## 5. Validate and close
`<fill: resume validation; metrics; postmortem trigger>`

## 6. Escalation
| Situation | Team | Within |
|---|---|---|
| `<fill>` | `<fill: Training Infra / Fleet / Fabric / SRE>` | `<fill>` |
