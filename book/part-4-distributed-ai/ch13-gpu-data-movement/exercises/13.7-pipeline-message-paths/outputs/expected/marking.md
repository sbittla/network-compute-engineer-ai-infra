# Marking scheme: 13.7 One pipeline message, two paths

Type worked-problem · kind computed · tier L1 · 7 points

**Evidence required:** a two-row table and both times with arithmetic

| Criterion | Points |
|---|---|
| Table row GDR: 0 host copies, 2 PCIe transfers, 16.8 MB PCIe bytes | 2 |
| Table row host-staged: 2 host copies, 4 PCIe transfers, 33.6 MB PCIe bytes | 2 |
| GDR time 8.39 MB / 45 GB/s = 186 µs (+ about 10 µs fixed) | 1 |
| Unpipelined host-staged bound 168 + 186 + 168 = 522 µs with arithmetic | 2 |
