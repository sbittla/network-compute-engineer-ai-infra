# D1 — A second lossless class? (★★★, L1)

Type: Design challenge · kind: `computed` · 15 points

## Prompt

<!-- prompt:start -->
**D1 ★★★ L1 — A second lossless class?** The Storage team wants its new RDMA-based checkpoint traffic
(Chapter 14) to share ORION's backend fabric as a *second* lossless priority (priority 4), arguing that
checkpoints "cannot tolerate loss". Write a one-page recommendation: accept, reject, or accept with
conditions. Quantify the headroom cost for a rail leaf (32 host ports at 30 m, 32 spine ports at 100 m),
explain the interaction with W-TRAIN's TC 3, and compare at least two alternatives.
*Evidence required:* headroom arithmetic; at least three risks; at least two alternatives in a
trade-off table; a decision with the conditions or evidence that would change it.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the chapter's assumptions: light travels 5 ns/m in fiber, port MTU 9,216 B, t_resp = 1 µs.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Write a one-page recommendation with the headroom arithmetic and a trade-off table. Put every deliverable in `outputs/`:

- `outputs/answer.md`
