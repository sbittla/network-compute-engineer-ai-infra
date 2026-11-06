# Marking scheme: 1.2 Scale-up versus scale-out for two workloads

Type outline-mandated · kind computed · tier L1 · 20 points

**Evidence required:** A table of the eight lower bounds with formula and units; the dominant resource per workload with ceiling fraction; named metrics with expected direction and magnitude; one placement proposal with its constraint.

| Criterion | Points |
|---|---|
| Eight lower bounds correct with units (A 0.566 ms, 6.02 ms, 0.327 ms, 0; B 0.404 s, 0.149 s, 0.089 s, 0.600 s), 1 point each | 8 |
| Dominant resource and the network that matters named for each workload (A memory, scale-up; B scale-out), with ceiling fractions 0.63 and 0.40 | 4 |
| Two telemetry signals per workload with expected direction and magnitude | 4 |
| Placement proposal for B that moves all-to-all onto NVLink, with the eight-GPU NVLink domain and HBM capacity named as the limit | 4 |
