# Marking scheme: 11.6 The timeout victim

Type knowledge-check · kind written · tier L1 · 4 points

**Evidence required:** explanation plus two named artifacts.

| Criterion | Points |
|---|---|
| Explains that all healthy ranks block in the collective the faulty rank never joins, so the first logger is arbitrary | 2 |
| Artifact 1: NCCL flight-recorder dumps (lowest SeqNum / mismatched op) | 1 |
| Artifact 2: py-spy stacks of all ranks, or host Xid logs / scheduler events / launcher exit summary | 1 |
