# 4.10 — Lab 4: trace analysis of a training step (reference results)

Graded with the Lab 4 rubric (lab README Section 7, 100 points); the checks listed in `meta.yaml` must PASS
in `solutions/lab/outputs/check_solution.txt`. Reference implementation: `solutions/lab/trace_analysis.py`.
Relies on manuscript Sections 4.5–4.7, 4.10, 4.11 (Table 4.4) and 4.12 (worked example, Table 4.5).

## Reference metrics `[SIMULATED]` (solution module, default parameters)

| Metric | `train_step_41` | `train_step_42` |
|---|---|---|
| Step window | 85.57 ms | 85.89 ms |
| Busy (any) / busy (kernel) | 88.8 % / 78.6 % | 89.0 % / 78.5 % |
| Copy time / overlapped with compute | 10.12 ms / 13.4 % | 10.44 ms / 13.1 % |
| `host_sync` gaps | 15 (4.91 ms) | 15 (4.77 ms) |
| `launch_bound` gaps | 600 (4.02 ms) | 600 (4.03 ms) |
| `dependency` gaps | 1 (0.31 ms) | 1 (0.31 ms) |

Copies: four large pageable H2D copies at ≈ 9–12 GB/s, two pinned at ≈ 48 GB/s. The pinned rate rules out
a degraded PCIe link (a Gen5 x16 link at reduced width or speed would slow the pinned copies too).

## Findings and savings per step (tool basis: mean of 2 steps, idle/copy time only) `[MODELED]`

| Rank | Finding | Saving (ms/step) | Evidence | Fix |
|---|---|---|---|---|
| 1 | PAGEABLE_H2D | 8.85 | 100,663,296-B and 4,194,304-B copies from pageable memory on stream 7, 9.3–12.2 GB/s, API call as long as the copy | Pinned staging pool, side-stream prefetch one step ahead |
| 2 | EXCESS_SYNC | 4.84 | 12 `debug_grad_norm_hook` ranges: 4-B pageable D2H + `cudaStreamSynchronize`, gaps of 0.27–0.55 ms | Remove the per-layer `.item()`; log a norm every N steps from a device tensor |
| 3 | LAUNCH_BOUND | 4.03 | `optimizer_step`: 600 grid-4 kernels, 2.6 µs median vs ≈ 9.3 µs launch interval; phase busy 31.9 % | `foreach`/fused AdamW or a CUDA Graph |
| 4 | LOW_OCCUPANCY (`layernorm_bwd_fused_kernel`) | 2.44 | 256 threads, 168 registers → 12.5 % (registers); 21.6 % of HBM roof | Cut registers (launch bounds) or more loads in flight |
| 5 | STREAM_DEPENDENCY | 0.31 | `cudaEventRecord` / `cudaStreamWaitEvent` / 310 µs `cudaLaunchHostFunc` on stream 13 before forward layer 6 | Move the monitoring callback off the critical path |
| | **Total** | **20.47** | | |

The worked example (Table 4.5) uses step 41 and also counts removed kernel time (hook reductions, tiny
optimizer kernels): 8.77 + 5.30 + 5.55 + 2.43 + 0.31 = 22.36 ms, projecting 85.57 − 22.36 = **63.2 ms**
(1.35×). On the tool's basis the projection is 85.57 − 20.47 ≈ **65.1 ms**. Accept 63–65 ms when the basis is
stated. Savings are upper bounds and interact (for example, removing the pageable copy also removes its two
`host_sync` gaps), so they must be validated one change at a time.

**Not problems (distractors):** the four GEMM families (18.75 % occupancy) and both flash-attention kernels
(6.25 %, 12.5 %) run at 45–62 % of the BF16 roof: low occupancy *by design*. The pinned 64 MiB side-stream
prefetch is good practice. The NVTX `log_loss` range (≈ 17.6 ms) is the CPU waiting in `loss.item()`; its
GPU idle is only ≈ 0.17 ms. The per-step `cudaDeviceSynchronize` is trailing idle (≈ 0.07 ms), excluded by
design.

## `analysis.md` marking guide (Task 7, 20 points)

Timeline annotated with the five phases and the sync gaps (5); findings ranked by saving with units and
labels (5); projected step time 63–65 ms with basis and arithmetic, noting the savings interact (4);
validation plan with repeated runs, warm-up and median/IQR (3); limitations: simulated data, theoretical
occupancy, single GPU (3).

**Common mistakes.** Double-counting overlapping intervals across streams; classifying a gap by the
previous activity instead of the next activity's submit time; computing pageable bandwidth from the API
duration; reporting occupancy without the limiter; flagging the GEMMs.
