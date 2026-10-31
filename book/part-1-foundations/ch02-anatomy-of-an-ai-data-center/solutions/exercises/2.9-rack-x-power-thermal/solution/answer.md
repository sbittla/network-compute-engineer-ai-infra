# 2.9 — Rack-X power and heat-removal budget: model answer

Method: manuscript Sections 2.5 (circuit arithmetic, redundancy), 2.6 (transients), 2.7 (coolant and air
arithmetic) and 2.8 (floor loading, commissioning, ownership). Rack-X is hypothetical; every input is an
`[ILLUSTRATIVE]` assumption and every result `[MODELED]`. `solve.py` reproduces items 2, 3, 5 and 6.

**1. Power one-line (concept).** Utility MV service + generators → transfer switchgear → transformers A/B
→ UPS A / UPS B (2N, or distributed redundant at hall level) → busway A/B with tap-off breakers → rack
power-shelf inputs A/B → power shelves (N+N or N+1 PSUs within the shelf) → DC busbar → compute trays.
Each stage is labelled with its redundancy (2N from the UPS down; N+1 inside the shelf).

**2. Electrical budget.** Per-side design load = 120 × 1.15 = **138 kW**.

```text
125 A circuit: √3 × 415 × 125 = 89.85 kVA × 0.80 × 0.95 = 68.29 kW
  2 circuits = 136.6 kW  ✗ (1.4 kW short: the trap)
  3 circuits = 204.9 kW  ✓ (66.9 kW headroom)
160 A circuit: √3 × 415 × 160 = 115.0 kVA × 0.76 = 87.41 kW
  2 circuits = 174.8 kW  ✓ (36.8 kW headroom, 21 %)
```

Either valid choice earns credit; prefer 2 × 160 A per side if the power shelves accept it (fewer
whips and breakers). Under 2N each side must carry the full 138 kW alone.

**3. Transient margin check.** 8 racks × 120 kW × 0.30 = **288 kW** step within 50 ms. Confirm against
tap-off and busway breaker trip curves, UPS step-load and mode-transfer behaviour, generator step
acceptance (on generator after a utility loss), and any utility ramp-rate obligation. Consider rack
energy storage or platform power smoothing.

**4. Thermal block diagram.** FWS (towers, dry coolers or chillers) → CDU heat exchanger (redundant
pumps, filters, sensors) → TCS supply manifold → rack manifolds with dripless quick-disconnects → cold
plates → TCS return; residual heat to room air or rear-door heat exchangers; leak sensors and isolation
valves marked.

**5. Heat-removal budget (per rack and row).**

```text
liquid = 0.85 × 120 = 102 kW;  air = 18 kW
ṁ   = 102 / (3.90 × 8)           = 3.269 kg/s → / 1.02 = 3.205 L/s = 192.3 L/min per rack
row = 8 × 192.3                  = 1,538 L/min (816 kW of liquid heat)
air = 18 / (1.006 × 1.20 × 15)   = 0.994 m³/s = 2,106 CFM per rack
CDUs: 816 kW needs one 1 MW unit; N+1 → 2 CDUs at 40.8 % each, 81.6 % with one failed
```

**6. Floor loading.** 1,400 kg / (0.6 × 1.2 m²) = **1,944 kg/m²** > 1,200 ✗. Ask the structural engineer:
the rating basis (footprint or distributed), concentrated and rolling loads along the transport path,
whether spreader plates or slab-on-grade placement are needed, and seismic anchoring.

**7. Safe operating envelope.**

| Parameter | Limit | Action when exceeded |
|---|---|---|
| Per-side load | ≤ 80 % of usable sustained (139.8 kW with 2 × 160 A) | Stop new placement; review power caps |
| TCS supply temperature | ≤ 30 °C design; alarm at +3 K | Call Facilities; consider a workload power cap |
| Flow per rack | ≥ 85 % of 192.3 = 163.5 L/min | Inspect strainers and QDs; drain if temperatures rise |
| Rack ΔT at load | ≤ 10 K (design 8 K) | As for low flow |
| CDU utilization | ≤ 85 % with the N+1 unit lost | Defer load additions |
| Inlet air | Within the ASHRAE recommended envelope for the equipment class | Call Facilities |
| Leak alarm | Any | Isolation procedure; drain the affected trays |

**8. Assumptions register.** Each of the given values (IT load 120 kW, margin 15 %, 2N feeds, 415 V,
derate 0.80, PF 0.95, capture 85 %, PG25 cp 3.90 and ρ 1.02, ΔT 8 K, supply 30 °C, air ΔT 15 K, CDU
1 MW, rack mass 1,400 kg, floor 1,200 kg/m²), with its source ("exercise assumption, to be confirmed by
the vendor reference design dated YYYY-MM / MEP engineer / coolant datasheet / structural engineer")
and the consequence if wrong. Example: a capture fraction of 0.80 instead of 0.85 adds 6 kW per rack,
48 kW per row, to the room air.

**9. Facility/MEP handoff checklist (owner in brackets).** Per-side maximum kW and transient profile (IT →
MEP); circuit count, rating, voltage and phase plan (MEP → IT); power-shelf input connector type (IT);
PDU or shelf telemetry protocol and OOB addressing (IT/MEP); heat to liquid and to air per rack (IT);
TCS supply temperature, flow and pressure available per rack (MEP); coolant type, chemistry
specification and filtration mesh (MEP, per cold-plate vendor); QD type and manifold connection (both);
leak-detection zones, alarm routing and automatic isolation behaviour (MEP → IT monitoring); floor
rating, transport path and anchoring (MEP/structural); commissioning plan including workload burn-in
(both); emergency power-down and leak-response ownership (both, signed); maintenance windows and the
feed-loss power policy (both).

**Common wrong answers:** 2 × 125 A circuits (136.6 < 138); summing both feeds; omitting the transient
check; presenting 120 kW as a standard rack power.
