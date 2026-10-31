# DEL — Inference capacity model and tuning recommendation (★★★, L1 (L2 optional))

Type: deliverable · Kind: lab

## Prompt

<!-- prompt:start -->
**DEL. ★★★ L1 (L2 optional) — Inference capacity model and tuning recommendation.** Submit the
completed lab module (Parts A–C) and a recommendation memo of at most two pages for W-INFER on
ORION. The memo must cover: the chosen replica layout and pool size for the 40 req/s launch, the
latency and throughput tiers, a disaggregation decision with network budget, phase-specific SLOs
and alert thresholds, and a validation plan listing the L2/L3 measurements and the manifest fields
to record.
*Evidence required:* the checker at 18/18, every number labelled, and the validation plan with
the commands from lab Section 9.
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/check_output.txt`
- `outputs/memo.md (≤ 2 pages)`

Run:

```bash
python lab/check.py
```

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
