# Marking scheme: 3.1 Reading the CPU map

Type knowledge-check · kind computed · tier L1 · 4 points

**Evidence required:** CPU lists, and one sentence that names the socket of GPU 2 and the consequence.

| Criterion | Points |
|---|---|
| Socket 1 first hardware threads are CPUs 56-111 | 1 |
| Their SMT siblings are CPUs 168-223 | 1 |
| GPU 2 (3a:00.0) sits under socket 0 (NUMA node 0), so CPUs 56-63 are on the wrong socket | 1 |
| Consequence stated (H2D copies and launches cross the inter-socket link, raising latency and lowering bandwidth) with a fix (bind to socket-0 cores) | 1 |
