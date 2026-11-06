# K5 — TP volume and time `[MODELED]`

- Activation per all-reduce: 4,096 × 8,192 × 2 B = 67.1 MB
- Ring bytes per GPU: 2 × 7/8 × 67.1 MB = 117.4 MB
- Per step per GPU: 117.4 MB × 4 × 20 × 128 = 1.20 TB
- Over NVLink at 360 GB/s: 3.34 s
- Over a NIC at 40 GB/s: 30.1 s, longer than the 17.4 s step
