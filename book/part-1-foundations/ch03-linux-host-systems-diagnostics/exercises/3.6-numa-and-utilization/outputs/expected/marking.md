# Marking scheme: 3.6 NUMA and utilization

Type knowledge-check · kind written · tier L1 · 4 points

**Evidence required:** A mechanism explanation, plus the exact perf stat and numastat invocations.

| Criterion | Points |
|---|---|
| Mechanism, a thread stalled on remote DRAM is still running, so stall cycles count as busy time | 2 |
| Measurement named, lower instructions per cycle than a well-placed peer | 1 |
| Exact commands (perf stat -e cycles,instructions -p <pid> -- sleep 10 and numastat -p <pid>, cross-checked with taskset -cp) | 1 |
