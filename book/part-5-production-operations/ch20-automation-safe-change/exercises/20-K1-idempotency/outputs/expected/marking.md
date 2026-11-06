# Marking scheme: 20-K1 Idempotent operations

Type knowledge-check · kind written · tier L1 · 4 points

**Evidence required:** Written answer (2–5 sentences) that names the mechanism, not just the term.

| Criterion | Points |
|---|---|
| Correct definition: once or many applications yield the same end state (not 'safe') | 1 |
| A naturally idempotent ORION operation (e.g. set MTU 9000, gNMI replace of a QoS map) | 1 |
| A non-idempotent ORION operation (firmware flash + reset, reboot, append, IP allocation) | 1 |
| Retry-safety technique: check running state before acting, read back, idempotency key per change/target | 1 |
