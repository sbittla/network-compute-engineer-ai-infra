# Marking scheme: 2.10 Growing ORION to 512 GPUs in the same hall

Type design-challenge · kind computed · tier L1 · 15 points

**Evidence required:** Decision record; power, cooling, CDU, and floor arithmetic for the chosen option; the fabric change with switch and link counts.

| Criterion | Points |
|---|---|
| At least three options with criteria, each checked against the rack, power, CDU and floor limits | 4 |
| Arithmetic for the chosen option correct (for example 16 DLC racks at 36.75 kW, 470.4 kW liquid on two CDUs at 78.4 %, IT under 800 kW, floor 1,139 kg/m2) | 5 |
| Consistent fabric change (16 rail leaves, 8 spines, 512 host links, 512 leaf-spine links, 24 switches) | 3 |
| Honesty about constraints that cannot be met (rack positions must be reclaimed; no N+1 CDU without a third unit) | 3 |
