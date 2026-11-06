# K2 — Pause quantum arithmetic (★, L1)

Type: Knowledge check · kind: `computed` · 5 points

## Prompt

<!-- prompt:start -->
**K2 ★ L1 — Pause arithmetic.** Compute the duration of one PFC pause quantum and of the maximum
single-frame pause (65,535 quanta) at 100 Gb/s and at 400 Gb/s. Why does a sustained pause appear as a
*rate* of pause frames in counters?
*Evidence required:* four values with formula and units; one-sentence explanation.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the chapter's assumptions: light travels 5 ns/m in fiber, port MTU 9,216 B, t_resp = 1 µs.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Show formula → substitution → result with units (r = 400 Gb/s = 50 B/ns), and label every number. Put every deliverable in `outputs/`:

- `outputs/answer.md`
