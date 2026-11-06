# 20-M2 — Canary rollout design for the leaf QoS profile (★★★, L1)

Type: Outline-mandated · Kind: `written` · Points: 20

## Prompt

<!-- prompt:start -->
Design the rollout of a new RoCE QoS profile to ORION's 8 rail leaves (`orion-be-leaf-r0`–`orion-be-leaf-r7`). The
new profile tightens ECN marking thresholds on TC 3. Produce:

1. **Prechecks**: per-leaf and fabric-wide, with the exact signals.
2. **Wave plan**: which leaf first and why; wave sizes; bake time justified from Table 20.8.
3. **Success criteria**: measurable, per rail, with baseline method and thresholds.
4. **Abort conditions**: at least four, each with statistic, threshold, and floor where relevant.
5. **Rollback**: mechanism, scope, rehearsal evidence, time bound.
6. **Audit evidence**: what is recorded per leaf and per wave, and where.

**Evidence required:** a 1–2 page design using the six headings; every threshold labelled
`[ILLUSTRATIVE]` or derived from a stated baseline; explicit reasoning about rail independence.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 20 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md). Values are ORION `[ILLUSTRATIVE]` unless stated.
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the model answer and marking scheme in [outputs/expected/](outputs/expected/README.md); compare the reasoning and evidence, not the wording.

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/design.md` (six headings, 1-2 pages)
