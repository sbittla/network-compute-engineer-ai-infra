# 17-M2 · ORION scheduling policy with replay evidence (★★★ · L1)

Type: outline-mandated · Kind: computed · Points: 15

<!-- prompt:start -->
**17-M2** ★★★ L1 — *Design a scheduling policy that considers GPU type, topology, quotas, queue
fairness, and gang placement* for ORION's training and inference pools. Specify: eligibility filters
and their order; GPU-type selection (labels/features); intra-node and multi-node topology rules;
quota model (hard, borrowing, overcommit ratio); priority classes and preemption asymmetry; fairness
key; gang mechanism; how small jobs are kept from fragmenting gang capacity; and the metrics that
prove the policy works. Validate one rule change by replaying the lab queue in your simulator.
*Evidence required:* a policy document (≤ 2 pages) and before/after simulator output for one rule.
<!-- prompt:end -->

## What to submit

Write your working in `outputs/answer.md`: formula → substitution → result with units for every
part, with evidence labels. If you check it with a script, save it as `outputs/work.py` and run it
from this folder with `python outputs/work.py`.
Save your before/after simulator output as `outputs/replay_before.txt` and `outputs/replay_after.txt`.
