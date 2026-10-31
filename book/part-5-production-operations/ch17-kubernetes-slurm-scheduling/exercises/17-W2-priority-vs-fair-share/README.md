# 17-W2 · Priority versus fair share on the Monday queue (★★★ · L1)

Type: worked-problem · Kind: computed · Points: 10

<!-- prompt:start -->
**17-W2** ★★★ L1 — Priority versus fair share on the Monday queue. In the lab snapshot, J01
(pretrain, 32 GPUs) is pending with `InsufficientCapacity` (manuscript Table 17.7). The pretraining
lead proposes raising J01 to priority 100.
1. Predict, by hand, the new placement for J01, J05, and J08 and the reason for each that does not
   start. (Hint: J01 and J05 are both pretrain at priority 100; which tie-breaker decides?)
2. Compare total GPUs placed and per-tenant GPUs placed with the baseline.
3. Identify the unintended consequence and propose a better policy (for example, a gang reservation
   or a separate QOS for urgent evaluations). Justify it with numbers from the snapshot.
4. Verify your prediction by editing a *copy* of `job_queue.json` and running your simulator.
*Evidence required:* the predicted table, the simulator output, the comparison, and the policy.
<!-- prompt:end -->

## What to submit

Write your working in `outputs/answer.md`: formula → substitution → result with units for every
part, with evidence labels. If you check it with a script, save it as `outputs/work.py` and run it
from this folder with `python outputs/work.py`.
Also save the edited queue as `outputs/job_queue_j01_p100.json` and the simulator output as
`outputs/simulator_output.txt`.
