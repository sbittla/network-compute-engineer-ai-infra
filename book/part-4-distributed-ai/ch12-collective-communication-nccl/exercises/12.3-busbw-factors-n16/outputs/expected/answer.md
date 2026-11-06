# 12.3 — nccl-tests busbw correction factors for n = 16

busbw = algbw × factor, where the factor converts the algorithm bandwidth (S/t) into the bandwidth each
rank's busiest link must sustain for an optimal algorithm (nccl-tests PERFORMANCE.md; Section 12.5).

| Collective | Factor | n = 16 |
|---|---|---|
| All-reduce | 2(n − 1)/n | 2 × 15/16 = **1.875** |
| All-gather | (n − 1)/n | 15/16 = **0.9375** |
| Reduce-scatter | (n − 1)/n | 15/16 = **0.9375** |
| Broadcast | 1 | **1** |
| All-to-all | (n − 1)/n | 15/16 = **0.9375** |

All values `[MODELED]` (definitions). **Why these factors.** In a ring all-reduce every rank sends
2(n − 1) chunks of S/n, i.e. 2(n − 1)/n × S bytes; reduce-scatter and all-gather are each half of that;
in all-to-all each rank sends (n − 1)/n of its buffer to the others; broadcast moves the whole buffer
once over each link of a pipeline.

**Use.** The factor makes busbw comparable across rank counts and with link speed: a 16-rank
all-reduce at 352 GB/s busbw on two HX8 nodes is compared with the node's 400 GB/s NIC egress, not with
algbw (188 GB/s). Common mistakes: using 2(n − 1)/n for all-gather; dividing instead of multiplying;
using n = 2 (nodes) instead of 16 (ranks).
