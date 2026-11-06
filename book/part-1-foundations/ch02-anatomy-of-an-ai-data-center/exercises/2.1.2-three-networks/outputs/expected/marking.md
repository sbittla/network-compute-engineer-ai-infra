# Marking scheme: 2.1.2 The three networks and their failure effects

Type knowledge-check · kind written · tier L1 · 3 points

**Evidence required:** Written answer naming the three networks and the effect of losing each.

| Criterion | Points |
|---|---|
| Backend loss makes distributed jobs hang or fail because collectives cannot complete | 1 |
| Frontend/storage loss stalls dataset reads and checkpoints and makes inference unreachable | 1 |
| OOB loss leaves running work untouched but removes power control, console and BMC telemetry | 1 |
