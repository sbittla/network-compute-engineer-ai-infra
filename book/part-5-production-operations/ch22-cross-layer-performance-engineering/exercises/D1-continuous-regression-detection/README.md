# D1 — Continuous regression detection for ORION (★★★, L1)

Design challenge · difficulty ★★★ · tier L1 · kind `computed` · [exercise index](../README.md)

<!-- prompt:start -->
**D1 ★★★ (L1) — Continuous regression detection for ORION.** Design a system that detects a ≥ 3 %
training-throughput regression within one day of a change window and produces a first attribution
automatically. Consider: dedicated canary benchmark jobs versus mining production jobs (natural
experiments), the GPU cost of reserved canaries on a 32-node cluster, the change-calendar and inventory
joins (time-aware), statistical thresholds (σ, MDE), and false-positive cost.
*Evidence required:* architecture sketch; a trade-off table with at least two options and four criteria
(detection time, GPU cost, false-positive rate, causal strength); a stated recommendation with the
arithmetic for canary cost and detectable effect.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md). Numbers in prompts are `[ILLUSTRATIVE]` unless labelled otherwise.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`
