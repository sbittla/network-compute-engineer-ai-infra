# K8 · Label cardinality for per-rank, per-step metrics (★★ · L1)

Type: knowledge-check · Kind: computed · Points: 5

<!-- prompt:start -->
**K8 ★★ L1 — Cardinality.** Why must `rank`, `request_id`, and `step` never be Prometheus labels on
high-frequency metrics? Estimate the series count if a 4,096-GPU job exported a per-rank step-time
gauge with a `step` label for one day at 17.4 s per step.
*Evidence required:* the series-count calculation and where that information should live instead.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Write your working in `outputs/answer.md`: formula → substitution → result with units for every
part, with evidence labels. If you check it with a script, save it as `outputs/work.py` and run it
from this folder with `python outputs/work.py`.
