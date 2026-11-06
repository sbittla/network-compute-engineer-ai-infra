# Marking scheme: 8.2 Silent arrival

Type knowledge-check · kind written · tier L1 · 4 points

**Evidence required:** mechanism stated; two notification methods with a cost each.

| Criterion | Points |
|---|---|
| Mechanism: one-sided WRITE is placed by the target NIC via the rkey, consumes no RECV WQE, so no target completion exists | 2 |
| Method 1 with a cost (e.g. polling a flag written last: burns a core, relies on ordering) | 1 |
| Method 2 with a cost (e.g. SEND or WRITE-with-immediate: needs posted RECVs, RNR risk, a CQE per message) | 1 |
