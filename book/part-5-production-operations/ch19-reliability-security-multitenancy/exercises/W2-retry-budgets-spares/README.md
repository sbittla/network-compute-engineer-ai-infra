# W2 — Retry budgets and spares (★★★, L1)

Type: Worked problem · Kind: `computed` · Points: 12

## Prompt

<!-- prompt:start -->
**W2 ★★★ L1 — Retry budgets and spares.**
(a) After an upgrade to NCCL 2.23 or later the `NCCL_IB_TIMEOUT` default becomes 20 (it was 18 up to
2.22). With `NCCL_IB_TIMEOUT=20` and `NCCL_IB_RETRY_CNT=7`, compute the retry budget. Which of the lab's
flaps (14 s, 6 s, 5 s, 14 s) would now be survived?
(b) What do you lose by raising the timeout? Quantify for a 4,096-GPU job whose peer has *died*.
(c) Size a declared ORION-XL spare pool (a variation; the reference cluster has none) with the Chapter 16
Poisson method at P(in repair ≤ k) ≥ 0.99, for repair turnaround of 3 days and of the canonical 5 days.
Express each as a percentage of the 512-node partition.
*Evidence required:* arithmetic for each part; a recommendation with its trade-off.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 19 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md); reliability uses node MTBF ≈ 1,536 node-hours, repair turnaround (MTTR) 5 days and restart overhead ≈ 15 min.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/answer.md` (arithmetic and recommendation)

"The canonical 5 days" in part (c) is the repair turnaround (MTTR) in the Before-you-start defaults above; use
the node MTBF of ≈ 1,536 node-hours from the same line for the failure rate. Both come from the reliability
table in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md#reliability-assumptions-canonical-illustrative).
The lab's four flaps for part (a), and the retry-budget formula, are in Section 19.4 ("NCCL timeout or hang")
of the chapter; the spare-pool worked example for part (c) is in Section 19.7
("Rank remapping and spares").
