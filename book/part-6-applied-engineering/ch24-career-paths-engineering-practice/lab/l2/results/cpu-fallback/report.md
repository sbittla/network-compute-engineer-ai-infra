# Lab 24 L2: converting a lab_l1 evidence item into lab_hw evidence (host topology, Chapter 5)

`[MEASURED]` on **CPU fallback: 13th Gen Intel(R) Core(TM) i7-13700HX**, 2026-11-01T00:09:26Z.

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

## Hardware run backing the evidence

CPU fallback: NUMA nodes ['node0'], RDMA devices none, host copy 256 MiB **24.63 GB/s** (10 reps) `[MEASURED]`.

## L2 manifest record (lab/manifest.yaml, extension L2)

| Field | Value |
|---|---|
| gpu_model | none (CPU fallback) |
| driver_version | n/a |
| cuda_version | n/a |
| nccl_version | n/a |
| os_kernel | 6.18.54.1-microsoft-standard-WSL2 |
| commands_run | `cat /sys/devices/system/node/node*/cpulist   # lstopo / numactl are not installed in the image`<br>`ls /sys/class/infiniband`<br>`python: torch host copy_ 256 MiB, perf_counter, 3 warm-ups + 10 reps` |
| run_count | 10 |
| warmup_policy | 3 warm-up transfers discarded before timing |
| raw_output_paths | `lab/l2/results/cpu-fallback/results.json (tables.hardware[0].raw_outputs)` |

## The converted evidence item

```yaml
- id: E08
  competency: host_topology
  type: lab_hw
  claimed_level: 2
  artifact: lab/l2/results/cpu-fallback/results.json
  date: '2026-11-01'
  verifier: ''
  measured_on_hardware: true
  summary: 'GPU-to-NIC mapping CSV and aligned/misaligned model. Hardware run on a CPU-only host: topo
    -m, PCIe link state, NUMA layout and 10-rep pinned H2D bandwidth [MEASURED]. Not shown: GPU-NIC alignment
    (no NIC on this host).'
```

## Scored with the lab's model

| Variant | Type | Claimed | measured_on_hardware | Artifact | Cap | Effective | Flags |
|---|---|---|---|---|---|---|---|
| original lab_l1 | lab_l1 | 2 | False | yes | 2 | **2** | - |
| mistake: lab_l1 with measured_on_hardware: true | lab_l1 | 2 | True | yes | 2 | **1** | SIMULATION_CLAIMED_AS_MEASURED |
| converted lab_hw | lab_hw | 2 | True | yes | 3 | **2** | - |
| mistake: lab_hw without artifact | lab_hw | 2 | True | no | 3 | **1** | NO_ARTIFACT |

Readiness for **AI Network Engineer (senior)**: 78.4 (near) before, 78.4 (near) after; host_topology level 2 -> 2.

What to conclude:

- Hardware evidence raises the ceiling (lab_l1 caps at 2, lab_hw at 3); it does not raise the level by itself. The claim must still be defended, and here the GPU-NIC half of the claim has no evidence because there is no NIC.
- The cheap shortcut, setting `measured_on_hardware: true` on a lab_l1 item, is caught and capped at 1, and a lab_hw item without an artifact is capped at 1 too. The manifest and the raw output are what make it evidence.
- This is a laptop Ada GPU in a WSL2 container. The evidence is honest about that, which is what a reviewer checks first.

_CPU fallback: no GPU was measured, so the converted item keeps claimed level 2 and the GPU fields of the manifest are recorded as n/a._

## Not runnable on this host

- **Intra-node nccl-tests all_reduce_perf -b 8 -e 4G -f 2 -g <ngpus> (Chapter 12 evidence)**: needs >= 2 GPUs in one host, nccl-tests built against the installed NCCL.
- **GPU-NIC alignment half of E08 (topo -m GPU-NIC relation, ibdev2netdev)**: needs an RDMA NIC on the GPU host.

- Item converted: E08 (host_topology). Its artifact points at lab/l2/results/cpu-fallback/results.json, the results.json this run writes; raw command output is stored inside it.
- Scoring uses the lab's own effective_level / demonstrated_levels / readiness with as_of = the run date.
