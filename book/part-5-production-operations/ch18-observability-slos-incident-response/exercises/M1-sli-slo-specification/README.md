# M1 · SLI/SLO specification for ORION (★★ · L1)

Type: outline-mandated · Kind: computed · Points: 15

<!-- prompt:start -->
**M1 ★★ L1 — SLI/SLO specification.** Define SLIs and SLOs for **training job completion**, **inference
latency**, **cluster availability**, and **fabric health** for ORION. For each: good/valid events,
measurement source and query, SLO and window, error budget (with arithmetic), burn-rate alert policy,
and the owner. *(Deliverable: `slo_spec.md`.)*
*Evidence required:* a table covering all four services; at least one PromQL recording rule per SLI;
budget arithmetic; exclusions (e.g. client 4xx, user-code failures) stated.
<!-- prompt:end -->

## What to submit

Write your working in `outputs/answer.md`: formula → substitution → result with units for every
part, with evidence labels. If you check it with a script, save it as `outputs/work.py` and run it
from this folder with `python outputs/work.py`.
The deliverable file is `outputs/slo_spec.md`.
