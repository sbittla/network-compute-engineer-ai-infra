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

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Submit one file, `outputs/slo_spec.md`: the four-service table, the PromQL recording rules, and the
error-budget arithmetic (formula → substitution → result with units, with an evidence label on each number).
If you check the arithmetic with a script, save it as `outputs/work.py` and run it from this folder with
`python outputs/work.py`.
