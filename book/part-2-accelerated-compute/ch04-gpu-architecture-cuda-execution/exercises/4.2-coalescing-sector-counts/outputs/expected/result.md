# Exercise 4.2 — sectors per warp load `[MODELED]`

Useful bytes per warp = 32 × 4 B = 128 B.

| Case | Stride (elements) | Sectors | Bytes fetched | Useful fraction |
|---|---|---|---|---|
| a_consecutive | 1 | 4 | 128 B | 100.0 % |
| b_stride_2 | 2 | 8 | 256 B | 50.0 % |
| c_stride_32 | 32 | 32 | 1,024 B | 12.5 % |
