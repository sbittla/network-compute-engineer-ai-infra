# 7.K4 — result `[MODELED]`

- Frame = ethernet 14 + ipv4 20 + udp 8 + bth 12 + reth 16 + icrc 4 + fcs 4 + payload 4,096 = **4,174 B** (IP packet 4,156 B; 4,158 B without RETH)
- Netdev MTU 1500: space for payload = 1500 − 20 − 8 − 12 − 4 = 1,456 B (less 16 B RETH) → largest IB MTU that fits = **1,024**
- Netdev MTU 9000 → active MTU 4,096; 4,096 needs an IP MTU ≥ 4,156 B
