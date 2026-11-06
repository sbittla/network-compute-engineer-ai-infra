# M4 - Design-B hall model `[MODELED]`

- Rack: 8 × 14.3 kW = **114.4 kW** provisioned (96 kW sustained)
- 2N: each side must carry the rack; with a 10 % transient margin each side needs >= 127.1 kW continuous
- Liquid: 0.8 × 114.4 = 91.52 kW; air residual 22.88 kW
- Flow: 91.52 / (4.18 × 10) = **2.19 kg/s = 131 L/min** (glycol 2.35 kg/s)
- Hall: power fit 62 nodes, cooling fit 87 -> **62 nodes in 8 racks**; 17.0 kg/s total, 177 kW to air, facility 1.000 MW
- Transient (250 W/GPU swing): 16 kW per rack, 124 kW per hall
