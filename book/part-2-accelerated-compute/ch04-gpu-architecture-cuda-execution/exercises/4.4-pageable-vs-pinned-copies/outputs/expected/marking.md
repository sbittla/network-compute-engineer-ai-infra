# Marking scheme: 4.4 Pageable versus pinned cudaMemcpyAsync

Type knowledge-check · kind written · tier L1 · 3 points

**Evidence required:** bandwidth, host-blocking and overlap arguments.

| Criterion | Points |
|---|---|
| Bandwidth: driver stages through a pinned bounce buffer with a CPU memcpy (about 10-25 GB/s vs about 50 GB/s pinned on Gen5 x16) | 1 |
| Host blocking: the call returns only after staging (or after completion for D2H), so the CPU cannot run ahead | 1 |
| No overlap: the copy serializes with the stream and cannot run concurrently with kernels on a side stream | 1 |
