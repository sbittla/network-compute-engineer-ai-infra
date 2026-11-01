# Capstone A L2: host topology, GPU/NIC locality and measured GPU power

`[MEASURED]` on **NVIDIA GeForce RTX 4060 Laptop GPU**, 2026-11-01T00:09:29Z.

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

## Topology probe

```text
GPU0	CPU Affinity	NUMA Affinity	GPU NUMA ID
GPU0	 X 				N/A
```

NUMA nodes: node0; CPUs: 24; RDMA devices: none; network interfaces in the container: lo. The HX8 design assumes GPU i and NIC i share a PCIe switch (PIX). There is no NIC column to check here.

## GPU board power: idle, then 60 s sustained FP16 GEMM

| Phase | power median (W) | power max (W) | SM clock median (MHz) | temperature max (C) | PCIe gen |
|---|---|---|---|---|---|
| idle | 15.9 | 17.4 | 2250 | 55 | 4 |
| load | 80.0 | 80.3 | 2280 | 81 | 4 |

Sustained **80.0 W**, maximum sample **80.3 W**, ratio **0.996** `[MEASURED]`. Limits reported by nvidia-smi: power.max_limit 120.00 W, power.limit [N/A], enforced.power.limit 80.0 W. Clock-event reasons during load: sw_power_cap 100 %. Throughput 27.4 TFLOP/s.
Under the board's power limit the SM clock settled at 2280 MHz, versus clocks.max.sm 3105 MHz. That is what a power cap does: a capped GPU runs slower, and in a synchronous job it becomes the straggler. This is why the exemplar keeps capped rack-05 nodes out of W-TRAIN.

## L1 rack power and 2N check (`instructor/reference/cluster_model.py`, option A_rail_1to1) `[MODELED]`

Design node: watts_max 10200 W, watts_sustained 8500 W (ratio 0.833).
Sensitivity: watts_sustained rescaled to watts_max x measured ratio = **10157 W**.

| Rack | max kW | feed usable kW | 2N at max | sustained kW (design) | 2N sustained (design) | sustained kW (rescaled) | 2N sustained (rescaled) |
|---|---|---|---|---|---|---|---|
| rack-01 | 40.80 | 43.70 | True | 34.00 | True | 40.63 | True |
| rack-02 | 40.80 | 43.70 | True | 34.00 | True | 40.63 | True |
| rack-03 | 40.80 | 43.70 | True | 34.00 | True | 40.63 | True |
| rack-04 | 40.80 | 43.70 | True | 34.00 | True | 40.63 | True |
| rack-05 | 40.80 | 34.42 | False | 34.00 | True | 40.63 | False |
| rack-06 | 40.80 | 43.70 | True | 34.00 | True | 40.63 | True |
| rack-07 | 40.80 | 43.70 | True | 34.00 | True | 40.63 | True |
| rack-08 | 40.80 | 43.70 | True | 34.00 | True | 40.63 | True |

_The ratio comes from one laptop GPU under a synthetic GEMM load, not from an HX8 chassis running W-TRAIN. It shows how the 2N verdict depends on the sustained/max assumption. Replace it with the chassis measurement._

## Not runnable here

- **GPU<->NIC PCIe affinity (expect PIX between GPU i and NIC i)**. Probe: nvidia-smi topo -m lists 1 GPU(s) and 0 NIC(s); /sys/class/infiniband=none. Needs: HX8-class node with 8 RDMA NICs. Fallback: topology matrix recorded as found.
- **lstopo / hwloc PCIe tree**. Probe: lstopo on PATH=True. Needs: hwloc installed on the host. Fallback: NUMA nodes from /sys/devices/system/node.
- **chassis power from the BMC (ipmitool dcmi power reading / Redfish)**. Probe: ipmitool=False, /dev/ipmi*=False. Needs: BMC with DCMI or Redfish, read-only account. Fallback: GPU board power from nvidia-smi (GPU only, not the chassis).
- **8-GPU all_reduce_perf load and 30-minute chassis power log**. Probe: GPUs=1. Needs: 8 GPUs + nccl-tests. Fallback: single-GPU GEMM load.

## What to conclude

- Size feeds on the maximum. Sustained power follows the workload and the power limit, so the sustained/max ratio is a measurement, not a constant.
- Under a compute-saturating load this GPU sits on its enforced limit (sustained/max = 1.00, SW power cap active). A power-limited node's sustained draw is its limit. The design's 0.83 assumes a workload that does *not* saturate the GPUs, so measure W-TRAIN itself on the chassis before relaxing the 2N sizing.
- 'Idle' here is the GPU with no load from this experiment. Other tenants or the display can keep the clocks up, so check the idle row before using it as a baseline.
- This is a **laptop Ada GPU (about 80 W enforced), not an H100 SXM (about 700 W)**: only the method transfers, the watts do not.

- Telemetry: nvidia-smi --query-gpu ... -lms 200; the first second of load is excluded (clock ramp); 'sustained' = median of the last 75 % of the load, 'max' = highest 200 ms sample.
- Load duration 60 s (quick mode 8 s). The README asks for >= 30 minutes of chassis power on an HX8 node.
