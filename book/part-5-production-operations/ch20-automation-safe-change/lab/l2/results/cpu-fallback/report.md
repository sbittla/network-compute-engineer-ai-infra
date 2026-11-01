# Lab 20 L2: a measured canary gate (no-op, injected regression, short bake) through the lab's controller

`[MEASURED]` on **CPU fallback: 13th Gen Intel(R) Core(TM) i7-13700HX**, 2026-11-01T01:09:18Z.

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

## Canary gate on measured samples

Abort condition AC1: post-change median more than **5 %** below baseline; bake needs >= 12 post samples. Node health at precheck: ok.

| Change | Baseline median (TFLOP/s (CPU)) | Post median | Drop | Baseline CV | Samples (base/post) | Gate decision |
|---|---|---|---|---|---|---|
| control | 0.091 | 0.091 | -0.2 % | 1.1 % | 12/12 | **proceed** |
| regression | 0.090 | 0.073 | +18.8 % | 1.6 % | 12/12 | **abort** |
| short_bake | 0.088 | 0.074 | +16.3 % | 4.4 % | 12/6 | **hold** |
- `regression`: AC1 gemm_tflops median 0.07 vs baseline 0.09 (-18.8% > 5%) on l2-this-host-regression
- `short_bake`: BAKE l2-this-host-short_bake has fewer than 12 post-change samples

`run_rollout` over [control, regression]: **aborted**, roll back ['l2-this-host-control', 'l2-this-host-regression'], not started [].

## Read-only LinuxHost adapter

Real state read: None (no backend NIC netdev); `compute_plan`: unreachable ['l2-this-host', 'orion-be-leaf-r0', 'orion-be-leaf-r1', 'orion-be-leaf-r2', 'orion-be-leaf-r3', 'orion-be-leaf-r4', 'orion-be-leaf-r5', 'orion-be-leaf-r6', 'orion-be-leaf-r7'], 0 actions; second plan 0 actions; dry-run writes 0.

What to conclude:

- The gate is only as good as the noise under it: the baseline varied by ~1.6 % (CV) and the no-op change moved the median -0.2 %, comfortably inside the 5 % threshold, so a real 19 % regression stands out and a healthy change is not aborted. Measure the noise before you set the threshold.
- Interleave baseline and post samples when you can; drift (thermals, a neighbour on the device) otherwise reads as a regression or hides one.
- The controller refuses to decide on thin evidence: with half the bake samples it holds, neither proceeding nor rolling back.
- This is one laptop Ada GPU with GEMM throughput standing in for per-rail busbw; the decision logic is the chapter's, the signal of a real fabric change needs the L3 two-node canary.

_CPU fallback: the samples are CPU GEMM throughput; GPU health (temperature, HW slowdown) was not checked._

## Not runnable on this host

- **LinuxHost adapter set(): ip link set dev <if> mtu 9000, then a second run planning zero actions**: needs a lab VM with an RDMA NIC or a soft-RoCE rxe device, root / CAP_NET_ADMIN, a real netdev (the harness runs with --network none).
- **L3 canary on >= 2 GPU nodes with RoCEv2 NICs: all_reduce_perf busbw per rail, CNP/PFC counters, Xid events**: needs >= 2 multi-GPU nodes with RoCEv2 NICs, a lab leaf switch with API access, nccl-tests.

- Samples: one sample = back-to-back steps for 0.5 s (768^3 FP32 GEMM on one pinned thread); baseline and post samples interleaved in ABBA order (CPU: best of 3 sub-windows per sample); 12 baseline samples per change; 5 warm-up steps of each variant first.
- Injected regression: 22 extra in-place multiply pass(es) over the GEMM output per step, sized from a timed GEMM and a timed pass to cost ~20 % of the step.
- AC1, the bake rule and the precheck rule are read from lab/data/abort_conditions.json; only the metric name changes (GEMM TFLOP/s instead of busbw).
- Node health for the precheck comes from nvidia-smi (temperature, HW slowdown) on the GPU; drained is true because nothing else is scheduled on this node by the lab.
