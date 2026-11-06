# 11.11 — Step-time sensitivity (★★, L1)

**Type:** Outline-mandated · **Kind:** computed · **Points:** 12

## Prompt

<!-- prompt:start -->
**11.11 (O2) ★★ L1 — Step-time sensitivity.** Starting from the baseline breakdown
(compute 13.92 s, bubble 0.33 s, exposed TP 3.08 s, exposed DP 0.098 s, exposed PP 0.028 s), estimate
the new step time and MFU when: (a) kernel efficiency rises from 0.50 to 0.55; (b) TP overlap rises
from 25 % to 60 %; (c) one rank of 256 runs its compute 8 % slower (straggler; synchronization
overhead); (d) DP time triples because of fabric congestion; (e) both (b) and (c). Rank the levers.
*Evidence required:* five step times and MFUs with arithmetic, and the ranking with one sentence each.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 11 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) with W-TRAIN on ORION-256 and the assumptions in Table 11.4.
- **The baseline:** the W-TRAIN worked-example layout of Section 11.10 (candidate A in Table 11.5): TP = 8, PP = 4, DP = 8, micro-batch 1, ZeRO-1, selective recompute, on ORION-256. The breakdown in the prompt is that layout's Step 6 result (17.45 s, MFU 39.9 %).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put your deliverables in `outputs/` in this folder:

- `outputs/answer.md`: formula → substitution → result with units, each number labelled `[MODELED]`
- `outputs/work.py`: optional: a script that reproduces your numbers

Show every formula, substitution and result with units, and label each number with its evidence label.
