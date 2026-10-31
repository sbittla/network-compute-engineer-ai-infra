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

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/answer.md (arithmetic and recommendation)`
