# 1.2 — Scale-up versus scale-out: model answer

Method: the ceiling model of manuscript Section 1.6 (Equation block 1.1). Each lower bound is work per
GPU divided by the per-GPU peak of that resource: 989 TFLOP/s BF16, 3,350 GB/s HBM, 450 GB/s NVLink per
direction, 50 GB/s per 400 Gb/s NIC (400 / 8). Inputs are `[ILLUSTRATIVE]`; results are `[MODELED]`.
`solve.py` reproduces every number.

## 1. Lower bounds

| Bound | Formula | Workload A (70B decode, TP 8) | Workload B (MoE training, 64 GPUs) |
|---|---|---|---|
| Compute | FLOP / 989 TFLOP/s | 0.56 / 989 = **0.566 ms** | 400 / 989 = **0.404 s** |
| Memory | HBM bytes / 3,350 GB/s | 20.18 / 3,350 = **6.02 ms** | 500 / 3,350 = **0.149 s** |
| Scale-up | NVLink bytes / 450 GB/s | 0.147 / 450 = **0.327 ms** | 40 / 450 = **0.089 s** |
| Scale-out | NIC bytes / 50 GB/s | 0 / 50 = **0** | 30 / 50 = **0.600 s** |
| Dominant | max of the four | Memory (HBM) | Scale-out (NIC) |
| Ceiling fraction | bound / observed | 6.02 / 9.5 = **0.63** | 0.600 / 1.5 = **0.40** |

## 2. Dominant resource and network

*A* is **memory-bound**: every decode step streams all weights plus the batch's KV cache from HBM. The
communication that matters is on the **scale-up** domain (160 TP all-reduces of ≈ 524 KB each per
step), and it costs latency (≈ 10 µs fixed cost each `[ILLUSTRATIVE]`, ≈ 1.6 ms per step) rather than
bandwidth (0.33 ms). It sits inside the 6.02 → 9.5 ms gap.

*B* is **communication-bound on scale-out**: expert-parallel all-to-all across 8 nodes puts 30 GB per GPU
through a 50 GB/s NIC, a bound 1.5× larger than compute. The ceiling fraction of 0.40 is in the
meaningful 0.3–0.9 band, so the classification is credible.

## 3. Confirming telemetry

| Workload | Metric | Expected |
|---|---|---|
| A | `DCGM_FI_PROF_DRAM_ACTIVE` | High, ≈ 0.6 or more during decode |
| A | `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE` | Low, < 0.1 |
| A | TPOT against batch × context | Rises roughly linearly with KV bytes; NIC counters ≈ 0 |
| B | Nsight Systems timeline | NCCL all-to-all (send/recv) kernels ≥ 40 % of the step |
| B | `ethtool -S` / RDMA port counters on the rail NICs | TX near line rate (tens of GB/s) during all-to-all phases |
| B | Switch ECN marks and CNPs on rail leaves | Rising during exchange phases; step time scales with tokens routed off-node |

## 4. Placement change for B

Keep each expert-parallel group inside one node (EP ≤ 8), or use hierarchical all-to-all so that
most token exchanges ride NVLink and only an aggregated remainder crosses the NIC. If all 30 GB
moved to NVLink, on top of the 40 GB already there: (40 + 30) / 450 = 0.156 s, so B would become
compute-bound at 0.404 s. **Limit on ORION:** the NVLink domain is 8 GPUs. The experts of a group
must fit in 8 × 80 GB = 640 GB of HBM alongside activations and optimizer state, and any cross-node
data-parallel gradient or expert-replica traffic stays on the NIC.

**Common wrong answers:** dividing NIC bytes by 400 (forgetting bits to bytes, which gives 0.075 s
and the wrong verdict for B); calling A communication-bound because "TP is communication"; adding
the bounds and calling the sum the prediction (the sum assumes no overlap and is an upper reference,
not the bound).
