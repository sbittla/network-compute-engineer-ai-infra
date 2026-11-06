# Marking scheme: 5.9 Modeled cost of one bad path

Type worked-problem · kind computed · tier L1 · 10 points

**Evidence required:** three results with arithmetic; one-paragraph explanation; label `[MODELED]`.

| Criterion | Points |
|---|---|
| (a) all PIX: t = 5.771 ms, busbw 370.7 GB/s with the ring factor 1.99219 and 134,217,728 B per ring | 2 |
| (b) one Gen5 x8 NIC: slowest ring 10.10 ms, busbw 211.7 GB/s | 3 |
| (c) one node without GDR: 15.055 ms, busbw 142.1 GB/s | 2 |
| (d) every ring visits every node and runs at its slowest member: 1/32 of the nodes costs about 62 % of busbw; labelled [MODELED] | 3 |
