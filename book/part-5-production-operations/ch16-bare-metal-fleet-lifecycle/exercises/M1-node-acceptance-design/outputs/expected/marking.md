# Marking scheme: M1 Node acceptance test design

Type outline-mandated · kind written · tier L1 · 20 points

**Evidence required:** A table with ≥ 12 checks in fail-fast order; every threshold labelled with its evidence class; a total duration estimate; the policy-version field you will record.

| Criterion | Points |
|---|---|
| Coverage: ≥ 12 checks spanning discovery, memory, NIC link, storage, thermals, burn-in, NVLink, RDMA pairs, single-node NCCL | 8 |
| Fail-fast order (cheap inventory/topology first, burn-in late, NCCL last) | 4 |
| Thresholds labelled with evidence class; FAIL vs WARN classes correct | 5 |
| Total duration (≈ 25 h with 24 h burn-in) and policy-version field recorded | 3 |
