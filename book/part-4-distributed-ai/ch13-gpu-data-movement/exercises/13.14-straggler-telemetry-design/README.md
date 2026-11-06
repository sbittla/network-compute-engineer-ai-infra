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

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare your method with the worked solution and marking scheme in the chapter's `solutions/exercises/13.14-straggler-telemetry-design/` (instructor material in the full repository; removed from student releases).

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/design.md`
- `outputs/volume_estimate.md` (your data-volume arithmetic, or the output of your script)

Optional: if you script the arithmetic, save the script as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
