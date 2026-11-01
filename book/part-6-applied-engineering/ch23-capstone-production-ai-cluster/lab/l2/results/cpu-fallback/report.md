# Lab 23 L2: node-level bundle assumptions validated on this host, new evidence linted

`[MEASURED]` on **CPU fallback: 13th Gen Intel(R) Core(TM) i7-13700HX**, 2026-11-01T00:09:05Z.

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

## Assumption register against this node

| ID | Assumption | Bundle | This node | Verdict |
|---|---|---|---|---|
| A-01 | Dense BF16 tensor peak per GPU | 989 TFLOP/s [VENDOR-SPEC, 2026-10] | 0.436 TFLOP/s FP32 on the CPU (no GPU) | node class differs: validate the ratio achieved/peak, not the number |
| A-04 | Model FLOPs utilisation (MFU) for W-TRAIN | 0.4 [ILLUSTRATIVE] | not measurable without a GPU | MFU 0.40 must sit below the measured GEMM ceiling; measure end-to-end on the 64-GPU slice (L3) |
| A-02 | HBM capacity per GPU | 80 GB | no GPU; host memory 7.75 GiB | FAILS acceptance on this node: not the bundle's GPU (exactly what the check is for) |
| A-03 | Node maximum power | 10.2 kW | not measurable (no GPU, no BMC, no RAPL) | NOT VALIDATED: needs a BMC/PDU reading over >= 10 min of burn-in |
| A-08 | Blocking checkpoint time (synchronous save to the PFS, conservative) | 60 s | 256 MiB state: write 0.69 GB/s, read 2.03 GB/s to local disk, verified=True | local write below the per-node PFS share (2.5 GB/s = 80 GB/s / 32 nodes); A-08 itself needs the 32-node sync save (L3) |
| A-10 | RoCE path MTU | 4096 B | RDMA devices: none; ibv_devinfo absent | NOT VALIDATED: no RDMA NIC |
| affinity | GPU-NIC PCIe affinity and NUMA layout | PIX per rail; 2 NUMA nodes (HX8) | topo -m lists a NIC: False; NUMA nodes: ['node0'] | NOT VALIDATED: no NIC; single NUMA node |

## Dense GEMM sweep (A-01)

| dtype | n | TFLOP/s (median) | TFLOP/s at p95 time | reps |
|---|---|---|---|---|
| float32 | 1024 | 0.31 | 0.24 | 10 |
| float32 | 2048 | 0.44 | 0.38 | 10 |
| float32 | 3072 | 0.42 | 0.38 | 10 |

## Checkpoint write and restore (A-08 / B-03 at node scale)

256 MiB per checkpoint, 5 repetitions: write median **0.69 GB/s** (worst 0.52), read-back median 2.03 GB/s; bit-exact restore: **True**.

## New evidence rows, linted with the lab's `check_evidence`

| id | metric | value | unit | label | tier | manifest |
|---|---|---|---|---|---|---|
| B-07 | Dense FP32 CPU GEMM, best of 3 sizes (median of reps) | 0.44 | TFLOP/s | MEASURED | L2 | lab/l2/results/cpu-fallback/environment.json |
| B-08 | Checkpoint write, 256 MiB, D2H + torch.save + fsync, local disk | 0.69 | GB/s | MEASURED | L2 | lab/l2/results/cpu-fallback/environment.json |

New findings on these rows: **0**. Negative controls (same metric at tier L1; MEASURED with no manifest) raised: **EVID-003, EVID-004**.

What to conclude:

- An acceptance run is a set of yes/no answers against the bundle, each with evidence. On this host A-02 fails outright (wrong GPU), A-03 and A-10 cannot be answered (no BMC, no NIC), and A-01/A-04 transfer only as a ratio.
- Keep the vendor maximum for rack budgeting and record the measured value next to it; do not overwrite one with the other.
- A MEASURED row is only evidence with its manifest and the right tier; the linter enforces that, and the negative controls show it would have caught the two common mistakes.
- Never trust a checkpoint you have not restored: the round trip here is verified bit for bit.

_CPU fallback: no GPU, so A-01 is a CPU FP32 GEMM, A-02 is host memory and no power was measured; the GPU-only invariants were skipped._

## Not runnable on this host

- **A-03 node power: sudo ipmitool dcmi power reading during >= 10 min of burn-in**: needs a BMC with DCMI/Redfish read access, an HX8-class server.
- **A-10 RoCE MTU and NIC firmware: ibv_devinfo active_mtu, fw_ver; GPU-NIC affinity in topo -m**: needs RDMA NICs on the GPU host, rdma-core.
- **L3 B-02 row: 2-node all_reduce_perf busbw with /GDRDMA evidence**: needs 2+ multi-GPU nodes with RDMA NICs, nccl-tests built with MPI.

- GEMM: 3 warm-ups, >= 5 timed repetitions per size (CUDA events on the GPU). Checkpoint: 1 warm-up round trip, then >= 5; the last round trip is verified with SHA-256 over every tensor's bytes.
- Checkpoint files go to /tmp inside the container (the image's overlay filesystem on the host's disk).
- The benchmarks.md rows point at lab/l2/results/cpu-fallback/environment.json, the environment manifest this run writes.
