# Marking scheme: 17-K6 Topology Manager rejection loop

Type knowledge-check · kind written · tier L1 · 5 points

**Evidence required:** Where the decision is made (scheduler vs kubelet) and the resulting loop.

| Criterion | Points |
|---|---|
| Decision is made by the kubelet at admission after binding; scheduler sees only counts | 2 |
| Pod Failed with TopologyAffinityError; controller recreates it and the scheduler binds the same node again (loop) | 2 |
| A valid mitigation (socket-sized replicas, scheduler-visible topology via DRA/labels, best-effort during migration) | 1 |
