# M4 — Capacity/power/cooling model and guardrails (★★★, L1)

Type: Outline-mandated · Kind: `computed` · Points: 15

## Prompt

<!-- prompt:start -->
**M4 ★★★ L1 — Capacity/power/cooling model and guardrails (course outline §20.3, table 8).** For a hall of Design-B
racks (8 nodes, 14.3 kW provisioned per node, 80 % heat to liquid), state the facility capacity, rack power
limit and redundancy mode, liquid-cooling capacity and required coolant flow at ΔT = 10 K, transient
headroom, and the power-capping policy. Produce the guardrail table (signal, threshold, automated action,
owner) and the workload/facility coordination interface.
*Evidence required:* assumptions register; rack power budget; coolant-flow arithmetic; guardrail table;
facility/MEP hand-off checklist (≥ 8 items).
<!-- prompt:end -->

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/capacity_power_cooling_model.md`

Run:

```bash
python solve.py --out outputs/     # your own script; show every formula and substitution
```
