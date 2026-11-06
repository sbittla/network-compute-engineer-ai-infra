# 5.7 — What must be NUMA-local to a GPU and its NIC (model answer)

Relies on manuscript Section 5.5 (NUMA, CPU affinity and interrupts) and Chapter 3.

| Resource | Why it must be local | Command that reveals it |
|---|---|---|
| **Host memory** for pinned/staging buffers (input batches, host-staged NCCL buffers) | DMA from the GPU or NIC to remote memory crosses the inter-socket link, adding latency and competing with other traffic | `numactl --hardware` (nodes, sizes, distances); `numastat -p <pid>` (where a process's pages actually live) |
| **CPU threads**: the rank's main thread, the NCCL proxy thread, data-loader workers | The proxy drives the NIC and touches its queues; a remote core adds cross-socket hops to every operation | `taskset -cp <pid>` (current affinity); the `CPU Affinity` / `NUMA Affinity` columns of `nvidia-smi topo -m` (on `orion-n01`: GPU0–3 → cores 0–55,112–167, NUMA 0) |
| **NIC interrupts** (completion vectors) | IRQs handled on a remote socket add latency and cache misses to every completion | `/proc/interrupts` (which CPUs take the `mlx5_*` vectors); `/proc/irq/<n>/smp_affinity_list` |

Also acceptable as a command: `lstopo` / `hwloc-ls` (which package each PCI device hangs under), and
`/sys/bus/pci/devices/<BDF>/numa_node`.

**Common wrong answers.** Naming the GPU's HBM (it is not host NUMA memory); giving a command that shows
configuration intent (a launcher flag) instead of observed state.
