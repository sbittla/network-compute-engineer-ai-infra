# 12.14 — Latency doubled, bandwidth fine (★★★, L1)

**Type:** Troubleshooting case · **Kind:** written · **Points:** 15

## Prompt

<!-- prompt:start -->
**12.14 ★★★ L1 — Latency doubled, bandwidth fine.** After a container image update, the nightly
8-node run shows: 8 B all-reduce time 95 µs (baseline 47 µs); 1 MiB time 118 µs (baseline 53 µs);
plateau busbw 344 GB/s (baseline 345). `#wrong` = 0. No node changes. Rank hypotheses, name
discriminating tests (with commands and the log lines you expect), give the most likely root cause, the
safe fix, and the validation evidence.
*Evidence required:* ≥ 3 ranked hypotheses, tests with expected outcomes, root cause, fix, and
validation criteria.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 12 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md); the lab data is in [lab/data/](../../lab/data/).
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the model answer and marking scheme in [outputs/expected/](outputs/expected/README.md); compare the reasoning and evidence, not the wording.

## What to submit

Put your deliverables in `outputs/` in this folder:

- `outputs/answer.md`: your answer, in the format the evidence line asks for

Answer in prose. Give any number you use with its unit and an evidence label (`[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`).
