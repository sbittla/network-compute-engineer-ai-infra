# 12.2 — Why all-to-all is harder on the network (★, L1)

**Type:** Knowledge check · **Kind:** written · **Points:** 4

## Prompt

<!-- prompt:start -->
**12.2 ★ L1.** Why is all-to-all harder on a network than all-reduce of the same per-rank size, even
though each rank sends fewer bytes? *Evidence required:* two mechanisms (fan-out/incast, cross-rail
paths, data dependence).
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md); the lab data is in [lab/data/](../../lab/data/).
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the worked answer and marking scheme in the chapter's `solutions/exercises/12.2-why-all-to-all-is-harder/` (instructor material in the full repository; removed from student releases).

## What to submit

Put your deliverables in `outputs/` in this folder:

- `outputs/answer.md`: your answer, in the format the evidence line asks for

Answer in prose. Give any number you use with its unit and an evidence label (`[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`).
