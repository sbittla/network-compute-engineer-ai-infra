# D1 — Hot spares vs elastic training (★★★, L1)

Type: Design challenge · Kind: `computed` · Points: 10

## Prompt

<!-- prompt:start -->
**D1 ★★★ L1 — Hot spares vs elastic training.** A 512-node ORION-XL job runs TP = 8, PP = 8, DP = 64, so one
DP replica is 8 nodes. Halcyon can either (A) keep a declared, Poisson-sized (p99) spare pool outside the
partition and restart at fixed world size (R = 15 min), or (B) use elastic training with no spares that
drops whole DP replicas and re-shards in 5 minutes. Using the canonical MTBF and 5-day MTTR, compare
expected useful throughput per *fleet* node for A, for B with rank re-packing, and for B without it
(expected and worst case). Address global-batch divisibility when DP changes, and recommend.
*Evidence required:* model with assumptions; numeric comparison; recommendation with risks.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 19 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md); reliability uses node MTBF ≈ 1,536 node-hours, repair turnaround (MTTR) 5 days and restart overhead ≈ 15 min.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/answer.md` (model, comparison table, recommendation)

"Canonical MTBF and 5-day MTTR" are the values in the Before-you-start defaults above (node MTBF ≈ 1,536
node-hours, repair turnaround 5 days). They come from the reliability table in
[docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md#reliability-assumptions-canonical-illustrative).
The Poisson spare-sizing method is from Chapter 16; Section 19.7 ("Rank remapping and spares") of the
the full edition of the chapter applies it to ORION-XL.
