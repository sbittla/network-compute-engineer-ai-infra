# M3 — Recovery and containment exercise (★★★, L1)

Type: Outline-mandated · Kind: `written` · Points: 20

## Prompt

<!-- prompt:start -->
**M3 ★★★ L1 — Recovery and containment exercise.** Design a recovery exercise that **tests fault
containment and validates that one tenant's failure does not disrupt another**: hypothesis, steady-state
SLIs, injection (dedicated lab partition only), abort criteria, observations, pass criteria, evidence.
*(Deliverable: recovery test plan.)*
*Evidence required:* complete plan per Section 19.10; at least three injections; explicit safety
controls; **and a tabletop run report** — walk the plan with the owning teams, record for each injection
the expected vs "discovered" behaviour, the gaps found, and the follow-up actions.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 19 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md); reliability uses node MTBF ≈ 1,536 node-hours, repair turnaround (MTTR) 5 days and restart overhead ≈ 15 min.
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the model answer and marking scheme in [outputs/expected/](outputs/expected/README.md); compare the reasoning and evidence, not the wording.

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/recovery_test_plan.md`
- `outputs/tabletop_report.md`
