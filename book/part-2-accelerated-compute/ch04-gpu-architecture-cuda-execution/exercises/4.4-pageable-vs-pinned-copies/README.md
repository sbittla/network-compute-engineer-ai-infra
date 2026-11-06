# Exercise 4.4 — Pageable versus pinned cudaMemcpyAsync

★ · Tier L1 · knowledge check · kind: `written`

<!-- prompt:start -->
**4.4** ★ L1 — Explain three distinct reasons a `cudaMemcpyAsync` from pageable memory is worse than
one from pinned memory.
*Evidence required:* bandwidth, host-blocking and overlap arguments.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 4 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the Table 4.1 (H100-SXM-class) values.
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the model answer and marking scheme in [outputs/expected/](outputs/expected/README.md); compare the reasoning and evidence, not the wording.

## What to submit

Put every deliverable in `outputs/`:

- `outputs/answer.md` — your answer, written to the evidence requirement above
