# M4 — Capacity/power/cooling model and guardrails: reference answer

Sources: manuscript Sections 21.5 (Design B), 21.6 (power chain, 2N), 21.7 (heat removal, transient
headroom) and 21.8 (Table 21.8); `lab/data/designs.yaml`. Inputs `[ILLUSTRATIVE]`. Rack power figures
are tied to *this* Design-B reference (8 nodes × 14.3 kW), not to any vendor rack
`[VENDOR-SPEC, 2026-10]`. Results `[MODELED]`; `solve.py` reproduces the arithmetic.

**Assumptions register**

| Input | Value | Label / source | Owner | How to measure |
|---|---|---|---|---|
| Hall IT power | 1.0 MW | `designs.yaml` `[ILLUSTRATIVE]` | Facilities | Switchgear and UPS rating, commissioning report |
| CDU capacity | 1.0 MW to liquid | `designs.yaml` | Facilities | CDU nameplate and N+1 test |
| Node power | 14.3 kW provisioned, 12.0 sustained | `designs.yaml` | Platform | PDU/BMC under the training benchmark |
| Heat to liquid | 80 % | prompt | Vendor + Facilities | CDU heat balance at load |
| Coolant | water, c_p 4.18 kJ/kg·K, ΔT 10 K | Section 21.7 | Facilities | Supply/return sensors, flow meters |
| Transient margin | 10 % | ORION policy | Platform | L3 rack telemetry (peak versus p99) |
| PUE | 1.20 (variation) | `designs.yaml` | Facilities | Metered facility/IT ratio by season |

**Facility capacity.** Power fit ⌊1,000 / (14.3 × 1.12)⌋ = 62 nodes. Cooling fit ⌊1,000 / 11.44⌋ =
87 nodes. **Power binds**: 62 nodes = 496 GPUs in ⌈62 / 8⌉ = **8 racks** (7 full, 1 with 6 nodes).
Sustained facility power = 62 × 12.0 × 1.12 × 1.20 = 1.000 MW.

**Rack power budget and redundancy.** 8 × 14.3 = **114.4 kW provisioned** per rack (96 kW sustained).
Redundancy mode 2N A/B: either side must carry the rack, so each side needs ≥ 114.4 / 0.9 =
**127.1 kW** continuous after derating. With 32.78 kW canonical circuits that is 4 circuits per side.

**Liquid cooling and flow.** Liquid heat = 0.8 × 114.4 = 91.5 kW; residual to air = **22.9 kW** per
rack (177 kW per hall, which still needs room air handling).

```text
mass flow = P / (c_p × ΔT) = 91.52 / (4.18 × 10) = 2.19 kg/s ≈ 131 L/min water per rack
glycol mix (c_p 3.9): 2.35 kg/s (+7 %); hall total (water) ≈ 17.0 kg/s
```

**Transient headroom.** At an assumed 250 W per-GPU swing, each rack swings ≈ 16 kW and the hall
≈ 124 kW per step. Provisioned minus sustained = 2.3 kW per node (18.4 kW per rack) covers this.
The 10 % margin covers excursions, and millisecond peaks follow vendor PSU guidance.

**Power-capping policy.** Default cap at the vendor's TDP. Caps are applied *uniformly per job*.
Automatic caps on budget alarms (below). The cap value is chosen from a measured curve (L2).

**Guardrail table**

| Signal | Threshold `[ILLUSTRATIVE]` | Automated action | Owner |
|---|---|---|---|
| Rack power per side | > 80 % of 127 kW for 5 min | Stop new placement on the rack | Platform |
| Rack power per side | > 90 % for 2 min | Uniform job cap, or checkpoint and move | Platform + Facilities |
| Feed loss A or B | Any | Verify one side carries the rack; cap if not; page | Facilities |
| CDU supply temperature | > design + 3 K for 5 min | Cap the row; alert | Facilities |
| CDU pump redundancy | Lost | Page; plan row-wide cap | Facilities |
| Leak sensor | Any | Isolate rack valves; drain the rack's jobs | Facilities + Platform |
| Job start/stop | > 500 kW | Ramp over ≥ 60 s; notify | Training Infra |
| GPU HW thermal slowdown | > 2 % of a row for 10 min | Ticket; inspect flow per cold plate | Facilities + Fleet |

**Workload/facility interface.** Facility → scheduler: per-rack/row budgets, CDU state, maintenance
windows, demand response. Scheduler → facility: planned large-job starts/stops, expected sustained row
load. Mechanism: rack power as a schedulable resource (see R4).

**Facility/MEP hand-off checklist** (≥ 8): rack weight and floor loading; coolant quality,
chemistry and filtration; leak detection and isolation valves; CDU redundancy mode (N+1 pumps);
supply/return temperatures and ΔT; flow per rack and per cold plate; electrical circuits per feed and
redundancy mode (2N, 4 circuits per side); metering and telemetry points (UPS, busway, PDU per phase,
CDU); commissioning tests (load bank, failover, transient step); maintenance access and ownership
boundaries (who services the CDU and the manifold).

**Common wrong answers:** using 14.3 × 8 as the *per-feed* need without the margin; forgetting the
air residual; the kg/s ↔ L/min conversion (× 60); quoting a "120 kW rack" without tying it to the design.
