# W2 — Incast and DCQCN feedback timing (★★, L1)

Type: Worked problem · kind: `computed` · 10 points

## Prompt

<!-- prompt:start -->
**W2 ★★ L1 — Incast and feedback.** Sixteen senders each send 2 MB simultaneously to one 400 Gb/s
destination port. The port's Xoff-equivalent threshold is 1.5 MB, its buffer share 6 MB, base RTT 6 µs,
DCQCN CNP interval N = 50 µs, initial α = 1.
(a) Excess arrival rate in KB/µs. (b) Time to reach the threshold. (c) Can ECN feedback arrive before
it? (d) Minimum possible completion time. (e) Approximate time for repeated DCQCN halving to bring the
aggregate rate to the drain rate, and what fraction of (d) that is. (f) BDP, and a defensible upper
bound for Kmin.
*Evidence required:* six results with formula → substitution → result.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the chapter's assumptions: light travels 5 ns/m in fiber, port MTU 9,216 B, t_resp = 1 µs.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Show formula → substitution → result with units (r = 400 Gb/s = 50 B/ns), and label every number. Put every deliverable in `outputs/`:

- `outputs/answer.md`
