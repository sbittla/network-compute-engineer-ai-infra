# Facility / MEP Handoff Checklist — ORION-256

Use this to hand the design to Facilities. Every line needs a value, an owner, and an evidence label.

## Power

- [ ] Per-rack maximum and sustained IT load (kW) for every position: <fill: link to power-cooling-budget.csv>
- [ ] Feed specification per position (phases, voltage, breaker A) and computed usable kW per feed: <fill>
- [ ] Redundancy policy confirmed (2N: either feed carries the full rack): <fill>
- [ ] Positions that fail 2N at max load, and the agreed mitigation (re-feed, power cap, fewer nodes): <fill>
- [ ] Transient headroom: GPU load steps at job start, synchronised collective phases; margin applied: <fill>
- [ ] Power-cap policy and who may change it (`nvidia-smi -pl` on nodes is a change-controlled action): <fill>
- [ ] PDU telemetry points to be ingested (per-outlet or per-phase current, breaker alarms): <fill>

## Cooling

- [ ] Per-row heat load at max vs N+1 cooling capacity: <fill>
- [ ] Rows that fail N+1 and the agreed mitigation (add unit, rear-door heat exchanger, relocate, cap): <fill>
- [ ] Inlet temperature limits for GPU nodes and the monitoring point: <fill>
- [ ] Airflow direction and containment for network racks (port-side intake vs power-side intake): <fill>

## Space and cabling

- [ ] Rack positions, weights and floor loading confirmed: <fill>
- [ ] Overhead tray capacity for the optical link count: <fill>
- [ ] Longest cable runs and the medium chosen (any > MM reach): <fill>

## Sign-off

| Role | Name | Date |
|---|---|---|
| Facilities engineer | <fill> | <fill> |
| Cluster architect | <fill> | <fill> |
