# Exercise 2.9 — High-density rack power and heat-removal budget with MEP handoff

**Difficulty:** ★★★ · **Tier:** L1 · **Type:** design-challenge · **Kind:** computed · **Points:** 25

## Prompt

<!-- prompt:start -->
*(Outline §20.3 exercise.)* Halcyon is evaluating a hypothetical rack-scale accelerator system,
**Rack-X**, for a future cluster. Treat all figures as assumptions, not as a description of any
product. If you substitute a real vendor's rack-scale design, cite the vendor reference design by
title and the month you checked it; never present its figures as a universal rack standard.

Assumptions `[ILLUSTRATIVE]`: maximum IT load 120 kW per rack; transient margin 15 %; 2N A/B feeds;
415 V three-phase circuits; derate 0.80; power factor 0.95; liquid capture fraction 85 %; TCS coolant
PG25 (cp 3.90 kJ/(kg·K), ρ 1.02 kg/L) with ΔT 8 K and supply 30 °C; air ΔT 15 K (cp 1.006, ρ 1.20);
8 racks per row served by CDUs of 1 MW liquid capacity each; rack mass 1,400 kg on a 0.6 m × 1.2 m
footprint; floor rated 1,200 kg/m² over the footprint.

Produce:

1. **Power one-line concept** from utility to rack power shelves, showing redundancy at each stage.
2. **Rack electrical budget:** per-side design load; the number of 125 A circuits per side, and
   alternatively 160 A circuits, needed; PDU (or power-shelf input) headroom for your choice.
3. **Transient margin check:** if all 8 racks step by 30 % of maximum within 50 ms, what is the row's
   step in kW, and which stages of the chain must be confirmed against it?
4. **Thermal/cooling block diagram** (FWS, CDU, TCS, manifolds, cold plates, air path).
5. **Heat-removal budget:** heat to liquid and air per rack; coolant flow (L/min) per rack and per
   row; residual airflow (CFM) per rack; CDU count for N+1 at the row level and its utilization.
6. **Floor loading** and what you would ask the structural engineer.
7. **Safe operating envelope:** a table of the parameters operators must keep inside limits (per-side
   kW, TCS supply temperature, flow per rack, ΔT, CDU utilization, inlet air temperature), with the
   limit and the action when exceeded.
8. **Assumptions register:** every assumption, its value, its source (or "to be confirmed by"), and
   the consequence if it is wrong.
9. **Facility/MEP handoff checklist:** the items IT must give Facilities and receive from Facilities
   before installation (at least 12 lines), each with an owner.

**Evidence required:** the nine artifacts above; arithmetic for 2, 3, 5, and 6; each number labelled.
<!-- prompt:end -->

## What to submit

Put every deliverable in [`outputs/`](outputs/):

- `outputs/rack_x_budget.md`: the nine artifacts, with arithmetic for items 2, 3, 5 and 6

Command to run (from this folder):

```bash
python outputs/solve.py --out outputs/   # optional: if you script the arithmetic
```

Label every number you produce (`[MODELED]`, `[ILLUSTRATIVE]`, `[MEASURED]` and so on) and show formula, substitution and result with units.
