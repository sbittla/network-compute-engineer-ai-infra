# 10.K1 — Pipeline stage of each counter (★, L1)

**Type:** Knowledge check · **Kind:** written · **Points:** 6

## Prompt

<!-- prompt:start -->
**10.K1** Name the switch-ASIC pipeline stage (SerDes/PMD, PCS/FEC, MAC, traffic manager) at which
each counter is produced: (a) Rx optical power, (b) FEC-uncorrectable codewords, (c) FCS errors,
(d) output discards, (e) PFC pause frames sent, (f) oversize (giant) frames.
*Evidence required:* a six-row table: counter → stage → one-line justification.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 10 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md). Values are `[ILLUSTRATIVE]` unless labelled otherwise.
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the model answer and marking scheme in [outputs/expected/](outputs/expected/README.md); compare the reasoning and evidence, not the wording.

## What to submit

Put your deliverables in `outputs/` in this folder:

- `outputs/answer.md`: your answer, in the format the evidence line asks for

Answer in prose. Give any number you use with its unit and an evidence label (`[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`).
