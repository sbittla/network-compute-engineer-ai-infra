# 17-M2 replay: urgent-eval QOS `[SIMULATED]`

| Job | Before (J01 at 100) | After (+ urgent-eval QOS for J05) |
|---|---|---|
| J05 | InsufficientCapacity | ['orion-n22', 'orion-n24'] |
| J10 | ['orion-n26'] | ['orion-n26'] |
| J01 | ['orion-n13', 'orion-n18', 'orion-n22', 'orion-n24'] | InsufficientCapacity |
| J12 | ['orion-n31'] | ['orion-n31'] |
| J02 | ['orion-n14'] | ['orion-n14'] |
| J03 | QuotaExceeded | QuotaExceeded |
| J04 | InvalidRequest | InvalidRequest |
| J08 | InsufficientCapacity | ['orion-n13', 'orion-n18'] |
| J07 | ['orion-n20'] | ['orion-n20'] |
| J11 | ['orion-n29'] | ['orion-n29'] |
| J13 | ['orion-n30'] | ['orion-n30'] |
| J15 | ['orion-n29'] | ['orion-n29'] |
| J06 | Fragmentation | Fragmentation |
| J14 | QuotaExceeded | QuotaExceeded |
| J09 | ['orion-n20'] | ['orion-n20'] |

GPUs placed: 69 → 69. New GPUs by tenant: {'before': {'finetune': 14, 'inference': 15, 'pretrain': 32, 'research': 0, 'search': 8}, 'after': {'finetune': 14, 'inference': 15, 'pretrain': 16, 'research': 16, 'search': 8}}.
