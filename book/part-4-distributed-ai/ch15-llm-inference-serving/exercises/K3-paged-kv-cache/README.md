# K3 — Paged KV cache (★, L1)

Type: knowledge-check · Kind: written

## Prompt

<!-- prompt:start -->
**K3. ★ L1 — Paged KV cache.** What problem does PagedAttention solve, and what new failure mode
does on-demand block allocation introduce?
*Evidence required:* the fragmentation/over-reservation mechanism, and preemption (recompute or
swap) with its cost.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 15 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) (W-INFER for serving questions).
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the model answer and marking scheme in [outputs/expected/](outputs/expected/README.md); compare the reasoning and evidence, not the wording.

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
