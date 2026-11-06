# Marking scheme: 8.5 Entropy from the UDP source port

Type knowledge-check · kind written · tier L1 · 5 points

**Evidence required:** ECMP hashing mechanism; collision explanation; two mitigations with their trade-off.

| Criterion | Points |
|---|---|
| Mechanism: source port is the per-QP entropy field hashed by ECMP; one QP stays on one path | 2 |
| Collision explanation: two QPs per pair → few flows; QPNs and ports change run to run, so collisions and bandwidth vary | 1 |
| Two mitigations, each with its trade-off (more QPs, rail-local placement, adaptive routing/spraying) | 2 |
