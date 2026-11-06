# D1 · Alerting for ORION-XL on one rotation (★★★ · L1)

Type: design-challenge · Kind: computed · Points: 10

<!-- prompt:start -->
**D1 ★★★ L1 — Alerting for ORION-XL on one rotation.** ORION-XL runs ≈ 40 concurrent training jobs
(64 to 4,096 GPUs) and three inference services, with one SRE rotation whose page budget is two
incidents per 12-hour shift. Design the page-severity alert set (≤ 8 rules), the ticket set, and the
routing. Defend which causes, if any, are allowed to page, and how you prevent 40 jobs from producing
40 pages during one fabric incident.
*Evidence required:* rule table (name, SLI or cause, windows/thresholds, severity, route); grouping /
inhibition strategy; estimated pages per shift with assumptions.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 18 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Write your design in `outputs/answer.md`: the rule table with the columns the prompt names, then the
grouping and inhibition strategy, then a short defence of which causes may page. For the pages-per-shift
estimate, list each assumption and show the arithmetic; give every number you use an evidence label.
