# Marking scheme: 3.10 Queues, stripes and packets

Type worked-problem · kind computed · tier L1 · 10 points

**Evidence required:** Every formula with substituted values; one sentence of interpretation per part.

| Criterion | Points |
|---|---|
| (a) Little's law, 830/s x 0.0486 s = 40.3 for nvme3n1 and 830 x 0.0491 = 40.8 for md0 | 2 |
| (b) 830 r/s x 512 KiB = 435 MB/s, cross-checked from the members | 2 |
| (c) 41 / 0.25 ms x 512 KiB = about 86 GB/s allowed, so the limit moves to the drives (31.5 GB/s of links) and then to GPU compute | 2 |
| (d) 15.25 / 224 = 6.8 %, consistent with %iowait 6.9 % | 2 |
| (e) 2.77 Mpps at MTU 9000, 16.3 Mpps at MTU 1500, ratio 5.9x (38 B of per-frame overhead) | 2 |
