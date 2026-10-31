# O4 result `[MODELED]`

KV/request 2,684,354,560 B; aggregate 214.7 Gb/s

| Design | rho | TTFT | TPOT | Worst ITL | Link util |
|---|---|---|---|---|---|
| shared | 0.453 | 0.512 s | 23.0 ms | 374.8 ms | 0.0 % |
| disagg-rdma | 0.604 | 0.638 s | 16.7 ms | 32.5 ms | 7.9 % |
| disagg-tcp | 0.604 | 0.638 s | 17.5 ms | 232.4 ms | 107.4 % |

Per layer: prefill 4.53 ms; RDMA 0.20 ms; TCP 2.68 ms
FP8 KV: 107.4 Gb/s; RDMA 7.9 ms; TCP 108 ms
