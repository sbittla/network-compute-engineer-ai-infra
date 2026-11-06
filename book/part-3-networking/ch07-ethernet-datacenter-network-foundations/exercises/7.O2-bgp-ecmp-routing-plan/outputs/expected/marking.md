# Marking scheme: 7.O2 BGP/ECMP routing plan and failure behaviour

Type outline-mandated · kind computed · tier L1 · 10 points

**Evidence required:** the plan, a failure table with all five columns for all three failures, and consistency with your lab's `fabric_capacity` output.

| Criterion | Points |
|---|---|
| Plan: ASN plan, origination and inbound prefix filters per tier | 2 |
| Plan: maximum-paths ≥ 32 at leaves and ≥ 8 at spines with justification, BFD/BGP timers and a drain procedure | 2 |
| Failure table row for a link failure: detection, withdrawn routes, ECMP width 32, 12.4 / 11.2 Tb/s, workload impact | 2 |
| Failure table row for a spine failure: ECMP width 24, 9.6 Tb/s per leaf, bisection 38.4 Tb/s, workload impact | 2 |
| Failure table row for a leaf failure: rail prefix withdrawn, rail capacity 0, bisection 38.4 Tb/s, job restart | 2 |
