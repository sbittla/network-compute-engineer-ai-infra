# Marking scheme: 3.12 Host inventory and diagnostic snapshot

Type outline-mandated · kind computed · tier L1 · 10 points

**Evidence required:** The inventory table with provenance per value; for L2, both raw JSON snapshots and the gap comparison.

| Criterion | Points |
|---|---|
| CPU model and topology (Xeon Platinum 8480+, 2 x 56 x 2 = 224) and NUMA nodes with CPU lists and memory (1,031,868 and 1,032,151 MB), with provenance | 2 |
| Memory total (free -m 2,064,019 MiB) and the 8 GPUs with BDF, NUMA node and Gen5 x16 link state | 2 |
| NICs (8 rail at 32 GT/s x16, 2 frontend at 16 GT/s x16) and 8 NVMe drives at 16 GT/s x4 | 2 |
| Interfaces rail0-7 and fe0-1 with MTU 9000 and 400,000/200,000 Mb/s | 2 |
| Kernel 5.15.0-122-generic, GPU driver 550.127.05, mlx5 firmware 28.39.1002 and cpufreq intel_pstate/performance, with sections cited | 2 |
