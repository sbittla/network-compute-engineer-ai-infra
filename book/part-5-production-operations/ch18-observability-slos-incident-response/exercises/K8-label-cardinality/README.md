# K8 · Label cardinality for per-rank, per-step metrics (★★ · L1)

Type: knowledge-check · Kind: computed · Points: 5

<!-- prompt:start -->
**K8 ★★ L1 — Cardinality.** Why must `rank`, `request_id`, and `step` never be Prometheus labels on
high-frequency metrics? Estimate the series count if a 4,096-GPU job exported a per-rank step-time
gauge with a `step` label for one day at 17.4 s per step.
*Evidence required:* the series-count calculation and where that information should live instead.
<!-- prompt:end -->

## What to submit

Write your working in `outputs/answer.md`: formula → substitution → result with units for every
part, with evidence labels. If you check it with a script, save it as `outputs/work.py` and run it
from this folder with `python outputs/work.py`.
