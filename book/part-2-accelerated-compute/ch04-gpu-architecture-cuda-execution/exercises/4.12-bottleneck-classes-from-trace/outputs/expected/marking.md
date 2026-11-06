# Marking scheme: 4.12 Identify the bottleneck class from a trace

Type outline-mandated · kind computed · tier L1 · 10 points

**Evidence required:** four findings, each with quoted evidence (row IDs, durations, bytes, metric values).

| Criterion | Points |
|---|---|
| Launch overhead: optimizer_step comb of 600 grid-4 kernels, about 2.6 µs median duration vs about 9.3 µs launch interval | 2 |
| Memory-transfer cost: 100,663,296 B pageable H2D copy (row 1) taking about 8.26 ms, about 12.2 GB/s vs about 48 GB/s pinned | 2 |
| Occupancy constraint: layernorm_bwd_fused_kernel 256 threads, 168 registers, registers limit 12 warps = 1 block = 12.5 % | 2 |
| Memory-bandwidth bottleneck: the same kernel at about 723-725 GB/s = about 21.6 % of 3.35 TB/s | 2 |
| Every finding quotes row IDs, durations, bytes or metric values and carries an evidence label | 2 |
