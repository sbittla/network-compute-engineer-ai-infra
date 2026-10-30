# Profiler Evidence Summary

## 1. Sources

| Source | Variant(s) | Scale | Tool and version | Evidence class |
|---|---|---|---|---|
| profile_summary.csv | all | 32, 256 | nsys-style aggregation (supplied) | `[SIMULATED]` |
| nccl_debug_*.log | baseline, ib_gdr | rank 0 | `NCCL_DEBUG=INFO` | `[SIMULATED]` |
| nccl_tests.csv | baseline, ib_gdr | 8, 16 GPUs | `all_reduce_perf` | `[SIMULATED]` |
| <fill: your L2/L3 captures> | | | | `[MEASURED]` |

## 2. Step-time breakdown at 256 GPUs (ms per step)

| Category | Baseline busy | Baseline exposed | ib_gdr busy | ib_gdr exposed |
|---|---|---|---|---|
| gemm + attention + other compute | <fill> | | | |
| nccl_dp_allreduce | | | | |
| nccl_pp_sendrecv | | | | |
| memcpy_dtoh_htod | | | | |
| idle_sync_wait | | | | |
| **Exposed communication fraction** | | <fill> | | <fill> |

## 3. NCCL transport evidence

Quote the decisive lines (no more than 4 per variant) and say what each proves:

```text
<fill>
```

- Which network NCCL used: <fill>
- Whether GPUDirect RDMA was in use, and why the channel-line `/GDRDMA` suffix is the evidence to cite: <fill>
- What the `memcpy` busy time adds: <fill>

## 4. nccl-tests

| GPUs | Variant | busbw at 8 GiB (GB/s) | Reference | Reading |
|---|---|---|---|---|
| 8 | both | <fill: busbw and algbw> | plain ring busbw ≈ 360–380 GB/s (algbw ceiling ≈ 257 GB/s); ≈ 450 busbw ⇒ NVLS `[VENDOR-SPEC, 2026-10]` | <fill> |
| 16 | baseline | <fill> | ≈ 350+ GB/s expected with 8 rails | <fill> |
| 16 | ib_gdr | <fill> | | per rail = busbw ÷ 8 = <fill> vs 50 GB/s |

## 5. What the profile does not prove

<fill>
