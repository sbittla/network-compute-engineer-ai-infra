# 17-W1 · Gang feasibility and cost (★★ · L1)

Type: worked-problem · Kind: computed · Points: 8

<!-- prompt:start -->
**17-W1** ★★ L1 — Gang feasibility and cost. A 12-node partition (HX8 nodes) has free GPUs per node
`[8, 8, 0, 4, 6, 2, 8, 3, 5, 8, 1, 7]` for nodes p01–p12. Node p07 is `draining`; all nodes have all
rails up.
1. What does a naive "free GPUs" panel show, and how many free GPUs are eligible?
2. What is the largest multi-node gang (whole nodes) that can start now?
3. A 4-node gang is submitted. What pending reason does the Chapter 17 policy give, and why?
4. Under best-fit, where does a 6-GPU single-node job go?
5. Without gang scheduling, two 3-node jobs arrive when exactly four whole nodes are free and are
   scheduled pod by pod, interleaved. How many GPUs are stranded, and what does it cost if it lasts
   5 h at the book's `[MODELED]` $3.00/GPU-hour (Chapter 21 TCO)?
6. A 128-GPU training job checkpoints every 45 min and takes 15 min (900 s) to restart. What does one
   preemption cost in GPU-hours on average?
*Evidence required:* every step as formula → substitution → result with units.
<!-- prompt:end -->

## What to submit

Write your working in `outputs/answer.md`: formula → substitution → result with units for every
part, with evidence labels. If you check it with a script, save it as `outputs/work.py` and run it
from this folder with `python outputs/work.py`.
