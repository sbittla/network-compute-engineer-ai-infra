# 14.12 recovery decision `[MODELED]`

- Failure 7 s into the ≈ 19 s persist of step 88327; no COMMIT -> invalid.
- Restore from step_088290 (committed 03:02:30).
- Damaged training: 2 h × 256 = 512 GPU-h
- Recompute 37 steps × 17.4 s = 643.8 s -> 45.8 GPU-h
- Soft restart 808.2 s -> 57.5 GPU-h
- Total ≈ 615 GPU-h
