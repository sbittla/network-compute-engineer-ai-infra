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

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) (W-INFER for serving questions).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare your method with the worked solution and marking scheme in the chapter's `solutions/exercises/O2-analyze-serving-trace/` (instructor material in the full repository; removed from student releases).

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

Optional: if you script the arithmetic, save the script as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
