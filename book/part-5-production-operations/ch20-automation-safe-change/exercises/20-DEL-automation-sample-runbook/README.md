# 20-DEL — Automation sample and safe-change runbook (★★★, L1)

Type: Deliverable · Kind: `lab` · Points: 30

## Prompt

<!-- prompt:start -->
Submit:

1. **Automation sample**: your completed Lab 20 Parts 1–2 (the reconciler and rollout controller)
   or your Exercise 20-M1 validator, with a README explaining its safety defaults: dry run, cap,
   audit, and kill-switch hook.
2. **Safe-change runbook** for one ORION change type of your choice (NIC firmware, leaf QoS, or host
   MTU), following the structure of the runbook excerpt in the manuscript: before / during / after,
   signals and thresholds table, abort and rollback procedure, escalation, and audit bundle
   contents.

**Evidence required:** both artifacts; the runbook cites the lab's decision log or your Exercise
20-M2 design as its threshold source.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 20 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md). Values are ORION `[ILLUSTRATIVE]` unless stated.
- **Checking your work:** Run the lab checker as shown below; this exercise is done when the named checks pass. [outputs/expected/](outputs/expected/README.md) shows those check lines from a finished lab, plus a worked answer and the marking scheme.

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/automation/` (safe_change.py or validator.py, plus README.md)
- `outputs/runbook.md`

Run:

```bash
cd ../../lab && python check.py   # the p1.* and p2.* lines are the sample's test evidence
```
