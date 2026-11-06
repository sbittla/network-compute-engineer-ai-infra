# W1 — Headroom budget for a spine (★★, L1)

Type: Worked problem · kind: `computed` · 10 points

## Prompt

<!-- prompt:start -->
**W1 ★★ L1 — Headroom budget.** A 64-port, 400 Gb/s spine has all ports on 150 m fiber runs (port MTU 9,216 B, t_resp = 1 µs). Two
priorities are lossless.
(a) Compute the headroom per port per lossless priority.
(b) Compute the total headroom reservation for the switch.
(c) Repeat (a) for 800 Gb/s with the same cable, MTU, and response time, and comment on how headroom
scales with link speed.
*Evidence required:* every term of the formula substituted with units; three results; one-sentence
comment.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 9 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the chapter's assumptions: light travels 5 ns/m in fiber, port MTU 9,216 B, t_resp = 1 µs.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Show formula → substitution → result with units (r = 400 Gb/s = 50 B/ns), and label every number. Put every deliverable in `outputs/`:

- `outputs/answer.md`
