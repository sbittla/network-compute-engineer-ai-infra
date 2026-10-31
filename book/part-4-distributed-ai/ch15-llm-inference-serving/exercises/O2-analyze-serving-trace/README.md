# O2 — Analyze a serving trace (★★, L1)

Type: outline-mandated · Kind: computed

## Prompt

<!-- prompt:start -->
**O2. ★★ L1 — Analyze a serving trace.** Using Lab Part B on `lab/data/`, report TTFT, ITL,
throughput (req/s and output tokens/s), queue time, and GPU utilization (`gpu_busy_pct`) for the
baseline (< 230 s) and for each detected episode. Explain why GPU utilization is the least
informative of these.
*Evidence required:* a table with each metric for the baseline and each episode, and the
explanation.
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

Run:

```bash
python solution/solve.py --out outputs
```

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
