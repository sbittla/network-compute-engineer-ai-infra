# 13.10 — GPU utilization low, network utilization high (O2) (★★★, L1)

Type: outline-mandated · Kind: lab

## Prompt

<!-- prompt:start -->
**13.10 (O2) ★★★ L1 — GPU utilization low, network utilization high.** Using the lab bundle (or the
windows in Section 13.13 if you have not finished the lab), determine whether communication,
synchronization, or data imbalance is responsible for the slowdown — for each of steps 0–19, 20–29,
and 30–59 — and justify each conclusion with at least two independent telemetry fields. State which
popular metric would have misled you and why.
*Evidence required:* a per-window verdict table with evidence fields, the decoy rejected, and the
misleading metric explained.
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/verdict_table.md`
- `outputs/check_output.txt (from python lab/check.py)`

Run:

```bash
python lab/check.py
```

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
