# 13.14 — Straggler telemetry for ORION-XL (★★★, L1)

Type: design-challenge · Kind: computed

## Prompt

<!-- prompt:start -->
**13.14 ★★★ L1 — Straggler telemetry for ORION-XL.** Design the per-rank telemetry pipeline for a
4,096-GPU job: which fields, sampling interval, how arrival skew is measured without synchronized
clocks, the join keys to hardware, the data volume per day, and the alert rules (with thresholds and
statistics). Defend one trade-off between fidelity and overhead.
*Evidence required:* field list, volume estimate with arithmetic, alert rules, and a defence paragraph.
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/design.md`
- `outputs/volume_estimate (your arithmetic or script output)`

Run:

```bash
python solution/solve.py --out outputs
```

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
