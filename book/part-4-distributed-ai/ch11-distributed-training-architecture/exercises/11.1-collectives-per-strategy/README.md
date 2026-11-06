# 11.1 — Collectives per strategy (★, L1)

**Type:** Knowledge check · **Kind:** written · **Points:** 6

## Prompt

<!-- prompt:start -->
**11.1 ★ L1 — Collectives per strategy.** For each of DDP, ZeRO-1, ZeRO-3/FSDP, Megatron TP with
sequence parallelism, pipeline parallelism, and expert parallelism, name the collective(s) used and how
often they run per optimizer step (per step, per micro-batch, per layer per micro-batch).
*Evidence required:* a six-row table with collective names and frequencies.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) with W-TRAIN on ORION-256 and the assumptions in Table 11.4.
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the model answer and marking scheme in [outputs/expected/](outputs/expected/README.md); compare the reasoning and evidence, not the wording.

## What to submit

Put your deliverables in `outputs/` in this folder:

- `outputs/answer.md`: your answer, in the format the evidence line asks for

Answer in prose. Give any number you use with its unit and an evidence label (`[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`).
