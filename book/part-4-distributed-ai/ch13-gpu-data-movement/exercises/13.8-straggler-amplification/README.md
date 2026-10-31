# 13.8 — Straggler amplification (★★, L1)

Type: worked-problem · Kind: computed

## Prompt

<!-- prompt:start -->
**13.8 ★★ L1 — Amplification.** (a) If each rank independently has a 0.05 % chance of a slow step,
what fraction of steps contain at least one slow rank at N = 256, 1,024, and 4,096? (b) In a 64-rank
job, one rank's compute is 774 ms while the others take 600 ms; steps take 924 ms. Compute the GPU
time lost per step and the lost fraction.
*Evidence required:* three probabilities and two numbers, formulas shown.
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

Run:

```bash
python solution/solve.py --out outputs
```

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
