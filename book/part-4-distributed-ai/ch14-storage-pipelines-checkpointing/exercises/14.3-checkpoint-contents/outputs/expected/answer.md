# 14.3 — What is in a checkpoint: worked solution

**Byte breakdown (Section 14.8) `[MODELED]`:**

| Component | Bytes/param | In training state | In checkpoint |
|---|---|---|---|
| BF16 weights | 2 | yes | yes |
| BF16 gradients | 2 | yes | **no** |
| FP32 master weights | 4 | yes | yes |
| Adam first moment *m* (FP32) | 4 | yes | yes |
| Adam second moment *v* (FP32) | 4 | yes | yes |
| **Total** | | **16** | **14** |

Gradients are recomputed by the first backward pass after resume, so saving them buys nothing. For
W-TRAIN's 70 × 10⁹ parameters: 70e9 × 14 B = **980 GB** per checkpoint, against 1.12 TB of training state.

**Three non-tensor items and what goes wrong without them:**

1. **Step counter and learning-rate scheduler state.** Without them the schedule restarts: warm-up
   repeats from LR ≈ 0 or the cosine decay jumps back to its peak. The loss jumps and the run is not
   equivalent.
2. **Data-loader position and shuffle seed/epoch.** Without them samples are replayed (seen twice) or
   skipped (never seen). This biases training and makes runs non-reproducible.
3. **RNG states** (Python, NumPy, CUDA per rank). Dropout masks and augmentation streams change, so the
   resumed run is not bitwise reproducible. For some methods it is not even statistically equivalent.

Also accepted: the **loss-scaler state** for FP16 training (scale and growth tracker; without it,
overflow and skip behaviour changes for hundreds of steps), and the parallel layout/world size needed to
reshard.

**Common wrong answers.** Saying gradients are saved. Listing tensors (optimizer moments) as
"non-tensor" items.
