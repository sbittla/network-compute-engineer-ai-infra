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

## What to submit

Put your deliverables in `outputs/` in this folder:

- `outputs/answer.md`: formula → substitution → result with units, each number labelled `[MODELED]`
- `outputs/work.py`: optional: a script that reproduces your numbers

Show every formula, substitution and result with units, and label each number with its evidence label.
