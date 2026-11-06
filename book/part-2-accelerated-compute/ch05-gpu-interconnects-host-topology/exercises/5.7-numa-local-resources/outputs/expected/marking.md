# Marking scheme: 5.7 What must be NUMA-local

Type knowledge-check · kind written · tier L1 · 3 points

**Evidence required:** three items with commands.

| Criterion | Points |
|---|---|
| Host memory for staging/pinned buffers, with numactl --hardware or numastat -p <pid> | 1 |
| CPU threads of the rank, NCCL proxy and loaders, with taskset -cp <pid> or topo -m CPU Affinity | 1 |
| NIC interrupts, with /proc/interrupts and /proc/irq/<n>/smp_affinity_list | 1 |
