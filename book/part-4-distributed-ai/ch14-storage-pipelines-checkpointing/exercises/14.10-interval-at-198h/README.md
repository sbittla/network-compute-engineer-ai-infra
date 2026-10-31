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

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`
- `outputs/planner_table.md (your Part A planner output)`

Run:

```bash
python solution/solve.py --out outputs
```

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
