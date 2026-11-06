# 11.10 — Choose a parallelism for three constraints (★★, L1)

**Type:** Outline-mandated · **Kind:** computed · **Points:** 15

## Prompt

<!-- prompt:start -->
**11.10 (O1) ★★ L1 — Choose a parallelism for three constraints.** For each workload, choose data,
tensor, pipeline (or a combination, with ZeRO if needed) on ORION and explain the communication
implications (collective, volume per step, link used):

- (a) a 1.3B-parameter model, sequence 2,048, global batch 512, 64 GPUs;
- (b) W-TRAIN at sequence 4,096 but restricted to 64 GPUs (8 nodes) with global batch 256;
- (c) a 70B model fine-tuned at sequence 65,536 on 32 GPUs, global batch 32.

*Evidence required:* for each case, the chosen (TP, PP, DP, CP, ZeRO stage), a memory estimate showing
it fits, the dominant traffic with bytes per GPU per step, and which ORION links carry it.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) with W-TRAIN on ORION-256 and the assumptions in Table 11.4.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put your deliverables in `outputs/` in this folder:

- `outputs/answer.md`: formula → substitution → result with units, each number labelled `[MODELED]`
- `outputs/work.py`: optional: a script that reproduces your numbers

Show every formula, substitution and result with units, and label each number with its evidence label.
