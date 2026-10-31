# Exercise 20.2 — result `[MODELED]`

a. Frame = IP MTU + 14 + 4 + 4 = IP MTU + 22. Max IP MTU = 9,100 − 22 = **9,078 B**.
b. Budget = 64 + (40 − 20) = 84 B (fixed 64 B + 20 B extended). Min IP MTU = 4,096 + 84 = **4,180 B**.
c. 9,000 + 22 = 9,022 ≤ 9,100 and 4,180 ≤ 9,000: **valid**.
d. Overhead = 106 B per packet; line rate 50 × 10⁹ B/s.

| RDMA MTU (B) | Wire bytes | Efficiency | Packets/s |
|---|---|---|---|
| 1,024 | 1,130 | 90.62 % | 44.25 M |
| 4,096 | 4,202 | 97.48 % | 11.90 M |

Efficiency gain 4,096 vs 1,024: 7.57 %.

e. Rules evaluated with policy data 22 B / 84 B: {'good_fabric': True, 'good_rdma': True, 'host_9100_fabric': False, 'host_4160_rdma': False}.
