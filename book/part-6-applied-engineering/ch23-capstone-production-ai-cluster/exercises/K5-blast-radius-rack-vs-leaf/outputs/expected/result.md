# K5 — blast radius `[MODELED]`

- Nodes per rack = floor(45.0 / 10.2) = 4
- Rack power failure: 4 × 8 = 32 GPUs = 12.5 % of 256
- Rail-leaf failure: 0 GPUs lost; 32 nodes each lose 1 of 8 rails (12.5 % of backend bandwidth); every multi-node job on the rail is hit
- Contrast, spine failure: uplinks 32 → 24, oversubscription 1.33:1
