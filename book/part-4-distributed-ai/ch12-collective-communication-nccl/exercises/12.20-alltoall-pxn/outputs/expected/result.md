# 12.20 — All-to-all and PXN `[MODELED]`

| Case | n | Chunk (MB) | NIC bytes/dir (MB) | Time (ms) | algbw (GB/s) | busbw (GB/s) | Spine share, PXN off | PXN on |
|---|---|---|---|---|---|---|---|---|
| 2 nodes | 16 | 67.1 | 536.9 | 11.93 | 90.0 | 84.4 | 46.7 % | 0 % |
| 32 nodes | 256 | 4.19 | 1040.2 | 23.12 | 46.5 | 46.3 | 85.1 % | 0 % |

Two nodes, per rank: intra-node 469.8 MB, same-rail 67.1 MB, cross-rail 469.8 MB.
