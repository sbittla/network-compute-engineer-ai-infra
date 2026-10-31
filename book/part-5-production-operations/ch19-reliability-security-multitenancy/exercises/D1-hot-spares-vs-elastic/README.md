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

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/answer.md (model, comparison table, recommendation)`
