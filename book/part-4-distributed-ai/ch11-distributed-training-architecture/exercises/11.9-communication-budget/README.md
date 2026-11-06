# 11.9 — Communication budget (★★, L1)

**Type:** Worked problem · **Kind:** computed · **Points:** 6

## Prompt

<!-- prompt:start -->
**11.9 ★★ L1 — Communication budget.** For the baseline, compute per-GPU bytes per step for TP, DP,
and PP, convert each to time with Table 11.4, and say which one you would attack first and why.
Then repeat the TP number for TP = 2 and explain the (t − 1) identity.
*Evidence required:* three volumes, three times, the TP = 2 result, and a one-sentence priority.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 11 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) with W-TRAIN on ORION-256 and the assumptions in Table 11.4.
- **The baseline:** the W-TRAIN worked-example layout of Section 11.10 (candidate A in Table 11.5): TP = 8, PP = 4, DP = 8, micro-batch 1, ZeRO-1, selective recompute, on ORION-256.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put your deliverables in `outputs/` in this folder:

- `outputs/answer.md`: formula → substitution → result with units, each number labelled `[MODELED]`
- `outputs/work.py`: optional: a script that reproduces your numbers

Show every formula, substitution and result with units, and label each number with its evidence label.
