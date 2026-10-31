# 8.8 — result `[MODELED]`

- (a) overhead 82 + 4 VLAN = 86 B; 2,048 / 2,134 = 0.9597 → **383.9 Gb/s**
- (b) overhead 82 + 20 IPv6 = 102 B; 4,096 / 4,198 = 0.9757 → **390.3 Gb/s**
- (c) 400 × 10⁹ / (4,198 × 8) = **11.91 M packets/s**
- (d) `NCCL_IB_TC=26` = 0b00011010 → DSCP **6**, ECN **ECT(0)** → ORION TC 0 (default lossy); correct value 26 × 4 + 2 = **106**
