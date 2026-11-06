# Marking scheme: 5.12 P2P versus host-staged transfer

Type outline-mandated · kind computed · tier L1 · 10 points

**Evidence required:** annotated lists, four times, NUMA argument.

| Criterion | Points |
|---|---|
| (a) NVLink P2P: one DMA GPU2 HBM → GPU6 HBM, event completion; host-staged pinned: D2H, event/sync, H2D with memory locations | 3 |
| (b) pageable: extra CPU copies through the driver's bounce buffer and host-blocking calls | 2 |
| (c) NVLink 11.6 ms; host-staged unpipelined 165.2 ms; pipelined in 64 MiB chunks about 83.9 ms; labelled [MODELED] | 3 |
| (d) GPU2 is on socket 0 and GPU6 on socket 1, so either buffer placement puts one leg across the inter-socket link | 2 |
