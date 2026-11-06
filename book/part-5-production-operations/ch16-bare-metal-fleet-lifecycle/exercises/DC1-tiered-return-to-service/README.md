# DC1 · Tiered return-to-service policy (★★★ · L1)

Type: design-challenge · Kind: computed · Points: 20

<!-- prompt:start -->
**DC1 ★★★ (L1) — Tiered return-to-service.** Full acceptance takes ≈ 25 h. Repair data show that 60 %
of repairs are optic/cable swaps, 25 % NIC swaps, 10 % GPU or baseboard swaps, and 5 % DIMM/NVMe
swaps `[ILLUSTRATIVE]`. Design a *tiered* re-acceptance policy that picks the acceptance depth from
what was replaced, without weakening the "only through `validated`" rule. Estimate the average
re-acceptance time under your policy versus full acceptance, and identify the failure mode your
policy could miss and how you would detect it in production.
*Evidence required:* a table mapping repair type → tests; a weighted-average time calculation; one
named residual risk with a detection signal and threshold.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Write your working in `outputs/answer.md`: formula → substitution → result with units for every
part, plus the evidence label. If you check the arithmetic with a script, save it as
`outputs/work.py` and run it from this folder with `python outputs/work.py`.
