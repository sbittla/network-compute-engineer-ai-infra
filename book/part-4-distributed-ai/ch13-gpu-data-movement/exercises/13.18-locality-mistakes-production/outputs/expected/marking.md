# Marking scheme: 13.18 Locality mistakes hidden by idle benchmarks

Type reflection · kind written · tier L1 · 3 points

**Evidence required:** the locality mistakes and why they appear only under production load

| Criterion | Points |
|---|---|
| Names cross-socket NIC use, cross-rail placement and NUMA misbinding (or similar) | 1 |
| Explains that idle benchmarks find spare inter-socket/spine/DRAM capacity | 1 |
| Explains that production contention and variance are amplified by synchronous training | 1 |
