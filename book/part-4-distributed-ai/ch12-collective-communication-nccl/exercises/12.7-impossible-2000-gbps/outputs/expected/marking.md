# Marking scheme: 12.7 The 2,000 GB/s home-made benchmark

Type knowledge-check · kind written · tier L1 · 3 points

**Evidence required:** bug, fix, and why.

| Criterion | Points |
|---|---|
| Bug: timer measures asynchronous kernel launch, not execution (no synchronize/events) | 1 |
| Fix: synchronize (or CUDA events) around the timed region, warm up, time many iterations | 1 |
| Why: 2,000 GB/s exceeds the ≈ 450 GB/s NVLink per-direction rate, so it cannot be real; also check bytes vs elements | 1 |
