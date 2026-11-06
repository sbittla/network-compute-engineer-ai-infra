# K2 · Why polling fails at 400 Gb/s (★ · L1)

Type: knowledge-check · Kind: computed · Points: 9

<!-- prompt:start -->
**K2 ★ L1 — Why polling fails at 400 Gb/s.** (a) How often does a 32-bit octet counter wrap at
400 Gb/s line rate? (b) What utilization does a 2 ms line-rate burst show when averaged over a 60 s
poll? (c) What is the maximum duration of a single PFC pause frame at 400 Gb/s?
*Evidence required:* each calculation with formula, substitution, and units.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare your method with the worked solution and marking scheme in the chapter's `solutions/exercises/K2-polling-at-400g/` (instructor material in the full repository; removed from student releases).

## What to submit

Write your working in `outputs/answer.md`: formula → substitution → result with units for every
part, with evidence labels. If you check it with a script, save it as `outputs/work.py` and run it
from this folder with `python outputs/work.py`.
