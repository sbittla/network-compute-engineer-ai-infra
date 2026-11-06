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

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the lab snapshot in [lab/data/](../../lab/data/) (seed 17).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Write your working in `outputs/answer.md`: formula → substitution → result with units for every
part, with evidence labels. If you check it with a script, save it as `outputs/work.py` and run it
from this folder with `python outputs/work.py`.
Also save the edited queue as `outputs/job_queue_j01_p100.json` and the simulator output as
`outputs/simulator_output.txt`.

For part 4, "your simulator" is `lab/starter/orion_sched.py` once you have implemented it in Lab 17. It reads
all three snapshot files (`cluster_state.json`, `job_queue.json`, `pending_cases.json`) from the directory
given by `--data`, so copy the whole data directory and edit the copy, never `lab/data/` itself:

```bash
cd ../../lab
cp -r data ../exercises/17-W2-priority-vs-fair-share/replay_data
# in replay_data/job_queue.json, set J01's priority to 100
python starter/orion_sched.py --data ../exercises/17-W2-priority-vs-fair-share/replay_data > ../exercises/17-W2-priority-vs-fair-share/outputs/simulator_output.txt
cp ../exercises/17-W2-priority-vs-fair-share/replay_data/job_queue.json ../exercises/17-W2-priority-vs-fair-share/outputs/job_queue_j01_p100.json
```

Run `python starter/orion_sched.py` with no `--data` for the baseline that part 2 compares against.
