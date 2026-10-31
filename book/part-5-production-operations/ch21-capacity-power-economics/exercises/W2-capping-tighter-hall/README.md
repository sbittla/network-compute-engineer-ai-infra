# W2 — Capping in a tighter hall (★★★, L1)

Type: Worked problem · Kind: `computed` · Points: 10

## Prompt

<!-- prompt:start -->
**W2 ★★★ L1 — Capping in a tighter hall.** Same 64 nodes and 16 racks as Section 21.8, but the rack limit is
30 kW (10 % transient margin) and you may only use the caps in the lab's curve; node peak = 4.6 kW + 8 × cap.
(a) Find nodes per rack and cluster throughput for 650 W, 550 W, and 350 W. (b) Which is best, and why is
"cap deeper to fit more nodes" not always right? (c) If six more racks become available (22 in all), what
do you recommend?
*Evidence required:* table for the three caps; reasoning; recommendation with numbers.
<!-- prompt:end -->

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/answer.md`

Run:

```bash
python solve.py --out outputs/     # your own script; show every formula and substitution
```
