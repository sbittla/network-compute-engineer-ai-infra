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

## What to submit

Show formula → substitution → result with units (r = 400 Gb/s = 50 B/ns), and label every number. Put every deliverable in `outputs/`:

- `outputs/answer.md`
