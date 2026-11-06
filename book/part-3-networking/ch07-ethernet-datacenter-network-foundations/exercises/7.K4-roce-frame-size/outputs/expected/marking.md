# Marking scheme: 7.K4 RoCEv2 frame size and the RDMA path MTU

Type knowledge-check · kind computed · tier L1 · 4 points

**Evidence required:** a header-by-header sum; the selected MTU with justification.

| Criterion | Points |
|---|---|
| Header-by-header sum to 4,174 B (14 + 20 + 8 + 12 + 16 + 4,096 + 4 + 4); 4,158 B accepted only if RETH is explicitly excluded | 2 |
| Active MTU 1,024 at netdev MTU 1500, with the ≈ 1,456 B payload-space argument | 1 |
| Reason for host MTU 9000: lets the device select 4,096 path MTU (needs IP MTU above ≈ 4,200 B) and gives TCP jumbo frames | 1 |
