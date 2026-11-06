# K3 — Bandwidth unit conversions

Source: manuscript Section 1.5 and Table 1.5; ORION values `[VENDOR-SPEC, 2026-10]` class. `solve.py`
recomputes each value.

```text
(a) 400 Gb/s ÷ 8 bit/B                          = 50 GB/s (per direction; line rate, not goodput)
(b) NVLink "900 GB/s" is total bidirectional     → 900 ÷ 2 = 450 GB/s per direction per GPU
(c) 8 backend NICs × 400 Gb/s = 3,200 Gb/s       → 3,200 ÷ 8 = 400 GB/s per direction per node
```

Two traps: (1) network rates are quoted in bits per second and per direction, while vendor NVLink figures
are often quoted in bytes per second summed over both directions; (2) the node's 400 GB/s of
backend bandwidth is still 9× less per GPU than NVLink (50 GB/s against 450 GB/s), the ratio that drives
the TP-inside-the-node placement rule. Line rate also exceeds achievable throughput: headers and protocol
overhead reduce RDMA goodput by several percent.

**Marking note:** the key gives 2 points (half credit without numbers); this folder scores it out of 4.
