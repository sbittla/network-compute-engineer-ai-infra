# 3.9 `[MODELED]`

- gen5x16: 63.02 GB/s raw
- gen4x16: 31.51 GB/s raw
- gen4x2: 3.94 GB/s raw
- gen1x16: 4.00 GB/s raw
- DP all-reduce sent 7.656 GB; healthy 0.170 s; Gen4 x16 0.296 s
- extra <= 0.126 s/step -> 44.2 GPU-h/day (1.84/h vs shrink 32/h)
- waiting 88 GPU-h; planned stop pays only if repair < 5.7 min
- Gen3 x8: 339 GPU-h/day; planned stop pays if repair < 2.40 h
