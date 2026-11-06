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
*Evidence required:* the checker at 19/19, every number labelled, and the validation plan with
the commands from lab Section 9.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 15 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) (W-INFER for serving questions).
- **Checking your work:** Run the lab checker as shown below; this exercise is done when the named checks pass. [outputs/expected/](outputs/expected/README.md) shows those check lines from a finished lab, plus a worked answer and the marking scheme.

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/check_output.txt`
- `outputs/memo.md (≤ 2 pages)`

Run:

```bash
python lab/check.py
```

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
