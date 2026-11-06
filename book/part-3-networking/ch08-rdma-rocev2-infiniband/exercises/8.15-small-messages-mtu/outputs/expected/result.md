# 8.15 — result `[MODELED]`

Port MTU 1500 B; QP path MTU 4,096; RDMA WRITE (RETH on the first packet).

| Message (B) | Largest IP packet (B) | At a 1,500-byte port |
|---|---|---|
| 2 | 62 | pass |
| 4 | 64 | pass |
| 8 | 68 | pass |
| 16 | 76 | pass |
| 32 | 92 | pass |
| 64 | 124 | pass |
| 128 | 188 | pass |
| 256 | 316 | pass |
| 512 | 572 | pass |
| 1,024 | 1,084 | pass |
| 2,048 | 2,108 | dropped |
| 4,096 | 4,156 | dropped |
| 8,192 | 4,156 | dropped |
| 16,384 | 4,156 | dropped |

- Last perftest row that completes: **1,024 B**; every larger size sends at least one packet > 1,500 B.
- `ibv_rc_pingpong` defaults (4,096 B SENDs at path MTU 1,024): largest packet 1,068 B → passes = True.
- `ib_write_bw -m 1024`: full sweep passes = True; DF ping 8,972 B passes = False, 1,472 B passes = True.
