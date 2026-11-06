# 7.K6 — ECMP-aware ingress after one link failure (★★, L1)

Type: Knowledge check · kind: `computed` · 3 points

## Prompt

<!-- prompt:start -->
**7.K6** ★★ L1 — One of the 8 links between orion-be-leaf-r0 and orion-be-spine-1 fails. Why does the ECMP-aware
ingress capacity of orion-be-leaf-r0 fall by 12.5 % when its raw uplink capacity falls by only 3.1 %?
*Evidence required:* both numbers with arithmetic and the one-sentence mechanism.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) for the ORION-256 backend, and the Section 7.3 conventions (Table 7.2).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Show formula → substitution → result with units, and label every number (`[MODELED]` unless stated). Put every deliverable in `outputs/`:

- `outputs/answer.md`
