# Chapter 12 hands-on: collectives you can measure, run `wsl2-rtx4060-laptop`

Numbers are `[MEASURED]` by this run (step in brackets) unless labelled `[MODELED]` (the chapter's formulas applied to measured inputs). CPU ranks use gloo over loopback TCP, one thread each; GB = 10⁹ B. Load average before/after: 3.63 4.81 4.60 2/421 75495 / 2.93 3.05 3.92 2/422 79725. Run time 492 s.

## Step 1: sweeps, 4 B to 64 MiB, and alpha-beta fits

| Op | Ranks | Floor 8n B–4 KiB (µs) | α fit (µs) | B fit (GB/s) | n½ | Plateau algbw (GB/s) | Plateau busbw (GB/s) | busbw/algbw | #wrong |
|---|---|---|---|---|---|---|---|---|---|
| all_reduce | 2 | 384.1 | 389.9 | 2.622 | 998.311 KiB | 2.348 | 2.348 | 1.000 | 0 |
| all_gather | 2 | 376.8 | 301.7 | 1.514 | 892.033 KiB | 1.959 | 0.980 | 0.500 | 0 |
| reduce_scatter | 2 | 481.8 | 469.6 | 0.919 | 843.297 KiB | 1.385 | 0.692 | 0.500 | 0 |
| broadcast | 2 | 173.5 | 186.0 | 5.329 | 967.937 KiB | 5.283 | 5.283 | 1.000 | 0 |
| all_reduce | 4 | 1576.5 | 1640.2 | 2.578 | 2.68803 MiB | 1.263 | 1.894 | 1.500 | 0 |
| all_gather | 4 | 998.0 | 964.6 | 1.469 | 1.80236 MiB | 1.368 | 1.026 | 0.750 | 0 |
| reduce_scatter | 4 | 1516.6 | 1550.5 | 0.675 | 1.33011 MiB | 0.833 | 0.625 | 0.750 | 0 |
| broadcast | 4 | 329.0 | 274.7 | 2.583 | 692.916 KiB | 2.052 | 2.052 | 1.000 | 0 |
| all_reduce | 8 | 5701.2 | 5554.4 | 1.175 | 3.55702 MiB | 0.567 | 0.992 | 1.750 | 0 |
| all_gather | 8 | 3174.7 | 3207.0 | 0.743 | 2.59843 MiB | 0.670 | 0.586 | 0.875 | 0 |
| reduce_scatter | 8 | 5200.8 | 5115.1 | 0.393 | 2.19191 MiB | 0.379 | 0.332 | 0.875 | 0 |
| broadcast | 8 | 503.7 | 444.4 | 1.590 | 689.849 KiB | 1.292 | 1.292 | 1.000 | 0 |

All `[MEASURED]` (Step 1); α, B and n½ are fits to the measured points from 8n B up, n½ = α·B/factor. Floor = median time from 8n B to 4 KiB, where every step of gloo's ring (2n chunks) carries data; below 8n B some chunks are empty and gloo skips them, so those calls are faster (see summary.json, below_region_us). Plateau = median of the four largest sizes (8–64 MiB).

**Against the chapter's formulas.**

- busbw plateau by rank count (ideal ring: independent of n) `[MEASURED]`: all_reduce n=2: 2.348, n=4: 1.894, n=8: 0.992; all_gather n=2: 0.980, n=4: 1.026, n=8: 0.586; reduce_scatter n=2: 0.692, n=4: 0.625, n=8: 0.332; broadcast n=2: 5.283, n=4: 2.052, n=8: 1.292
- algbw plateau by rank count (falls as 2(n − 1)/n grows) `[MEASURED]`: all_reduce n=2: 2.348, n=4: 1.263, n=8: 0.567
- all_reduce α against the ring's 2(n − 1) latency steps: n=2: α = 389.9 µs = 195.0 µs × 2 steps; n=4: α = 1640.2 µs = 273.4 µs × 6 steps; n=8: α = 5554.4 µs = 396.7 µs × 14 steps `[MEASURED fit]`

| Ranks | Size | all_reduce (µs) | reduce_scatter (µs) | all_gather (µs) | AR / (RS + AG) | RS / AR |
|---|---|---|---|---|---|---|
| 2 | 64 KiB | 443.0 | 496.7 | 295.3 | 0.56 | 1.12 |
| 2 | 1 MiB | 745.1 | 860.6 | 529.6 | 0.54 | 1.16 |
| 2 | 16 MiB | 7275.4 | 10264.9 | 6601.1 | 0.43 | 1.41 |
| 2 | 64 MiB | 25866.6 | 59128.0 | 48739.4 | 0.24 | 2.29 |
| 4 | 64 KiB | 2235.3 | 1977.6 | 1034.3 | 0.74 | 0.88 |
| 4 | 1 MiB | 1996.5 | 2674.0 | 1232.8 | 0.51 | 1.34 |
| 4 | 16 MiB | 13135.8 | 19347.2 | 9079.9 | 0.46 | 1.47 |
| 4 | 64 MiB | 56068.0 | 124175.4 | 69499.5 | 0.29 | 2.21 |
| 8 | 64 KiB | 5118.5 | 5028.0 | 3478.7 | 0.60 | 0.98 |
| 8 | 1 MiB | 10272.1 | 6971.3 | 4232.1 | 0.92 | 0.68 |
| 8 | 16 MiB | 29290.4 | 41297.0 | 19952.4 | 0.48 | 1.41 |
| 8 | 64 MiB | 119585.3 | 189238.5 | 108871.7 | 0.40 | 1.58 |

The identity all-reduce = reduce-scatter + all-gather predicts AR / (RS + AG) ≈ 1 and RS / AR ≈ 0.5 for a ring implementation `[MODELED]`; the measured ratios `[MEASURED]` show what gloo actually does.

- A 25 MiB DDP bucket on 4 ranks: α + factor·S/B = 16895 µs `[MODELED]` from the fit, 90 % of plateau bandwidth (n½ = 2.68803 MiB); measured 32 MiB all_reduce: 26870 µs `[MEASURED]`.

## Step 2: run-to-run spread (all_reduce, 4 ranks, separate launches)

Plateau busbw over 3 launches: 1.894, 2.373, 2.537 GB/s, CV 0.120; median per-size CV 0.147 `[MEASURED]` (Step 2).

## Step 3: ring versus tree (hand-written from send/recv)

Ping-pong between two ranks: α = 62.9 µs, B = 6.134 GB/s `[MEASURED fit]`. Ring model 2(n − 1)(α + S/(nB)), tree model 2·log₂n·(α + S/B) `[MODELED]`.

**4 ranks.** First size where the ring beats the tree: 4 MiB `[MEASURED]`; model crossover α·B·(2(n−1) − 2log₂n)/(2log₂n − 2(n−1)/n) = 301.369 KiB `[MODELED]`.

| Size | gloo all_reduce (µs) | ring (µs) | tree (µs) | ring model (µs) | tree model (µs) | Faster | Model says |
|---|---|---|---|---|---|---|---|
| 16 B | 713.9 | 2313.1 | 426.4 | 377.3 | 251.5 | tree | tree |
| 64 B | 1632.7 | 1577.6 | 427.0 | 377.3 | 251.6 | tree | tree |
| 256 B | 1535.6 | 1323.2 | 435.4 | 377.4 | 251.7 | tree | tree |
| 1 KiB | 1680.1 | 1261.8 | 417.9 | 377.5 | 252.2 | tree | tree |
| 4 KiB | 1522.1 | 1135.3 | 414.7 | 378.3 | 254.2 | tree | tree |
| 16 KiB | 1324.8 | 1195.1 | 477.9 | 381.3 | 262.2 | tree | tree |
| 64 KiB | 1541.4 | 1295.2 | 507.8 | 393.3 | 294.3 | tree | tree |
| 256 KiB | 1677.1 | 1461.9 | 646.8 | 441.4 | 422.5 | tree | tree |
| 1 MiB | 2167.7 | 1893.5 | 1227.8 | 633.7 | 935.3 | tree | ring |
| 4 MiB | 3209.7 | 3849.6 | 3907.6 | 1402.9 | 2986.4 | ring | ring |
| 16 MiB | 10807.5 | 13599.3 | 18236.3 | 4479.7 | 11191.2 | ring | ring |
| 64 MiB | 49590.3 | 52994.7 | 68617.6 | 16786.7 | 44010.1 | ring | ring |

**8 ranks.** First size where the ring beats the tree: 16 MiB `[MEASURED]`; model crossover α·B·(2(n−1) − 2log₂n)/(2log₂n − 2(n−1)/n) = 709.105 KiB `[MODELED]`.

| Size | gloo all_reduce (µs) | ring (µs) | tree (µs) | ring model (µs) | tree model (µs) | Faster | Model says |
|---|---|---|---|---|---|---|---|
| 64 B | 4690.5 | 4052.4 | 712.5 | 880.4 | 377.4 | tree | tree |
| 256 B | 4398.2 | 3877.0 | 712.2 | 880.4 | 377.5 | tree | tree |
| 1 KiB | 4210.0 | 3995.3 | 638.3 | 880.7 | 378.3 | tree | tree |
| 4 KiB | 4200.1 | 4007.8 | 648.9 | 881.5 | 381.3 | tree | tree |
| 16 KiB | 4199.3 | 4121.6 | 646.3 | 885.0 | 393.3 | tree | tree |
| 64 KiB | 4377.3 | 4309.4 | 727.3 | 899.1 | 441.4 | tree | tree |
| 256 KiB | 4493.9 | 4528.9 | 1071.5 | 955.1 | 633.7 | tree | tree |
| 1 MiB | 5504.2 | 5098.2 | 2150.5 | 1179.5 | 1402.9 | tree | ring |
| 4 MiB | 8532.3 | 8666.7 | 6908.4 | 2076.9 | 4479.7 | tree | ring |
| 16 MiB | 21994.5 | 22623.5 | 28238.5 | 5666.5 | 16786.7 | ring | ring |
| 64 MiB | 88891.8 | 95476.4 | 117167.4 | 20024.7 | 66015.1 | ring | ring |

## Step 4: NCCL on one GPU

Two ranks on one GPU: exit 1, rejected by NCCL: True (`srini:78443:78530 [0] init.cc:943 NCCL WARN Duplicate GPU detected : rank 1 and rank 0 both on CUDA device 1000`) `[MEASURED]`. NCCL version 2.21.5+cuda12.4

| Op (1 rank) | Floor ≤ 64 KiB (µs) | 64 MiB (µs) | algbw 64 MiB (GB/s) | busbw (GB/s) |
|---|---|---|---|---|
| all_reduce | 15.1 | 14.6 | 4592.7 | 0.0 |
| all_gather | 38.7 | 594.6 | 112.9 | 0.0 |
| reduce_scatter | 41.4 | 593.9 | 113.0 | 0.0 |
| broadcast | 14.3 | 13.4 | 5011.9 | 5011.9 |

`[MEASURED]` (Step 4). busbw is 0 for one-rank all-reduce, all-gather and reduce-scatter because their factors contain (n − 1). Broadcast's factor is 1, so its busbw only repeats algbw: an in-place one-rank broadcast (and all-reduce) copies nothing, which is why its 64 MiB time equals its floor. The all-gather and reduce-scatter 64 MiB times are a device-memory copy. One GPU shows the per-call floor, not a network. gloo's 2-rank all_reduce floor for comparison: 384.1 µs.

nccl-tests: nccl-tests not built: no CUDA toolkit (nvcc) on this host; see README optional step.
