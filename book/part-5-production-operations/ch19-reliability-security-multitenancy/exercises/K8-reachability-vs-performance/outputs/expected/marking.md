# Marking scheme: K8 Reachability vs performance

Type knowledge-check · kind written · tier L1 · 5 points

**Evidence required:** mechanism through shared links/PFC; two mitigations

| Criterion | Points |
|---|---|
| States VRF/VNI isolate reachability, not shared spine links and switch buffers | 1 |
| Mechanism: B's congestion fills shared queues; ECN marks and PFC pauses (HOL blocking, pause spreading) slow A | 2 |
| Two valid mitigations (separate leaf groups/spine planes, QoS classes with buffer allocation, rate limits, CC tuning) | 2 |
