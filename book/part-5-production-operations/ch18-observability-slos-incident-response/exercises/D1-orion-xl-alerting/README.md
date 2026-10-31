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

## What to submit

Write your working in `outputs/answer.md`: formula → substitution → result with units for every
part, with evidence labels. If you check it with a script, save it as `outputs/work.py` and run it
from this folder with `python outputs/work.py`.
