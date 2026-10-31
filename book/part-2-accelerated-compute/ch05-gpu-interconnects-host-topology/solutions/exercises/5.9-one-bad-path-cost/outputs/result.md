# Exercise 5.9 — one bad path `[MODELED]`

Ring factor 2 × 255 / 256 = 1.99219; bytes per ring = 134,217,728 B; moved per ring = 267,386,880 B.

| Case | Slowest path | t | busbw |
|---|---|---|---|
| a_all_pix | 48 GB/s | 5.771 ms | 370.7 GB/s |
| b_one_gen5_x8_nic | 27 GB/s | 10.103 ms | 211.7 GB/s |
| c_one_node_no_gdr | 18 GB/s | 15.055 ms | 142.1 GB/s |

(d) One node of 32 (3.1 %) without GDR costs 62 % of busbw: every ring visits every node.
