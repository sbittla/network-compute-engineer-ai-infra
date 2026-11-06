# 11.2 — Bytes per parameter (★, L1)

**Type:** Knowledge check · **Kind:** computed · **Points:** 5

## Prompt

<!-- prompt:start -->
**11.2 ★ L1 — Bytes per parameter.** Explain where each of the 16 bytes per parameter of BF16
mixed-precision Adam goes, and give the bytes per local parameter for ZeRO-1, ZeRO-2, and ZeRO-3 with
DP = 8. *Evidence required:* a breakdown and three numbers.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 11 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) with W-TRAIN on ORION-256 and the assumptions in Table 11.4.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put your deliverables in `outputs/` in this folder:

- `outputs/answer.md`: formula → substitution → result with units, each number labelled `[MODELED]`
- `outputs/work.py`: optional: a script that reproduces your numbers

Show every formula, substitution and result with units, and label each number with its evidence label.
