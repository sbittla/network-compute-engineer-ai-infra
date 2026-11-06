# Marking scheme: 20-W1 MTU budget for an IPv6, VLAN-tagged variant

Type worked-problem · kind computed · tier L1 · 10 points

**Evidence required:** Formula, substituted values and result with units for each part; the two policy rules.

| Criterion | Points |
|---|---|
| (a) frame = IP MTU + 22 B; max host IP MTU 9,078 B | 2 |
| (b) IPv6 header budget 84 B; minimum IP MTU 4,180 B | 2 |
| (c) both inequalities shown: 9,022 <= 9,100 and 4,180 <= 9,000; valid | 1 |
| (d) overhead 106 B; efficiency 90.6 % / 97.5 %; 44.2 M / 11.9 M packets/s at 50 GB/s | 3 |
| (e) two rules with thresholds read from policy data (22 B, 84 B, min port MTU) | 2 |
