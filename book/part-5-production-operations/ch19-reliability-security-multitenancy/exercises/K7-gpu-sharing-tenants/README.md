# K7 — Sharing a GPU across tenants (★, L1)

Type: Knowledge check · Kind: `written` · Points: 6

## Prompt

<!-- prompt:start -->
**K7 ★ L1 — Sharing a GPU across tenants.** Compare whole-GPU, MIG, and time-slicing for two tenants on
one H100-class GPU: memory isolation, fault isolation, performance isolation.
*Evidence required:* a 3 × 3 table.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md); reliability uses node MTBF ≈ 1,536 node-hours, repair turnaround (MTTR) 5 days and restart overhead ≈ 15 min.
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the model answer and marking scheme in [outputs/expected/](outputs/expected/README.md); compare the reasoning and evidence, not the wording.

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/answer.md`
