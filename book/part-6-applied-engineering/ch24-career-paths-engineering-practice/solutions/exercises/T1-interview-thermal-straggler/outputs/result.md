# T1 — magnitude check `[MODELED]`

- Compute ≈ 0.777 × 17.4 s = 13.5 s
- Slowed compute = 13.5 × 1,830 / 1,585 = 15.59 s (+2.09 s)
- Predicted step 19.49 s (+12.0 %) vs observed 19.5 s (+12.1 %)
- Upper bound: memory-bound kernels scale less than the clock ratio
- Against the 1,980 MHz boost (wrong baseline) the prediction would be 3.36 s
