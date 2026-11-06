# Marking scheme: 8.15 Small messages work, large ones do not

Type troubleshooting · kind computed · tier L1 · 20 points

**Evidence required:** hypotheses ranked with reasons; real commands; packet-size arithmetic showing which sizes fit; fix routed through the Fabric team with change control; validation criteria.

| Criterion | Points |
|---|---|
| (a) Three hypotheses ranked with reasons: switch-port MTU 1500 first; QoS/PFC and optics ruled down; host MTU excluded by evidence | 5 |
| (b) Two safe discriminating tests with real commands (DF ping 8,972 vs 1,472; ib_write_bw -m 1024) | 5 |
| (c) Packet-size arithmetic: 1,024-byte message → 1,084 B ≤ 1,500 passes; 2,048 → 2,108 B dropped; pingpong default MTU 1,024 explained | 6 |
| (d) Fix through the Fabric team with change control and measurable validation | 4 |
