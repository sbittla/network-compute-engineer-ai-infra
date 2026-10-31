# 11.2 — Bytes per parameter (BF16 mixed precision, Adam)

**Where the 16 bytes go** (Section 11.2, Table 11.1):

| Item | Precision | Bytes |
|---|---|---|
| Weights used in forward/backward | BF16 | 2 |
| Gradients | BF16 | 2 |
| Master copy of weights | FP32 | 4 |
| Adam first moment (m) | FP32 | 4 |
| Adam second moment (v) | FP32 | 4 |
| **Total** | | **16** |

The 12 bytes of FP32 optimizer state are three quarters of the model state, which is why sharding the
optimizer (ZeRO-1) gives the largest saving for the smallest communication change.

**Per local parameter with DP = 8** `[MODELED]`:

```text
ZeRO-1 (optimizer sharded)            = 2 + 2 + 12/8        = 2 + 2 + 1.5  = 5.5 B
ZeRO-2 (optimizer + gradients)        = 2 + (2 + 12)/8      = 2 + 1.75     = 3.75 B
ZeRO-3 (optimizer + grads + weights)  = (2 + 2 + 12)/8      = 16/8         = 2.0 B
```

ZeRO-3 also needs transient buffers to all-gather the current (and prefetched) layer's full weights
before using them; the lab model adds two layers of BF16 weights for that.

**Check against W-TRAIN.** Baseline TP = 8, PP = 4 → P = 70e9/32 = 2.1875e9 local parameters; with
ZeRO-1 over DP = 8: 2.1875e9 × 5.5 B = 12.03 GB of model state — the lab's `memory_baseline` value.

**Common wrong answers.** 20 B/param — acceptable only if the learner explicitly adds a 4 B FP32
gradient-accumulation buffer and says so; dividing the weights by DP under ZeRO-1; forgetting the
FP32 master weights (12 → 8 B).
