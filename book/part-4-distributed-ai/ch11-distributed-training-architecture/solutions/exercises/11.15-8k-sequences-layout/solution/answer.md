# 11.15 — W-TRAIN at sequence 8,192 on ORION-256

**Config.** In `lab/data/model_wtrain.yaml` set `seq_len: 8192` and `global_batch_seqs: 512` (same
4,194,304 tokens per step), then evaluate layouts with the lab model. Results `[MODELED]` (b = 1,
ZeRO-1, selective recompute; memory for stage 0):

| Layout | Mem stage 0 | Bubble | Step | MFU |
|---|---|---|---|---|
| TP 8 / PP 4 / DP 8 | 38.8 GB | 4.5 % | 17.66 s | 39.4 % |
| TP 8 / PP 2 / DP 16 | 47.6 GB | 3.0 % | 17.48 s | 39.8 % |
| TP 4 / PP 8 / DP 8 | 61.7 GB | 9.9 % | 16.79 s | 41.4 % |
| TP 8 / PP 8 / DP 4 | 34.5 GB | 5.2 % | 17.77 s | 39.1 % |
| TP 2 / PP 8 / DP 16 | 116 GB | 17.9 % | — | overflow |

Why the numbers move: doubling s doubles the activation per layer (s·b·h·34/t), and halving the
global batch in sequences halves m, which roughly doubles the bubble at every PP.

**Recommendation (model answer): TP 8 / PP 2 / DP 16** — 47.6 GB leaves 20 GB below the 68 GB limit
and matches the baseline's 17.45 s within 0.2 %. TP 4/PP 8 is ≈ 4 % faster but leaves only 6 GB of
headroom. Either is acceptable if the trade-off is stated; picking TP 4/PP 8 requires an
allocator-statistics test (peak over ≥ 200 steps plus an eval and a checkpoint).

| Criterion | TP 8 / PP 2 / DP 16 (chosen) | TP 4 / PP 8 / DP 8 (alternative) |
|---|---|---|
| Memory | 47.6 GB — 20 GB headroom | 61.7 GB — 6 GB headroom; a fragmentation spike or eval buffer can OOM |
| Communication | TP 1.2 TB per GPU on NVLink (exposed ≈ 3.1 s); DP 15 GB once per step across rails | TP bytes ÷ 7/3 (exposed ≈ 1.3 s); 2× more PP messages; DP peers partly share a node |
| Step / MFU | 17.48 s / 39.8 % | 16.79 s / 41.4 % |
| Risk | Low: same TP layout as today, rail-aligned DP | Higher: bubble 9.9 %, headroom, new rank map to validate |

**Caveat.** Attention-score FLOPs grow with s and are not in 6ND; at 8k they are a larger share, so
every step time above is optimistic by a similar factor — compare layouts, not absolute values.
