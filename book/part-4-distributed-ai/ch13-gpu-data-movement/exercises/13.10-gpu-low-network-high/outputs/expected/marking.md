# Marking scheme: 13.10 GPU utilization low, network utilization high (O2)

Type outline-mandated · kind lab · tier L1 · 12 points

**Evidence required:** a per-window verdict table with evidence fields, the decoy rejected, and the misleading metric explained

| Criterion | Points |
|---|---|
| Steps 0-19: synchronization from data imbalance on rank 12, with two independent fields (tokens +31 %, normal clocks; wait up, transfer normal) | 3 |
| Steps 20-29: thermal straggler rank 37 hidden behind rank 12 (clock -22 %, 90 °C, sw_thermal_slowdown, tokens normal) | 3 |
| Steps 30-59: communication-bound on rail 2 (transfer 120 to 198 ms, retransmissions about 3,200 per step on index 2, burst rate 359 to 222 Gb/s) | 3 |
| Decoy rank 51 rejected (84 °C, normal clocks, no reason) | 1 |
| Misleading metric utilization.gpu 99.7 % explained (spinning NCCL kernels); step-averaged NIC rate hides bursts | 2 |
