# Marking scheme: K1 DCQCN roles in the 12:1 incast

Type knowledge-check · kind written · tier L1 · 4 points

**Evidence required:** three device names, the packet name, DSCP and TC values.

| Criterion | Points |
|---|---|
| CP = orion-be-leaf-r3 egress queue on eth1/5 toward orion-n05 | 1 |
| NP = orion-n05's NIC (mlx5_3), the receiver that generates CNPs | 1 |
| RP = each of the 12 sending NICs | 1 |
| NP→RP packet is the CNP, DSCP 48, TC 6 (strict priority) | 1 |
