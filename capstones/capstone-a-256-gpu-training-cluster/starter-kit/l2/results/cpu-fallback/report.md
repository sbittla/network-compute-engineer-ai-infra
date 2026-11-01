# Capstone A L2: host topology, GPU/NIC locality and measured GPU power

`[MEASURED]` on **CPU fallback: 13th Gen Intel(R) Core(TM) i7-13700HX**, 2026-11-01T00:10:39Z.

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

## Topology probe

```text
(nvidia-smi absent)
```

NUMA nodes: node0; CPUs: 24; RDMA devices: none; network interfaces in the container: lo. The HX8 design assumes GPU i and NIC i share a PCIe switch (PIX). There is no NIC column to check here.

## Sustained CPU load (60 s)

Median 376 GFLOP/s, min 229, max 544; window CV 16.9 %. Power was not measurable (no RAPL in the container).

## L1 rack power and 2N check (`instructor/reference/cluster_model.py`, option A_rail_1to1) `[MODELED]`

Design node: watts_max 10200 W, watts_sustained 8500 W (ratio 0.833).

| Rack | max kW | feed usable kW | 2N at max | sustained kW (design) | 2N sustained (design) |
|---|---|---|---|---|---|
| rack-01 | 40.80 | 43.70 | True | 34.00 | True |
| rack-02 | 40.80 | 43.70 | True | 34.00 | True |
| rack-03 | 40.80 | 43.70 | True | 34.00 | True |
| rack-04 | 40.80 | 43.70 | True | 34.00 | True |
| rack-05 | 40.80 | 34.42 | False | 34.00 | True |
| rack-06 | 40.80 | 43.70 | True | 34.00 | True |
| rack-07 | 40.80 | 43.70 | True | 34.00 | True |
| rack-08 | 40.80 | 43.70 | True | 34.00 | True |

## Not runnable here

- **CPU package power**. Probe: /sys/class/powercap/intel-rapl present=False. Needs: RAPL powercap exposed to the container, or a BMC/PDU reading. Fallback: sustained CPU load throughput only; L1 rack power with design values.
- **GPU<->NIC PCIe affinity (expect PIX between GPU i and NIC i)**. Probe: nvidia-smi topo -m lists 0 GPU(s) and 0 NIC(s); /sys/class/infiniband=none. Needs: HX8-class node with 8 RDMA NICs. Fallback: topology matrix recorded as found.
- **lstopo / hwloc PCIe tree**. Probe: lstopo on PATH=True. Needs: hwloc installed on the host. Fallback: NUMA nodes from /sys/devices/system/node.
- **chassis power from the BMC (ipmitool dcmi power reading / Redfish)**. Probe: ipmitool=False, /dev/ipmi*=False. Needs: BMC with DCMI or Redfish, read-only account. Fallback: none.
- **8-GPU all_reduce_perf load and 30-minute chassis power log**. Probe: GPUs=0. Needs: 8 GPUs + nccl-tests. Fallback: single-GPU GEMM load.

## What to conclude

- Size feeds on the maximum. Sustained power follows the workload and the power limit, so the sustained/max ratio is a measurement, not a constant.
- _CPU fallback: no GPU was used. GPU power, clock and topology invariants were skipped._

- Telemetry: nvidia-smi --query-gpu ... -lms 200; the first second of load is excluded (clock ramp); 'sustained' = median of the last 75 % of the load, 'max' = highest 200 ms sample.
- Load duration 60 s (quick mode 8 s). The README asks for >= 30 minutes of chassis power on an HX8 node.
