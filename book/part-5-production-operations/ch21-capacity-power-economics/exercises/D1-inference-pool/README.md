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

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/answer.md`

Run:

```bash
python solve.py --out outputs/     # your own script; show every formula and substitution
```
