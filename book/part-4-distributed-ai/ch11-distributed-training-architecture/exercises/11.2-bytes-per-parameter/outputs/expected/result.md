# 11.2 — Bytes per parameter `[MODELED]`

16 B = 2 (BF16 weights) + 2 (BF16 grads) + 12 (FP32 master + Adam m + v).

| Stage (DP = 8) | Formula | Bytes/param |
|---|---|---|
| ZeRO-1 | 2 + 2 + 12/8 | 5.5 |
| ZeRO-2 | 2 + (2 + 12)/8 | 3.75 |
| ZeRO-3 | 16/8 | 2.0 |

Cross-check: W-TRAIN baseline ZeRO-1 states = 2.1875e9 x 5.5 B = 12.03 GB.
