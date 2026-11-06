# Marking scheme: 12.20 All-to-all and PXN on ORION

Type worked-problem · kind computed · tier L1 · 8 points

**Evidence required:** formula → substitution → result for (a)–(d), and two sentences for (e).

| Criterion | Points |
|---|---|
| (a) chunk S/16 = 67.1 MB; intra-node 7 chunks = 469.8 MB, same-rail 1 chunk = 67.1 MB, cross-rail 7 chunks = 469.8 MB (1,006.6 MB sent) | 2 |
| (b) every NIC carries S/2 = 536.9 MB per direction; T = 536.9 MB / 45 GB/s = 11.93 ms; algbw 90.0 GB/s; busbw = 90.0 × 15/16 = 84.4 GB/s | 2 |
| (c) same time and busbw with PXN off on an idle 1:1 fabric; spine share 7/15 = 46.7 % with PXN off, 0 % with PXN on | 1 |
| (d) 32 nodes, n = 256, T = 31/32 × S / 45 GB/s = 23.12 ms, busbw 46.3 GB/s; spine share 217/255 = 85.1 % with PXN off, 0 % with PXN on | 2 |
| (e) idle non-blocking spines absorb the cross-rail bytes; in production they are shared and hashed, and the all-to-all runs at its slowest flow | 1 |
