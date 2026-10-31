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

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`
