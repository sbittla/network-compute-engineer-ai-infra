# 17-W2 replay `[SIMULATED]`

| Job (variant order) | Baseline | J01 at priority 100 |
|---|---|---|
| J10 | ['orion-n26'] | ['orion-n26'] |
| J01 | InsufficientCapacity | ['orion-n13', 'orion-n18', 'orion-n22', 'orion-n24'] |
| J05 | ['orion-n22', 'orion-n24'] | InsufficientCapacity |
| J12 | ['orion-n31'] | ['orion-n31'] |
| J02 | ['orion-n14'] | ['orion-n14'] |
| J03 | QuotaExceeded | QuotaExceeded |
| J04 | InvalidRequest | InvalidRequest |
| J08 | ['orion-n13', 'orion-n18'] | InsufficientCapacity |
| J07 | ['orion-n20'] | ['orion-n20'] |
| J11 | ['orion-n29'] | ['orion-n29'] |
| J13 | ['orion-n30'] | ['orion-n30'] |
| J15 | ['orion-n29'] | ['orion-n29'] |
| J06 | Fragmentation | Fragmentation |
| J14 | QuotaExceeded | QuotaExceeded |
| J09 | ['orion-n20'] | ['orion-n20'] |

GPUs placed: baseline 69, variant 69.
New GPUs by tenant: baseline {'finetune': 14, 'inference': 15, 'pretrain': 16, 'research': 16, 'search': 8}; variant {'finetune': 14, 'inference': 15, 'pretrain': 32, 'research': 0, 'search': 8}.
