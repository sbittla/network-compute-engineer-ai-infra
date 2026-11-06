# 17-DEL · Workload placement policy and scheduling troubleshooting guide (★★★ · L1)

Type: deliverable · Kind: written · Points: 100

<!-- prompt:start -->
**17-DEL** — *Workload placement policy and scheduling troubleshooting guide.* Submit the policy from
17-M2 and the guide from 17-M3 as one document, with the lab's `placement-report.md` as an appendix.
*Evidence required:* the document, the lab checker output (`10/10`), and the replay evidence from 17-M2.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 17 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the lab snapshot in [lab/data/](../../lab/data/) (seed 17).
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the model answer and marking scheme in [outputs/expected/](outputs/expected/README.md); compare the reasoning and evidence, not the wording.

## What to submit

Put these files in `outputs/`:

- `placement_policy_and_guide.md` — the 17-M2 policy and the 17-M3 guide as one document
- `placement-report.md` — from the lab (appendix)
- `check_output.txt` — `cd lab && python check.py` (must show `10/10`)
- `replay_before.txt`, `replay_after.txt` — the 17-M2 replay evidence

This deliverable builds on two earlier exercises. Do [17-M2](../17-M2-scheduling-policy-design/) first (its
README shows how to produce the replay files) and [17-M3](../17-M3-pending-troubleshooting-guide/), then copy
their outputs here. The lab itself is [Lab 17](../../lab/README.md).
