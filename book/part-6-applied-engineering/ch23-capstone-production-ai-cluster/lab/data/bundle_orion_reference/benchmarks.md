# Benchmark evidence -- ORION-256 reference

Every row states its evidence label, tier and manifest (or model formula).

| id | metric | value | unit | label | tier | manifest |
|---|---|---|---|---|---|---|
| B-01 | W-TRAIN step time at 40 % MFU | 17.4 | s | MODELED | L1 | model: 6*N*tokens / (256*989e12*0.40) |
| B-02 | all_reduce_perf busbw, 8 GiB, 2 nodes x 8 GPUs, 8 rails (median of 5; per rail = busbw/8) | 356.1 | GB/s | MEASURED | L3 | manifests/l3-2node-2026-10-12.yaml |
| B-03 | Checkpoint write, 980 GB at 80 GB/s | 12.3 | s | MODELED | L1 | model: 980 GB / 80 GB/s |
| B-04 | DP gradient all-reduce per step (4.375 GB/GPU, ring) | 0.19 | s | MODELED | L1 | model: 2*(7/8)*4.375 GB / 40 GB/s per rail |
| B-05 | Checkpoint overhead at Young/Daly interval | 2.6 | % | MODELED | L1 | model: delta/tau + tau/(2M), delta=60 s, M=48 h |
| B-06 | Design-lint runtime on this bundle | 0.4 | s | MEASURED | L1 | manifests/l1-laptop.yaml |
