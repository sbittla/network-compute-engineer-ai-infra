# Marking scheme: 8.20 Correlation versus a discriminating test

Type reflection · kind written · tier L1 · 3 points

**Evidence required:** one correlation-only signal and the missing causal link.

| Criterion | Points |
|---|---|
| A correlation-only signal (e.g. timing of the config push, 'only n05 changed') | 1 |
| The missing causal link: mechanism GID index 2 = RoCEv1 → not routable → no ACKs | 1 |
| A test that changes only the suspect variable (-x 3 passes, -x 2 fails) plus consistent leaf counters | 1 |
