# 12.5 — NCCL channels and 350 GB/s across two nodes (★★, L1)

**Type:** Knowledge check · **Kind:** written · **Points:** 4

## Prompt

<!-- prompt:start -->
**12.5 ★★ L1.** What is an NCCL channel, and why can a 16-rank all-reduce across two HX8 nodes reach
≈ 350 GB/s busbw when each NIC is 50 GB/s? *Evidence required:* explanation with the 8 × 50 GB/s
arithmetic.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 12 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md); the lab data is in [lab/data/](../../lab/data/).
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the model answer and marking scheme in [outputs/expected/](outputs/expected/README.md); compare the reasoning and evidence, not the wording.

## What to submit

Put your deliverables in `outputs/` in this folder:

- `outputs/answer.md`: your answer, in the format the evidence line asks for

Answer in prose. Give any number you use with its unit and an evidence label (`[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`).
