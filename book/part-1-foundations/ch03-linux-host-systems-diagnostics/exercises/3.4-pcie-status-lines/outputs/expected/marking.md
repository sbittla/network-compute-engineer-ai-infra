# Marking scheme: 3.4 PCIe status lines

Type knowledge-check · kind computed · tier L1 · 4 points

**Evidence required:** A verdict per line, with the rule applied.

| Criterion | Points |
|---|---|
| (a) GPU at x8 of x16 under load is a fault (critical), because width below capability is never benign | 1 |
| (b) idle GPU at 2.5 GT/s x16 is probably benign, verify under load (power-saving downshift, full width) | 1 |
| (c) VGA 5 GT/s x1 of 5 GT/s x1 is healthy (status equals capability) | 1 |
| (d) rail NIC at Gen4 x16 under load is a fault (warning), with the bandwidth consequence (31.5 GB/s raw, about 26 GB/s achievable, below 50 GB/s line rate) | 1 |
