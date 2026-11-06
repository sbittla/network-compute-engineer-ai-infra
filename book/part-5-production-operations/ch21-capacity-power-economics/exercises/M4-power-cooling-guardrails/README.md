# M4 — Capacity/power/cooling model and guardrails (★★★, L1)

Type: Outline-mandated · Kind: `computed` · Points: 15

## Prompt

<!-- prompt:start -->
**M4 ★★★ L1 — Capacity/power/cooling model and guardrails.** For a hall of Design-B
racks (8 nodes, 14.3 kW provisioned per node, 80 % heat to liquid), state the facility capacity, rack power
limit and redundancy mode, liquid-cooling capacity and required coolant flow at ΔT = 10 K, transient
headroom, and the power-capping policy. Produce the guardrail table (signal, threshold, automated action,
owner) and the workload/facility coordination interface.
*Evidence required:* assumptions register; rack power budget; coolant-flow arithmetic; guardrail table;
facility/MEP hand-off checklist (≥ 8 items).
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md). Inputs are `[ILLUSTRATIVE]` and results `[MODELED]` unless stated.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/capacity_power_cooling_model.md`

Optional: if you script the arithmetic, save the script as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```
