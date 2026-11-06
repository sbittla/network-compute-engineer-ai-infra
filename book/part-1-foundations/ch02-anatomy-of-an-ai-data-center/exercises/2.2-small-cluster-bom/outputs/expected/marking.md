# Marking scheme: 2.2 Small-cluster servers, rack units, ports, and links

Type outline-mandated · kind computed · tier L1 · 20 points

**Evidence required:** A BOM table (item, quantity, formula); the per-side power calculation; a one-line justification for the spine count.

| Criterion | Points |
|---|---|
| Nodes per rack with arithmetic (17.48 kW per circuit, 34.96 kW per side; 3 nodes need 33.88 kW, 4 need 45.1 kW) | 5 |
| GPU racks (6) and rack units of nodes per full rack (24U) | 2 |
| Switches and links (8 leaves, 2 spines, 128 host links, 128 leaf-spine links, 384 ports used, 256 leaf ports unused) | 5 |
| Transceivers (512) and bisection (25.6 Tb/s per direction), 2 points each | 4 |
| Frontend (32) and OOB (56) port counts | 2 |
| One assumption to verify, with the reason (for example the 1.08 kW per-side headroom) | 2 |
