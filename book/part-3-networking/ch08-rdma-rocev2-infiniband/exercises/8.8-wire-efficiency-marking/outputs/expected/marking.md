# Marking scheme: 8.8 Wire efficiency and DSCP marking

Type worked-problem · kind computed · tier L1 · 8 points

**Evidence required:** overhead per packet itemised; formula → substitution → result with units for each part; DSCP/ECN bit arithmetic shown.

| Criterion | Points |
|---|---|
| (a) 86 B overhead itemized; 2,048/2,134 = 0.9597 → 383.9 Gb/s | 2 |
| (b) 102 B overhead with IPv6; 4,096/4,198 = 0.9757 → 390.3 Gb/s | 2 |
| (c) 400 × 10⁹ / (4,198 × 8) = 11.91 M packets/s | 2 |
| (d) TC byte 26 → DSCP 6, ECN ECT(0); lands in the default lossy class; correct value 106 | 2 |
