# 20-D1 — Drift policy and break-glass for the ORION fabric (★★★, L1)

Type: Design challenge · Kind: `written` · Points: 15

## Prompt

<!-- prompt:start -->
Platform and Fabric disagree. Fabric wants the GitOps controller to **auto-revert** any drift on
leaf QoS and MTU within 5 minutes. Platform wants **alert-only**, because on-call engineers
sometimes need to hand-tune ECN thresholds during incidents. Propose a policy covering which fields
auto-revert, which alert, how break-glass works (who, how long, how recorded, how it expires), and
how you prevent the fighting-writers failure of Section 20.13. Defend it with at least two failure
scenarios.

**Evidence required:** a policy table (field class × behaviour × rationale), a break-glass
procedure, and two scenario walk-throughs showing the policy's behaviour.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md). Values are ORION `[ILLUSTRATIVE]` unless stated.
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the model answer and marking scheme in [outputs/expected/](outputs/expected/README.md); compare the reasoning and evidence, not the wording.

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/policy.md` (table, break-glass procedure, two scenarios)
