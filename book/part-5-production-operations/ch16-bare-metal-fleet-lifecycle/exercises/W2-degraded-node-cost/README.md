# W2 · What a degraded node costs W-TRAIN (★★ · L1)

Type: worked-problem · Kind: computed · Points: 15

<!-- prompt:start -->
**W2 ★★ (L1) — What a degraded node costs.** W-TRAIN on ORION (step 17.4 s at 40 % MFU, TP 8, PP 4,
DP 8). (a) One GPU runs at 85 % throughput; assume 70 % of the step is compute on the critical path
and 30 % exposed communication. Compute the new step time, throughput loss, and GPU-equivalents lost.
(b) One compute NIC's PCIe link trains at Gen5 x8 instead of x16. Compute the PCIe ceiling per
direction, assume 85 % of it is achieved, and compute the extra DP all-reduce time per step for the
7.66 GB per GPU of Section 16.6, as a percentage of step time. (c) Which defect is worse for this job,
and why must acceptance reject both anyway?
*Evidence required:* arithmetic for each part; the critical-path argument in (c).
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare your method with the worked solution and marking scheme in the chapter's `solutions/exercises/W2-degraded-node-cost/` (instructor material in the full repository; removed from student releases).

## What to submit

Write your working in `outputs/answer.md`: formula → substitution → result with units for every
part, plus the evidence label. If you check the arithmetic with a script, save it as
`outputs/work.py` and run it from this folder with `python outputs/work.py`.
