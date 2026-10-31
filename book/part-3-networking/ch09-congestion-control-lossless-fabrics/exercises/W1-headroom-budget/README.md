# W1 — Headroom budget for a spine (★★, L1)

Type: Worked problem · kind: `computed` · 10 points

## Prompt

<!-- prompt:start -->
**W1 ★★ L1 — Headroom budget.** A 64-port, 400 Gb/s spine has all ports on 150 m fiber runs. Two
priorities are lossless.
(a) Compute the headroom per port per lossless priority.
(b) Compute the total headroom reservation for the switch.
(c) Repeat (a) for 800 Gb/s with the same cable, MTU, and response time, and comment on how headroom
scales with link speed.
*Evidence required:* every term of the formula substituted with units; three results; one-sentence
comment.
<!-- prompt:end -->

## What to submit

Show formula → substitution → result with units (r = 400 Gb/s = 50 B/ns), and label every number. Put every deliverable in `outputs/`:

- `outputs/answer.md`
