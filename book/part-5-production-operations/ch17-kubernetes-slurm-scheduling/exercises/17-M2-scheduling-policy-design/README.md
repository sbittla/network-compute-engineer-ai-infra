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

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the lab snapshot in [lab/data/](../../lab/data/) (seed 17).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Write the policy document (≤ 2 pages) in `outputs/answer.md`. Cover each item the prompt lists, in that
order, and state each rule so that someone could implement it. Give any number you use (quota, overcommit
ratio, threshold) with its source and an evidence label. End with the metrics that would show the policy
works.

Save your before/after simulator output as `outputs/replay_before.txt` and `outputs/replay_after.txt`.
"Your simulator" is `lab/starter/orion_sched.py` once you have implemented it in Lab 17. It reads all three
snapshot files (`cluster_state.json`, `job_queue.json`, `pending_cases.json`) from the directory given by
`--data`, so replay your rule change on a copy of the whole data directory, never on `lab/data/` itself:

```bash
cd ../../lab
python starter/orion_sched.py --data data > ../exercises/17-M2-scheduling-policy-design/outputs/replay_before.txt
cp -r data ../exercises/17-M2-scheduling-policy-design/replay_data
# edit replay_data/job_queue.json or replay_data/cluster_state.json to express the one rule change
python starter/orion_sched.py --data ../exercises/17-M2-scheduling-policy-design/replay_data > ../exercises/17-M2-scheduling-policy-design/outputs/replay_after.txt
```

If the rule change cannot be expressed in the data alone, change a copy of `orion_sched.py` instead and say
so in the policy document.
