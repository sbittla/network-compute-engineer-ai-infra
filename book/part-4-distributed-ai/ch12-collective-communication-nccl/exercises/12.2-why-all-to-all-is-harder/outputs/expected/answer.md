# 12.2 — Why all-to-all is harder than all-reduce of the same size

Each rank in an all-to-all sends (n − 1)/n of its buffer once — fewer bytes than all-reduce's
2(n − 1)/n — yet it is usually slower and harder on the fabric:

1. **Fan-out and incast.** A ring all-reduce is neighbour-to-neighbour: each rank talks to one
   successor, and every link carries one steady flow. In all-to-all every rank sends to n − 1
   destinations at once, so every receiver gets n − 1 concurrent flows: incast. Switch egress buffers
   fill, ECN marks and PFC pauses rise (Chapter 9), and with many small flows the fabric spends its
   time in congestion control rather than at line rate.
2. **Cross-rail paths.** On ORION's rail-optimized fabric, all-reduce rings stay on one rail (GPU i ↔
   NIC i ↔ rail i). All-to-all sends GPU i's data to GPU j on another node for every j, so most traffic
   must change rail: either through the spines (an extra hop, ECMP collisions, shared with other jobs)
   or by forwarding over NVLink first (PXN), which costs NVLink bandwidth.
3. **Data dependence (MoE).** In expert parallelism the volume per destination depends on the router's
   choices; hot experts create persistent imbalance, so the slowest destination sets the completion
   time, and the pattern changes every step, defeating static tuning.

Any two with their mechanism earn full marks (Section 12.2; Chapter 10 Exercise 10.T1 shows the
operational consequence: discards and PFC on all spine uplinks during an all-to-all window).
