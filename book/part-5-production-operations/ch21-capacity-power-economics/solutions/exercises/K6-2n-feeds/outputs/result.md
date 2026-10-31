# K6 - 2N feeds `[MODELED]`

Circuit: sqrt(3) × 415 V × 60 A × 0.95 × 0.8 = 32.78 kW continuous

- canonical: 2 circuit(s) per side = 65.55 kW; × (1 - 0.1) = **59.0 kW** planned peak; 4 uncapped HX8 nodes (40.8 kW)
- legacy: 1 circuit(s) per side = 32.78 kW; × (1 - 0.1) = **29.5 kW** planned peak; 2 uncapped HX8 nodes (20.4 kW)

Legacy rack: three nodes need a GPU cap <= 654 W; at 650 W they draw 29.4 kW.
Failure scenario: loss of side A or B; the surviving side must carry the whole rack.
