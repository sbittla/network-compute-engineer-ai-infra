# Marking scheme: 5.8 PCIe budget

Type worked-problem · kind computed · tier L1 · 10 points

**Evidence required:** arithmetic for (a), justification for (b), two traffic estimates for (c) with assumptions.

| Criterion | Points |
|---|---|
| (a) Gen4 x16 31.5 GB/s, Gen5 x8 31.5 GB/s, Gen5 x16 63.0 GB/s per direction with 128b/130b arithmetic | 3 |
| (b) only Gen5 x16 carries a 400 Gb/s (50 GB/s) NIC at line rate, with the achievable-rate caveat | 2 |
| (c) with GDR the NIC-GPU DMA stays inside the switch: uplink carries essentially only control traffic | 2 |
| (c) host-staged: 200 GB/s of upstream demand against 63 GB/s, about 16 GB/s per NIC per direction, assumptions stated, labelled [MODELED] | 3 |
