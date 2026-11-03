# Lab 1 L2: workload characterisation of a measured kernel mix and a GPU inventory

`[MEASURED]` on **NVIDIA GeForce RTX 4060 Laptop GPU**, 2026-10-31T23:32:36Z.

| Environment | Value |
|---|---|
| device | cuda |
| cpu_model | 13th Gen Intel(R) Core(TM) i7-13700HX |
| cpu_count | 24 |
| mem_total_gib | 7.8 |
| os | Linux-6.18.54.1-microsoft-standard-WSL2-x86_64-with-glibc2.35 |
| torch | 2.5.1+cu124 |
| cuda_runtime | 12.4 |
| driver_version | 592.82 |
| pcie.link.gen.max | 4 |
| pcie.link.width.max | 8 |
| clocks.max.sm | 3105 |
| power.limit | [N/A] |

**Status:** ran
**Invariants:** all passed

## GPU inventory

| Field | Value |
|---|---|
| name | NVIDIA GeForce RTX 4060 Laptop GPU |
| capability | 8.9 |
| sm_count | 24 |
| smi_total_mib | 8188.0 |
| l2_cache_mib | 32.0 |
| driver_version | 592.82 |
| pci_bus_id | 00000000:01:00.0 |
| clocks_max_sm_mhz | 3105 |
| clocks_max_mem_mhz | 8001 |
| power_limit_w | [N/A] |
| nccl_version | 2.21.5 |
| cuda_runtime | 12.4 |
| torch | 2.5.1+cu124 |
| PCIe link (current / max) | Gen4 x8 / Gen4 x8 |

`nvidia-smi topo -m`:

```text
[4mGPU0	CPU Affinity	NUMA Affinity	GPU NUMA ID[0m
GPU0	 X 				N/A

Legend:

  X    = Self
  SYS  = Connection traversing PCIe as well as the SMP interconnect between NUMA nodes (e.g., QPI/UPI)
  NODE = Connection traversing PCIe as well as the interconnect between PCIe Host Bridges within a NUMA node
  PHB  = Connection traversing PCIe as well as a PCIe Host Bridge (typically the CPU)
  PXB  = Connection traversing multiple PCIe bridges (without traversing the PCIe Host Bridge)
  PIX  = Connection traversing at most a single PCIe bridge
  NV#  = Connection traversing a bonded set of # NVLinks
```

## Platform file for this device (the lab's schema)

| Ceiling | Value | Source |
|---|---|---|
| compute (BF16 dense ) | 38.15 TFLOP/s | 24 SMs x 512 FLOP/clk/SM x 3105 MHz (clocks.max.sm) [MODELED from VENDOR-SPEC] |
| memory | 256.0 GB/s | 128-bit bus x 2 x 8001 MHz (GDDR6, clocks.max.memory) [MODELED from VENDOR-SPEC] |
| I/O and scale-up | 15.75 GB/s | PCIe Gen4 x8 = 15.75 GB/s per direction [MODELED] |

Machine balance: **149 FLOP/B** here vs **295 FLOP/B** for the manuscript's ORION H100-class GPU (Section 1.6).

## Measured kernel mix, classified by the lab's `classify()`

| ID | Workload | Median | p95 | min-max | AI (FLOP/B) | Achieved | Lower bound | Bound (dominant) | Ceiling fraction | Flags |
|---|---|---|---|---|---|---|---|---|---|---|
| L2-TRAIN | mlp4x1024-train-step (33.6 M params, 8192 tokens/step, BF16 autocast, AdamW) | 73.400 ms | 74.607 ms | 72.511 ms-74.959 ms | 768.3 | 22.48 TFLOP/s | 43.253 ms | compute (compute) | 0.59 | none |
| L2-GEMM | gemm-4096 (4096^3, bfloat16) | 4.914 ms | 5.039 ms | 4.794 ms-5.039 ms | 1365.3 | 27.97 TFLOP/s | 3.602 ms | compute (compute) | 0.73 | none |
| L2-DECODE | decode-gemv-b8 (weights 16384x4096 (128 MiB), batch 8) | 554.4 us | 592.9 us | 546.8 us-611.3 us | 8.0 | 242.7 GB/s | 525.5 us | memory (memory) | 0.95 | none |
| L2-ELTWISE | eltwise-add (256 MiB per tensor, FP32) | 3.525 ms | 3.605 ms | 3.481 ms-3.615 ms | 0.1 | 228.4 GB/s | 3.145 ms | memory (memory) | 0.89 | none |
| L2-H2D | batch-load-h2d-pinned (256 MiB pinned host -> device) | 20.877 ms | 21.012 ms | 20.820 ms-21.059 ms | 0.0 | 12.9 GB/s over PCIe | 17.041 ms | io (io_read) | 0.82 | none |
| L2-TINY | tiny-launch-x200 (200 x 1024-element adds) | 3.205 ms | 3.811 ms | 2.982 ms-4.515 ms | 0.1 | 0.5 GB/s | 6.4 us | memory (memory) | 0.00 | LATENCY_OR_OVERHEAD |

### Telemetry during each workload (nvidia-smi, the stand-in for DCGM)

| ID | Samples | SM clock (MHz) | Power (W) | GPU util | Mem util | Max temp (C) | Clock-event masks |
|---|---|---|---|---|---|---|---|
| L2-TRAIN | 24 | 2370 | 71.5 | 99 % | 40 % | 77 | 0x0000000000000001, 0x0000000000000004 |
| L2-GEMM | 11 | 2355 | 79.9 | 97 % | 19 % | 78 | 0x0000000000000004 |
| L2-DECODE | 9 | 2520 | 74.0 | 85 % | 100 % | 77 | 0x0000000000000000 |
| L2-ELTWISE | 10 | 2520 | 64.1 | 95 % | 100 % | 71 | 0x0000000000000000 |
| L2-H2D | 14 | 2535 | 43.6 | 99 % | 6 % | 69 | 0x0000000000000000 |
| L2-TINY | 11 | 2535 | 26.3 | 13 % | 0 % | 64 | 0x0000000000000000 |

`utilization.gpu` is the fraction of time *any* kernel ran (Section 1.6): the tiny-launch burst and the GEMM can both read high while one uses a fraction of the SMs. Mask 0x4 is sw_power_cap (routine on a laptop GPU under load); 0x1 is gpu_idle.

## What to conclude

- **Decode is memory-bound here too.** The decode-gemv-b8 has an intensity of ~8.0 FLOP/B, 19x below the 149 FLOP/B balance, and runs at 243 GB/s of a 256 GB/s roof: the W02 argument of Section 1.9 holds on any GPU, because intensity ~ batch size.
- **The square GEMM and the training step are compute-bound** (ceiling fractions 0.73 and 0.59); the training step's fraction is its MFU against this device's peak, and the gap to the GEMM is optimizer, activation and launch overhead.
- **The tiny-launch burst** reaches a ceiling fraction of 0.002: no throughput ceiling explains it, which is exactly what LATENCY_OR_OVERHEAD means. Do not buy bandwidth for it; fuse or graph-capture it.
- **The batch load is I/O-bound on the PCIe link** (12.9 of 15.75 GB/s); on ORION the same role is played by the frontend NICs and the PFS.
- **This is a laptop Ada GPU, not an H100.** Its BF16 peak is ~25x lower and its DRAM ~13x lower than ORION's; the machine balance is lower too, so some kernels that are compute-bound here would be memory-bound on an H100. Re-derive the platform file for every machine; never reuse ORION's ceilings for measured rows.

## Not runnable on this host (probed, not faked)

| Part of the extension | Probe | Needs | Used instead |
|---|---|---|---|
| dcgmi dmon -e 1002,1004,1005,1011 (SM_ACTIVE, PIPE_TENSOR_ACTIVE, DRAM_ACTIVE, NVLINK_TX) | which dcgmi -> not found | DCGM with profiling-metric support (data-center GPUs) | nvidia-smi clocks/power/utilisation/clock-event reasons sampled during each workload |
| nsys profile of the training step | which nsys -> not found | Nsight Systems CLI | the step is timed with CUDA events (Chapter 4's L2 uses torch.profiler) |
| nccl-tests all_reduce_perf -g 8 (intra-node NVLink all-reduce) | torch.cuda.device_count() = 1; nvidia-smi nvlink -s: Device does not have or support Nvlink | >= 2 GPUs in one node, NVLink/NVSwitch, nccl-tests | scale-up columns are 0 in every measured row; the PCIe link is the only interconnect |
| L3: ibv_devinfo, ethtool -S, multi-node all_reduce_perf | /sys/class/infiniband absent | 2+ nodes with RoCEv2 or InfiniBand NICs | scale-out column is 0 in every measured row |

- Observed time = median of >= 5 timed repetitions after 3 warm-ups (CUDA events on the GPU, perf_counter on the CPU); p95, IQR and min/max are in the table. FLOP and byte counts are from shapes [MODELED]; the training-step bytes are a lower bound (optimizer state + saved activations), so its memory time is too.
- Rows are passed to the reference solution's normalize_and_validate() and classify() exactly as CSV strings.
