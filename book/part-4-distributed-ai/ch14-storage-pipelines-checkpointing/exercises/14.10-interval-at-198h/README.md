# 14.10 — Interval and lost accelerator-hours at a measured failure rate (★★, L1)

Type: worked-problem · Kind: computed

## Prompt

<!-- prompt:start -->
**14.10 Interval and lost accelerator-hours at a measured failure rate** ★★ · L1
Redo the worked example (Section 14.12) with M = 198 h, the rate derived from the Llama 3 report.
For synchronous and asynchronous PFS strategies, compute the Young interval (rounded up to whole
17.4 s steps), overhead, RPO max, and lost GPU-hours per day. Use your Part A planner and also verify
one strategy by hand. What changed in the ranking and the magnitudes, and why?
*Evidence required:* planner output table plus one hand calculation.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the W-TRAIN values.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`
- `outputs/planner_table.md (your Part A planner output)`

Optional: if you script the arithmetic, save the script as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
