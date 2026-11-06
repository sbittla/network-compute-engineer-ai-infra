# Marking scheme: 5.16 One node slow after a rack move

Type troubleshooting · kind written · tier L1 · 10 points

**Evidence required:** ranked hypotheses with tests, root cause, traffic-path explanation, fix, validation.

| Criterion | Points |
|---|---|
| Ranked hypotheses with tests: swapped cables (LLDP), optics/FEC (counters), GDR disabled (/GDRDMA), PCIe link degradation (LnkSta) | 3 |
| Root cause: rail 4/5 patch-panel swap on orion-n12 during the rack move | 2 |
| Traffic-path explanation: in the stretched L2 domain the swapped NIC still reaches peers; NCCL still pairs GPU4 with mlx5_4, so rail-4 and rail-5 traffic to orion-n12 crosses the spines, adding a hop and tail latency (ECMP collisions on the EVPN-VXLAN underlay; an STP/MLAG answer is accepted if stated) | 3 |
| Safe fix (drain at checkpoint, swap cords per plan) and validation (LLDP, mapping diff, nccl-tests, p99 over ≥ 5 runs) | 2 |
