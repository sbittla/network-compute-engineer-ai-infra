# Capstone H L2: roofline calibration of prefill and decode on one GPU

`[MEASURED]` on **CPU fallback: 13th Gen Intel(R) Core(TM) i7-13700HX**, 2026-11-01T01:13:31Z.

| Environment | Value |
|---|---|
| device | cpu |
| cpu_model | 13th Gen Intel(R) Core(TM) i7-13700HX |
| cpu_count | 24 |
| mem_total_gib | 7.8 |
| os | Linux-6.18.54.1-microsoft-standard-WSL2-x86_64-with-glibc2.35 |
| torch | 2.5.1+cu124 |
| cuda_runtime | 12.4 |

**Status:** ran
**Invariants:** all passed

## Model under test

Random-weight decoder: d=512, layers=4, heads=8, torch.float32, 13 M non-embedding parameters, 59 MB of weights, 16 KiB of KV per token.

Measured ceilings: dense GEMM **0.29 TFLOP/s** (n=1024), memory copy **65.3 GB/s** (read + write) `[MEASURED]`.

## Prefill (output length 1)

| Prompt tokens | Median (ms) | p95 (ms) | IQR (ms) | TFLOP/s | tokens/s | L1 model (ms) | error |
|---|---|---|---|---|---|---|---|
| 32 | 7.01 | 11.53 | 3.439 | 0.12 | 4563 | 3.54 | -49 % |
| 64 | 10.08 | 12.69 | 2.515 | 0.16 | 6347 | 7.12 | -29 % |
| 128 | 17.45 | 24.53 | 4.565 | 0.19 | 7336 | 14.39 | -18 % |
| 256 | 29.20 | 40.32 | 11.388 | 0.23 | 8766 | 29.37 | +1 % |
| 512 | 59.43 | 70.16 | 8.099 | 0.23 | 8616 | 61.10 | +3 % |
| 1024 | 132.41 | 181.96 | 21.196 | 0.23 | 7734 | 131.60 | -1 % |

## Decode step at context 256

| Batch | Median (ms) | p95 (ms) | GB/s moved | tokens/s | L1 model (ms) | error |
|---|---|---|---|---|---|---|
| 1 | 3.183 | 4.224 | 19.8 | 314 | 3.633 | +14 % |
| 2 | 4.049 | 5.998 | 16.6 | 494 | 3.869 | -4 % |
| 4 | 4.623 | 7.130 | 16.3 | 865 | 4.342 | -6 % |
| 8 | 5.338 | 7.257 | 17.3 | 1499 | 5.288 | -1 % |
| 16 | 7.145 | 9.488 | 17.6 | 2239 | 7.179 | +0 % |
| 32 | 10.933 | 13.545 | 17.7 | 2927 | 10.961 | +0 % |

## Fitted L1 constants

| Constant | L1 default (H100-class TP8) | Fitted vs measured ceiling |
|---|---|---|
| mfu_prefill | 0.5 | 0.78 |
| hbm_eff | 0.7 | 0.27 |
| step_overhead_s | 0.004 s | 0.10 ms |

## What-if: L1 pool sizing with the measured efficiencies `[MODELED]`

Using `instructor/reference/serve.py` `size_pools()` for the H100-class instance, swapping mfu_prefill 0.5 -> 0.78 and hbm_eff 0.7 -> 0.27:

| | P (prefill) | D (decode) | decode batch | GPUs |
|---|---|---|---|---|
| L1 defaults | 4 | 1 | 491 | 40 |
| measured efficiencies | 3 | 4 | 146 | 56 |

_This transfers efficiencies measured on a small model on a laptop GPU onto a 70B TP8 H100-class instance. Constants are relative to the vendor peak, as the L1 hardware table is. It shows how sensitive the pool sizes are to these constants; it is not a prediction for ORION._

The L1 formulas in `instructor/reference/serve.py` (`prefill_time_s`, `decode_step_time_s`, MODEL re-pointed at this model) reproduce the 'L1 model' columns to 2e-16 relative difference.

## KV transfer path available on one host

| Prompt tokens | KV bytes | Median (ms) | GB/s | path |
|---|---|---|---|---|
| 512 | 8.4 MB | 0.065 | 128.6 | host memcpy |
| 1024 | 16.8 MB | 0.098 | 171.4 | host memcpy |

## Not runnable here

- **L3 KV-cache transfer between two RDMA nodes (ib_write_bw --use_cuda, GPUDirect RDMA, TCP baseline)**. Probe: /sys/class/infiniband devices=none, /dev/infiniband=False, ib_write_bw=absent, torch.cuda.device_count()=0. Needs: two GPU nodes, RDMA NIC per rail (GPUDirect RDMA capable), lab switch, perftest built with CUDA. Fallback: host-memory KV copy measured instead (table kv_offload).

## What to conclude

- _CPU fallback: no GPU was used. mfu_prefill and hbm_eff are relative to a GEMM and a copy measured on this CPU, and the GPU-only invariants (vendor peak, memory peak, PCIe ceiling, flat memory-bound decode, decode-model agreement) were skipped._
- This CPU's ridge point is ~4 FLOP/byte (a GPU's is in the hundreds), so decode becomes compute-bound at small batches here and the memory-only L1 decode formula fits poorly: exactly why the L1 model is a GPU model.
- The prefill/decode asymmetry still shows: prefill throughput grows with prompt length, decode tokens/s grows with batch.

- Model: random weights, greedy argmax; output quality is irrelevant, only the cost of the work.
- Prefill FLOPs = 2*N*T + 2*L*d*T^2 and decode bytes = weights + B*ctx*KV bytes/token, the L1 formulas; l1_formula_crosscheck evaluates serve.prefill_time_s / decode_step_time_s themselves with MODEL re-pointed at this model.
- Repetitions: 3 warm-ups, >= 5 timed, interleaved round-robin across sizes; CUDA events on the GPU, perf_counter on the CPU; medians reported.
