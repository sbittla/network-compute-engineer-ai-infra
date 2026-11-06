# Marking scheme: 6.3 4.6 TB/s of DRAM bandwidth on a 3.35 TB/s GPU

Type knowledge-check · kind written · tier L1 · 3 points

**Evidence required:** two mechanisms, one counter or experiment each.

| Criterion | Points |
|---|---|
| Mechanism 1: part of the data served from the 50 MB L2 (producer output still resident, or output absorbed by L2 write-back), so traffic never reached DRAM; only what fits in L2 | 1 |
| Mechanism 2: bytes computed from tensor shapes double-count or assume a layout not used | 1 |
| Check: Nsight Compute dram__bytes_read.sum / dram__bytes_write.sum and lts__t_bytes, or rerun with an input larger than L2 | 1 |
