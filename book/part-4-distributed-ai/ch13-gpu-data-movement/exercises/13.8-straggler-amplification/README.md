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

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

Optional: if you script the arithmetic, save the script as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
