# 13.1 result `[MODELED]`

- NIC bytes = DP + PP = 7.66 + 2.15 = 9.81 GB per GPU per step
- NVLink (TP) bytes = 1.20 TB
- Ratio = 1.200e+12 / 9.810e+09 = 122.3× (vs DP alone 156.7×)
- Cause: tensor parallelism's per-layer collectives stay on NVLink.
