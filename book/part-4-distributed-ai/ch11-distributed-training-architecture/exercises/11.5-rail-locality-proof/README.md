# 11.5 — Rail locality of DP peers (★★, L1)

**Type:** Knowledge check · **Kind:** computed · **Points:** 3

## Prompt

<!-- prompt:start -->
**11.5 ★★ L1 — Rail locality.** With Megatron's TP-fastest rank order, TP = 8, and `torchrun
--nproc-per-node=8`, prove that every DP peer of global rank 19 is attached to rail leaf 3.
*Evidence required:* the rank arithmetic.
<!-- prompt:end -->

## What to submit

Put your deliverables in `outputs/` in this folder:

- `outputs/answer.md`: formula → substitution → result with units, each number labelled `[MODELED]`
- `outputs/work.py`: optional: a script that reproduces your numbers

Show every formula, substitution and result with units, and label each number with its evidence label.
