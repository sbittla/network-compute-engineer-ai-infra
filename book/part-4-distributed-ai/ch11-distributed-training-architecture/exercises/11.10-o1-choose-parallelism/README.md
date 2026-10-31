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

## What to submit

Put your deliverables in `outputs/` in this folder:

- `outputs/answer.md`: formula → substitution → result with units, each number labelled `[MODELED]`
- `outputs/work.py`: optional: a script that reproduces your numbers

Show every formula, substitution and result with units, and label each number with its evidence label.
