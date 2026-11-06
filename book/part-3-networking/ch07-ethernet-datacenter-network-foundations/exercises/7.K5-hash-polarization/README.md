# 7.K5 — Hash polarization (★★, L1)

Type: Knowledge check · kind: `computed` · 4 points

## Prompt

<!-- prompt:start -->
**7.K5** ★★ L1 — Define hash polarization. Using the leaf-uplink numbering in Section 7.6, show
which of a spine's 8 downstream links are used when leaf and spine use the same hash *h mod n*.
*Evidence required:* the modular-arithmetic argument and the resulting link set.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 7 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) for the ORION-256 backend, and the Section 7.3 conventions (Table 7.2).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Show formula → substitution → result with units, and label every number (`[MODELED]` unless stated). Put every deliverable in `outputs/`:

- `outputs/answer.md`
