# Marking scheme: 5.21 When lstopo and nvidia-smi disagree

Type reflection · kind written · tier L1 · 3 points

**Evidence required:** short written answers (≤ 150 words each) citing specific mechanisms or data.

| Criterion | Points |
|---|---|
| Platform features the tree model misses (extra bridges, retimers, multi-level or firmware-hidden switches, NVSwitch functions, other PCI domains) | 1 |
| Or the driver classifies differently from the hwloc-derived rule | 1 |
| Action: lspci -tv, vendor block diagram, measured P2P bandwidth as tie-breakers | 1 |
