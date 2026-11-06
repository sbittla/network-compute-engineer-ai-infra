# Marking scheme: 13.1 NVLink versus NIC bytes per step

Type knowledge-check · kind computed · tier L1 · 5 points

**Evidence required:** the two volumes from Table 13.1 and the parallelism responsible

| Criterion | Points |
|---|---|
| Quotes TP 1.20 TB (NVLink) and DP + PP 7.66 + 2.15 = 9.81 GB (NIC) per GPU per step from Table 13.1 | 2 |
| Ratio computed with arithmetic: 1.20e12 / 9.81e9 = 122 (accept 120-160 with working) | 1 |
| Names tensor parallelism (collectives per layer per micro-batch) as the cause | 1 |
| Evidence label [MODELED] on the volumes and ratio | 1 |
