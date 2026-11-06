# 3.6 — Why NUMA-remote placement rarely looks like low CPU utilization

Source: manuscript Section 3.4 ("First touch and NUMA placement") and Section 3.9.

**Mechanism.** CPU utilization counts the time a thread is scheduled on a CPU, not how much useful work it
does there. A thread whose loads miss in cache and must fetch from the *remote* socket's DRAM (≈ 2× the
local latency; the `numactl -H` distance is 21 against 10) stalls in the pipeline, but it is still
*running*. Stall cycles are busy cycles to the scheduler. Remote placement therefore lowers
**instructions per cycle (IPC)** and throughput while utilization stays the same or even rises (the work
takes longer). It also adds traffic on the inter-socket link.

**Measurement that reveals it.** Compare IPC against a well-placed peer process doing the same work:

```bash
perf stat -e cycles,instructions -p <pid> -- sleep 10      # IPC = instructions / cycles
numastat -p <pid>                                          # per-node memory of the process (MB)
taskset -cp <pid>                                          # which CPUs (and so which node) it runs on
```

Remote placement shows as a low IPC together with most of the process's memory on a node outside its CPU
affinity. On `orion-n12` that is 210,855.6 of 213,171.2 MB on node 1 (98.9 %) while the PID is bound to
node-0 CPUs. `/proc/<pid>/numa_maps` gives per-mapping detail, and uncore or offcore counters (remote
DRAM accesses) give the hardware view where `perf` exposes them.
