# T1 — The quiet downtrain `[MODELED]`

- Gen5 x16: 32 × 16 × 128/130 / 8 = 63.0 GB/s/dir; x8: 31.5 GB/s/dir (≈ 25–27.5 achievable) < 50 GB/s NIC line rate
- orion-n10 NIC TX 985 Gb/s vs peers 1,050–1,080: 6.2 %–8.8 % lower (≈ 7.5 %)
- Restart cost = 128 GPUs × (15 + 15) min = 64 GPU-h; degraded running wastes 128 × 0.09 = 11.52 GPU-h per hour
- Break-even remaining runtime = 64 / 11.52 = 5.6 h
