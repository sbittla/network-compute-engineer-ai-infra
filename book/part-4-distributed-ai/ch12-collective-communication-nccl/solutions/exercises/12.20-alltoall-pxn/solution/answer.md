# 12.20 — All-to-all and PXN on ORION

All numbers `[MODELED]` (`solve.py`). Relies on manuscript Section 12.8 ("All-to-all and PXN,
quantified"), Section 12.5 (busbw factor (n − 1)/n for all-to-all) and Figure 12.3 (rail alignment).
Effective NIC rate 45 GB/s (90 % of 50 GB/s); S = 1 GiB = 1,073,741,824 B.

**(a) Bytes per rank.** Each rank sends S/n to each of the other n − 1 ranks.

```text
chunk      = S/16 = 67.1 MB
intra-node = 7 chunks (the other 7 GPUs of its node, over NVLink)          = 469.8 MB
same-rail  = 1 chunk  (the GPU with the same index on the other node)      =  67.1 MB
cross-rail = 7 chunks (the other 7 GPUs of the other node)                 = 469.8 MB
total sent = 15/16 × S                                                     = 1,006.6 MB
```

**(b) PXN on.** Inter-node bytes per rank are 8 chunks = S/2. With PXN, GPU *j*'s NIC carries one chunk
from each of the 8 local GPUs, all bound for remote GPU *j* on rail *j*: 8 × 67.1 = 536.9 MB per
direction, the same for every NIC.

```text
T     = 536.9 MB / 45 GB/s = 11.93 ms
algbw = S/T = 1,073.7 MB / 11.93 ms = 90.0 GB/s
busbw = algbw × (n − 1)/n = 90.0 × 15/16 = 84.4 GB/s
```

The NVLink side (7 own chunks plus 7 forwarded chunks ≈ 0.94 GB at ≈ 450 GB/s, ≈ 2 ms) is not the
bottleneck, as the prompt assumes.

**(c) PXN off.** GPU *i*'s NIC now carries GPU *i*'s own 8 remote chunks: again 536.9 MB per
direction, so on an idle non-blocking fabric T, algbw and busbw are unchanged (11.93 ms, 90.0 and
84.4 GB/s). The difference is the path: the 7 cross-rail chunks leave on rail *i* and must cross a
spine to reach rail *j*.

```text
spine share, PXN off = 7 cross-rail chunks / 15 chunks sent = 7/15 = 46.7 %  (7/8 of inter-node bytes)
spine share, PXN on  = 0 %  (the cross-rail hop happens on NVLink; rail leaves connect both nodes)
```

**(d) 256 ranks, 32 nodes.** Remote chunks per rank: 248 of 255, i.e. (N − 1)/N × S = 31/32 × S per NIC.

```text
T     = 31/32 × 1,073.7 MB / 45 GB/s = 23.12 ms
algbw = 45 × 32/31 = 46.5 GB/s;  busbw = 46.5 × 255/256 = 46.3 GB/s
general: busbw ≈ 45 × N/(N − 1) × (n − 1)/n → one NIC's rate as N grows
spine share, PXN off = 31 × 7 / 255 = 217/255 = 85.1 %;  PXN on = 0 % (each rail leaf reaches all 32 nodes)
```

All-to-all busbw is bounded by one NIC per GPU because nothing is reduced on the way, which is why it
is ≈ 46–84 GB/s while a multi-node all-reduce reaches ≈ 350 GB/s.

**(e) Why the benchmark hides it.** Per-NIC bytes are the same either way, and ORION's 1:1 spines have
room for the cross-rail bytes when nothing else runs, so an idle-fabric `alltoall_perf` shows the same
busbw with PXN on and off. In production the PXN-off case puts 47–85 % of its bytes on spines shared
with other jobs and exposed to ECMP hash collisions, and an all-to-all finishes at the pace of its
slowest flow; PXN keeps those bytes on the rail leaves.

**Common mistakes.** Using 8 NICs × 45 GB/s as the ceiling (that is the node's egress, not a rank's);
forgetting the (n − 1)/n factor; counting the same-rail chunk as a spine crossing.
