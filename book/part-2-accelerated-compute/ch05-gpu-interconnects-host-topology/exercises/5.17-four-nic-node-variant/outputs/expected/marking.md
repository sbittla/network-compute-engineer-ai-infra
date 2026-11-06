# Marking scheme: 5.17 Four-NIC node variant

Type design-challenge · kind computed · tier L1 · 10 points

**Evidence required:** topology diagram, mapping, model arithmetic, workload recommendation with a rejected alternative.

| Criterion | Points |
|---|---|
| Topology diagram and mapping: 4 rails, GPU pair (2k, 2k+1) shares NIC k, both PIX | 3 |
| Model arithmetic: 24 GB/s per ring (48 / 2), t = 11.34 ms, busbw about 188.6 GB/s vs 370.7 GB/s for HX8, assumptions stated, labelled [MODELED] | 3 |
| Workload recommendation with a rejected alternative (e.g. 8 rails over dual-port NICs) | 4 |
