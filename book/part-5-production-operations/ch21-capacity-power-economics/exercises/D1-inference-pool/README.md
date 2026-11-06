# D1 — The inference pool (★★★, L1)

Type: Design challenge · Kind: `computed` · Points: 10

## Prompt

<!-- prompt:start -->
**D1 ★★★ L1 — The inference pool.** `chat-70b` needs 96 GPUs (Section 21.3) sized for peak + N+2, with average
load 40 % of peak. Option 1: dedicated pool. Option 2: shared pool where preemptible training borrows idle
replicas and must yield within 60 s. Compare useful GPU-hours per year, risk to the TTFT SLO, and
operational complexity. Recommend, with the guardrails that make your choice safe.
*Evidence required:* quantified comparison with assumptions; SLO risk analysis; guardrails.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md). Inputs are `[ILLUSTRATIVE]` and results `[MODELED]` unless stated.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare your method with the worked solution and marking scheme in the chapter's `solutions/exercises/D1-inference-pool/` (instructor material in the full repository; removed from student releases).

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/answer.md`

Optional: if you script the arithmetic, save the script as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```
