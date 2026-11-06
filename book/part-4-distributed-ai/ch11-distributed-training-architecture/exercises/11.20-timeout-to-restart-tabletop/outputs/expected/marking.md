# Marking scheme: 11.20 From timeout to restart

Type troubleshooting · kind computed · tier L1 · 10 points

**Evidence required:** timeline, rank-to-hardware table, health decision per component, restart plan, and one sentence on what evidence would *prove* the cause.

| Criterion | Points |
|---|---|
| Rank-to-hardware table: n312 GPU 5 → rank 2493 (2488–2495); n141 NIC 2 → rank 1122 (1120–1127), rail 2 | 2 |
| Timeline from 01:00 to 03:12 with the watchdog delay | 2 |
| Health decision: ECC fault as most likely cause, NIC flaps correlated but separate; node-level quarantine for each | 2 |
| Restart plan: checkpoint before 02:58, replacement nodes or shrunken DP, validation criteria | 2 |
| States what would prove the cause (flight-recorder dumps showing rank 2493 behind, Xid before the timeout) | 2 |
