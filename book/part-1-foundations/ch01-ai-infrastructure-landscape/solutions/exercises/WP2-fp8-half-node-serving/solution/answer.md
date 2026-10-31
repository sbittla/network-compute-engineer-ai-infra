# WP2 — FP8 serving on half a node (TP = 4, two replicas per HX8)

Method: manuscript Section 1.9 Step 5 (W-INFER decode) and Section 1.6 (arithmetic intensity). W-INFER
from `docs/REFERENCE_CLUSTER.md`: FP8 weights ≈ 70 GB; KV cache 327,680 B per token in BF16; 8 KV heads.
All results `[MODELED]`; the 0.63 ceiling fraction is carried over from the BF16 case
`[ILLUSTRATIVE]`. `solve.py` reproduces every number.

**(a) Bytes read per GPU per decode step (batch 32, mean context 2,048).**

```text
weights per GPU = 70 GB / 4                          = 17.5 GB
KV per replica  = 32 × 2,048 × 327,680 B             = 21.47 GB
KV per GPU      = 21.47 GB / 4  (2 of 8 KV heads/GPU) = 5.37 GB
total per GPU   = 17.5 + 5.37                        = 22.87 GB
```

The KV cache is still BF16, so its bytes per GPU *double* compared with TP 8 (2.68 → 5.37 GB): each GPU
now holds two KV heads instead of one.

**(b) Lower bounds.**

```text
T_memory  = 22.87 GB / 3,350 GB/s                     = 6.83 ms
FLOP/GPU  = 2 × 70e9 × 32 / 4                         = 1.12 × 10^12 FLOP
T_compute = 1.12 TFLOP / 1,979 TFLOP/s (FP8 dense)    = 0.566 ms
```

**(c) Throughput at ceiling fraction 0.63.**

```text
step       = 6.83 ms / 0.63            = 10.84 ms
per replica = 32 tokens / 10.84 ms     = 2,952 tokens/s
per node    = 2 replicas × 2,952       ≈ 5,900 tokens/s   (≈ 1.75 × the BF16 TP 8 figure of ≈ 3,370)
```

| Per GPU, decode step | BF16, TP 8 | FP8, TP 4 |
|---|---|---|
| HBM bytes read | 20.18 GB | 22.87 GB |
| T_memory | 6.02 ms | 6.83 ms |
| TPOT at fraction 0.63 | ≈ 9.5 ms | ≈ 10.8 ms |
| Replicas per node | 1 | 2 |
| Output tokens/s per node | ≈ 3,370 | ≈ 5,900 |

Each replica is slightly slower (more bytes per GPU), but the node serves two of them, so throughput per
node rises ≈ 75 % and TPOT stays far inside the 50 ms p95 SLO.

**(d) Intensity versus machine balance.** Counting weights only: 2 FLOP per parameter per sequence × 32
sequences per 1 byte per FP8 parameter = **64 FLOP/B**. FP8 machine balance = 1,979 TFLOP/s ÷ 3.35 TB/s ≈
**591 FLOP/B**. Decode is still ≈ 9× below balance, so it is memory-bound; FP8 helps by halving the
weight bytes, not by its higher FLOP rate.

**What must be measured to trust (c):** the TPOT distribution (p50/p95) at FP8 TP 4 under the target
load. FP8 kernel efficiency and the different all-reduce latency at p = 4 change the ceiling fraction,
and model quality at FP8 must be validated before any capacity decision.

**Common wrong answers:** halving the KV bytes too (the cache is still BF16); forgetting the second replica
per node; using the BF16 peak (989 TFLOP/s) for FP8 compute; computing KV per GPU by dividing by 8.
