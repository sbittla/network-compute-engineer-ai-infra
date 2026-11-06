# Exercise 3.2 — Since-boot samples

**Difficulty:** ★ · **Tier:** L1 · **Type:** knowledge-check · **Kind:** written · **Points:** 3

## Prompt

<!-- prompt:start -->
Explain why the first line of `vmstat 1 5` and the first report of `iostat -x 1 2` must be discarded.
Give one example where including them would hide a real problem.
*Evidence required:* a definition of what the first sample measures, plus a numeric example.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 3 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the model answer and marking scheme in [outputs/expected/](outputs/expected/README.md); compare the reasoning and evidence, not the wording.

## What to submit

Put every deliverable in [`outputs/`](outputs/):

- `outputs/answer.md`: your answer with the evidence the prompt requires

Answer in prose. Give any number you use with its unit and an evidence label (`[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`). Quote raw snapshot lines where you rely on them.
