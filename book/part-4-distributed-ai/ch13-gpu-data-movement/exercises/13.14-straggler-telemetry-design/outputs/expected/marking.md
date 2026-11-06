# Marking scheme: 13.14 Straggler telemetry for ORION-XL

Type design-challenge · kind computed · tier L1 · 12 points

**Evidence required:** field list, volume estimate with arithmetic, alert rules, and a defence paragraph

| Criterion | Points |
|---|---|
| Field list: CUDA-event phases, entry skew, tokens, clocks/reasons/temp/power, NIC throughput and retransmissions, map keys | 3 |
| Sampling interval (every 10-50 steps per rank plus DCGM 1 Hz) and skew measured without synchronized clocks | 2 |
| Volume estimate with consistent arithmetic (e.g. 4,096 x 20 x 8 B x 4,320 samples = 2.8 GB/day) | 3 |
| Alert rules with thresholds and statistics (robust z ≥ 6 in ≥ 25 % of a window, wait fraction > 10 %, rail-grouped retransmission ratio) | 2 |
| Defended fidelity-versus-overhead trade-off | 2 |
